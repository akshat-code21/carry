"""Normalizer node: HTML → clean plain text."""

import re
import unicodedata

import structlog
from langchain_core.documents import Document

from src.pipeline.hfi.state import PipelineState

logger = structlog.get_logger()

_PAGE_NUM = re.compile(r"^\s*[Pp]age\s+\d+\s*$", re.MULTILINE)
_EDGAR_HEADER = re.compile(
    r"(UNITED STATES SECURITIES.*?FORM 13F[-\w]*\s+)", re.DOTALL | re.IGNORECASE
)
_TIMESTAMP = re.compile(r"\[?\d{1,2}:\d{2}(:\d{2})?\]?\s*")
_MULTI_NEWLINE = re.compile(r"\n{3,}")


def normalizer_node(state: PipelineState) -> PipelineState:
    raw = state.get("raw_text", "") or ""
    content_type = state.get("content_type", "")

    if not raw:
        return {**state, "cleaned_text": "", "error": "Empty raw_text"}

    if content_type in ("article", "newsletter", "website_page") and _looks_like_html(raw):
        try:
            from langchain_community.document_transformers import Html2TextTransformer
            doc = Document(page_content=raw, metadata={})
            transformed = Html2TextTransformer().transform_documents([doc])
            text = transformed[0].page_content if transformed else raw
        except Exception as e:
            logger.warning("Html2TextTransformer failed, falling back to raw", error=str(e))
            text = raw
    else:
        text = raw

    if content_type == "filing":
        text = _EDGAR_HEADER.sub("", text)

    if content_type == "video":
        text = _TIMESTAMP.sub(" ", text)

    text = _PAGE_NUM.sub("", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    text = unicodedata.normalize("NFKD", text)
    text = text.strip()

    return {**state, "cleaned_text": text, "error": None}


def _looks_like_html(text: str) -> bool:
    return bool(re.search(r"<(html|head|body|div|p|span|article)\b", text[:2000], re.IGNORECASE))
