"""Report generator node — produces structured markdown using LLM."""

import json
import uuid
from datetime import UTC, datetime, timedelta

import structlog
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings
from src.pipeline.hfi.prompts.report_generation import INVESTOR_REPORT_PROMPT
from src.pipeline.hfi.state import PipelineState

logger = structlog.get_logger()

REPORT_TRIGGER_TYPES = {"filing", "article", "newsletter", "video"}


def clean_markdown_fences(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```markdown"):
        cleaned = cleaned[11:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    return cleaned.strip()


def generate_report_from_context(
    *,
    investor_id: str,
    user_id: str,
    investor_name: str,
    entities: list[dict],
    theses: list[dict],
    source_urls: list[str],
    content_item_ids: list[str],
    period_days: int = 30,
    filing_period: str = "N/A",
    portfolio_changes_json: str = "None",
) -> str:
    """Generate an investor report from pre-aggregated context. Persists to DB."""
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    now = datetime.now(UTC)
    period_start = (now - timedelta(days=period_days)).strftime("%Y-%m-%d")
    period_end = now.strftime("%Y-%m-%d")

    source_links = "\n".join(f"- [{url}]({url})" for url in source_urls if url) or "- None"

    prompt = INVESTOR_REPORT_PROMPT.format(
        investor_name=investor_name,
        period_start=period_start,
        period_end=period_end,
        source_count=len(set(source_urls)),
        content_count=len(content_item_ids),
        entities_json=json.dumps(entities, indent=2)[:8000],
        theses_json=json.dumps(theses, indent=2)[:8000],
        portfolio_changes_json=portfolio_changes_json,
        previous_summary="No previous report.",
        generated_at=now.isoformat(),
        filing_period=filing_period,
        source_links=source_links,
    )

    markdown = _call_llm(client, prompt)
    markdown = clean_markdown_fences(markdown)

    # Persist report to DB
    _save_report_sync(
        investor_id=investor_id,
        user_id=user_id,
        markdown=markdown,
        period_start=period_start,
        period_end=period_end,
        content_item_ids=content_item_ids,
    )

    return markdown


def report_generator_node(state: PipelineState) -> PipelineState:
    if not state.get("report_triggered"):
        return {**state, "report_generated": False}
    if state.get("content_type") not in REPORT_TRIGGER_TYPES:
        return {**state, "report_generated": False}

    try:
        portfolio_changes_json = "None"
        if state.get("portfolio_changes"):
            portfolio_changes_json = json.dumps(state.get("portfolio_changes"), indent=2)[:8000]
        generate_report_from_context(
            investor_id=state["investor_id"],
            user_id=state["user_id"],
            investor_name=state.get("investor_name", state["investor_id"]),
            entities=state.get("entities", []),
            theses=state.get("theses", []),
            source_urls=[state.get("source_url", "")],
            content_item_ids=[state["content_item_id"]],
            filing_period=state.get("filing_period", "N/A"),
            portfolio_changes_json=portfolio_changes_json,
        )
    except Exception as e:
        logger.error("Report generation failed", error=str(e))
        return {**state, "report_generated": False, "error": str(e)}

    return {**state, "report_generated": True}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=10, max=60))
def _call_llm(client: OpenAI, prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-5.4-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_completion_tokens=4000,
        timeout=90,
    )
    return response.choices[0].message.content or ""


def _save_report_sync(
    investor_id: str,
    user_id: str,
    markdown: str,
    period_start: str,
    period_end: str,
    content_item_ids: list[str],
) -> None:
    """Fire-and-forget DB save via asyncio."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(
            _save_report_async(
                investor_id, user_id, markdown, period_start, period_end, content_item_ids
            )
        )
    except RuntimeError:
        pass


async def _save_report_async(
    investor_id: str,
    user_id: str,
    markdown: str,
    period_start: str,
    period_end: str,
    content_item_ids: list[str],
) -> None:
    from src.database import async_session_factory
    from src.models.hfi_report import HfiReport

    title_line = next(
        (line for line in markdown.splitlines() if line.startswith("# ")), "Intelligence Report"
    )
    title = title_line.lstrip("# ").strip()

    summary_lines = []
    for line in markdown.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        if any(
            line.startswith(p)
            for p in ("**Generated:**", "**Period:**", "**Sources analyzed:**", "```")
        ):
            continue
        summary_lines.append(line)

    summary = " ".join(summary_lines[:3])[:300] if summary_lines else ""

    async with async_session_factory() as db:
        report = HfiReport(
            user_id=uuid.UUID(user_id),
            investor_id=uuid.UUID(investor_id),
            report_type="investor_report",
            title=title,
            summary=summary,
            content_markdown=markdown,
            source_item_ids=[uuid.UUID(cid) for cid in content_item_ids],
            period_start=datetime.fromisoformat(period_start),
            period_end=datetime.fromisoformat(period_end),
        )
        db.add(report)
        await db.commit()
        logger.info("Report saved", investor_id=investor_id, content_items=len(content_item_ids))
