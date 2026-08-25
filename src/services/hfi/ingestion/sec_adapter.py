"""
SEC EDGAR 13F adapter.
Custom implementation — uses EDGAR REST API directly (free, no key needed).
Rate limit: 10 req/s. Always send User-Agent header.
"""

import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import httpx
import structlog
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from tenacity import retry, stop_after_attempt, wait_exponential

from src.services.hfi.ingestion.base_adapter import BaseAdapter

logger = structlog.get_logger()

EDGAR_HEADERS = {
    "User-Agent": "HedgeFundIntelligence/1.0 (contact@hedgefundintelligence.com)",
    "Accept-Encoding": "gzip, deflate",
}
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/"

# Both possible 13F XML filenames
INFOTABLE_FILENAMES = ["infotable.xml", "informationtable.xml"]

# XML namespaces used across different 13F versions
NS_PATTERNS = [
    "{http://www.sec.gov/edgar/document/thirteenf/informationtable}",
    "{http://www.sec.gov/edgar/thirteenf/informationtable}",
    "{http://www.sec.gov/edgar/thirteenf}",
    "",  # no namespace fallback
]


class SECEdgarAdapter(BaseAdapter):
    async def fetch(self, source) -> list[Document]:
        cik = source.config.get("cik_number") or ""
        if not cik:
            logger.warning("SEC adapter: no cik_number in source config", source_id=str(source.id))
            return []

        cik_padded = cik.zfill(10)
        last_accession = source.config.get("last_accession", "")
        max_filings = source.config.get("max_filings", 10)

        try:
            filings = await self._get_all_13f_filings(cik_padded, max_filings=max_filings)
        except Exception as e:
            logger.error("EDGAR submissions fetch failed", cik=cik_padded, error=str(e))
            raise

        docs = []
        for filing in filings:
            accession = filing["accessionNumber"]
            if accession == last_accession:
                break

            filing_period = filing.get("reportDate", "")
            period_label = _period_label(filing_period)

            try:
                holdings = await self._parse_13f(
                    cik_padded,
                    accession,
                    primary_doc=filing.get("primaryDocument", ""),
                )
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.warning("13F parse failed", accession=accession, error=str(e))
                continue

            raw_xml_summary = _holdings_to_text(holdings, filing_period)
            doc = Document(
                page_content=raw_xml_summary,
                metadata={
                    "source": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type=13F-HR",
                    "content_type": "filing",
                    "investor_id": str(source.investor_id),
                    "source_id": str(source.id),
                    "accession_number": accession,
                    "filing_period": period_label,
                    "report_date": filing_period,
                    "published_at": filing.get("filingDate", ""),
                    "title": f"13F Filing — {period_label}",
                    "holdings": holdings,
                },
            )
            docs.append(doc)

        return docs

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=5, max=30))
    async def _get_all_13f_filings(self, cik_padded: str, max_filings: int = 10) -> list[dict]:
        """Fetch latest 13F-HR / 13F-HR/A filings for a CIK (up to max_filings)."""
        data = await self._get_submissions_json(cik_padded)
        filings = self._extract_13f_filings(data)

        if max_filings is None or len(filings) < max_filings:
            older_files = data.get("filings", {}).get("files", [])
            for file_entry in older_files:
                name = file_entry.get("name", "")
                if not name:
                    continue
                try:
                    older = await self._get_older_submissions_json(name)
                    filings.extend(self._extract_13f_filings(older))
                    if max_filings is not None and len(filings) >= max_filings:
                        break
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.warning("EDGAR older submissions fetch failed", file=name, error=str(e))
                    continue

        seen: set[str] = set()
        unique: list[dict] = []
        for f in sorted(filings, key=lambda x: x.get("filingDate", ""), reverse=True):
            acc = f.get("accessionNumber", "")
            if acc in seen:
                continue
            seen.add(acc)
            unique.append(f)
            if max_filings is not None and len(unique) >= max_filings:
                break
        logger.info("EDGAR 13F filings enumerated", cik=cik_padded, total=len(unique))
        return unique

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=5, max=30))
    async def _get_submissions_json(self, cik_padded: str) -> dict:
        url = SUBMISSIONS_URL.format(cik=cik_padded)
        async with httpx.AsyncClient(headers=EDGAR_HEADERS, timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=3, max=15))
    async def _get_older_submissions_json(self, file_name: str) -> dict:
        url = f"https://data.sec.gov/submissions/{file_name}"
        async with httpx.AsyncClient(headers=EDGAR_HEADERS, timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _extract_13f_filings(data: dict) -> list[dict]:
        recent = data.get("filings", {}).get("recent", {})
        form_types = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        primary_docs = recent.get("primaryDocument", [])

        return [
            {
                "accessionNumber": accessions[i].replace("-", ""),
                "filingDate": filing_dates[i],
                "reportDate": report_dates[i],
                "primaryDocument": primary_docs[i] if i < len(primary_docs) else "",
            }
            for i, ft in enumerate(form_types)
            if ft in ("13F-HR", "13F-HR/A")
        ]

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _parse_13f(
        self, cik_padded: str, accession_nodash: str, primary_doc: str = ""
    ) -> list[dict]:
        cik = cik_padded.lstrip("0")
        base_url = ARCHIVES_BASE.format(cik=cik, accession=accession_nodash)

        async with httpx.AsyncClient(
            headers=EDGAR_HEADERS, follow_redirects=True, timeout=60
        ) as client:
            xml_content = await self._fetch_infotable_xml(
                client, cik, accession_nodash, primary_doc, base_url
            )

        if not xml_content:
            raise ValueError(f"Could not fetch infotable XML for accession {accession_nodash}")

        if xml_content.strip().startswith(("<!DOCTYPE html", "<html")):
            return _parse_html_holdings(xml_content)

        return _parse_infotable_xml(xml_content)

    async def _fetch_infotable_xml(
        self,
        client: httpx.AsyncClient,
        cik: str,
        accession_nodash: str,
        primary_doc: str,
        base_url: str,
    ) -> str | None:
        """Try multiple strategies to find and fetch the 13F information table XML."""

        # Strategy 1: filing index JSON (most accurate, 1 request, no 404 guessing)
        try:
            xml_content = await self._fetch_infotable_from_index_json(
                client, base_url, accession_nodash
            )
            if xml_content:
                return xml_content
        except Exception:
            pass

        # Strategy 2: standard infotable.xml / informationtable.xml
        for fname in INFOTABLE_FILENAMES:
            try:
                resp = await client.get(base_url + fname)
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code == 429:
                    await asyncio.sleep(1.0)
                await asyncio.sleep(0.15)
            except Exception:
                continue

        # Strategy 3: filing index HTM (expanded search)
        try:
            xml_content = await self._fetch_infotable_from_index_htm(
                client, base_url, accession_nodash
            )
            if xml_content:
                return xml_content
        except Exception:
            pass

        # Strategy 4: root primary_doc.xml
        if primary_doc:
            try:
                xml_content = await self._fetch_root_primary_doc(
                    client, cik, accession_nodash, primary_doc
                )
                if xml_content:
                    return xml_content
            except Exception:
                pass

        return None

    async def _fetch_infotable_from_index_json(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        accession_nodash: str,
    ) -> str | None:
        index_url = f"{base_url}index.json"
        resp = await client.get(index_url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        items = data.get("directory", {}).get("item", [])
        if not items:
            return None

        filename = _find_infotable_filename(items)
        if not filename:
            return None
        await asyncio.sleep(0.1)
        xml_resp = await client.get(base_url + filename)
        if xml_resp.status_code == 200:
            return xml_resp.text
        return None

    async def _fetch_infotable_from_index_htm(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        accession_nodash: str,
    ) -> str | None:
        hyphenated = f"{accession_nodash[:10]}-{accession_nodash[10:12]}-{accession_nodash[12:]}"
        idx_resp = await client.get(base_url + f"{hyphenated}-index.html")
        if idx_resp.status_code != 200:
            return None

        xml_url = _find_infotable_url(idx_resp.text, base_url)
        if xml_url:
            await asyncio.sleep(0.1)
            xml_resp = await client.get(xml_url)
            if xml_resp.status_code == 200:
                return xml_resp.text

        soup = BeautifulSoup(idx_resp.text, "html.parser")
        for link in soup.find_all("a"):
            href = str(link.get("href", ""))
            if (
                href.endswith(".xml")
                and "primary_doc" not in href
                and not href.endswith("_htm.xml")
            ):
                full_url = href if href.startswith("http") else f"https://www.sec.gov{href}"
                await asyncio.sleep(0.1)
                xml_resp = await client.get(full_url)
                if xml_resp.status_code == 200:
                    text = xml_resp.text
                    if "infotable" in text.lower() or "nameOfIssuer" in text:
                        return text
        return None

    async def _fetch_root_primary_doc(
        self,
        client: httpx.AsyncClient,
        cik: str,
        accession_nodash: str,
        primary_doc: str,
    ) -> str | None:
        xml_filename = primary_doc.rsplit("/", 1)[-1] if "/" in primary_doc else primary_doc
        if not xml_filename.endswith(".xml"):
            return None
        root_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}/{xml_filename}"
        )
        resp = await client.get(root_url)
        if resp.status_code == 200:
            return resp.text
        return None


def _parse_infotable_xml(xml_content: str) -> list[dict]:
    """Parse 13F infotable XML into list of holding dicts."""
    root = ET.fromstring(xml_content)
    holdings = []

    for ns in NS_PATTERNS:
        info_tables = root.findall(f".//{ns}infoTable")
        if not info_tables:
            info_tables = root.findall(f".//{ns}InfoTable")
        if info_tables:
            for table in info_tables:

                def g(tag):
                    for n in NS_PATTERNS:
                        el = table.find(f"{n}{tag}")
                        if el is None:
                            el = table.find(f"{n}{tag[0].upper() + tag[1:]}")
                        if el is not None and el.text:
                            return el.text.strip()
                    return ""

                shares_el = table.find(f"{ns}shrsOrPrnAmt")
                if shares_el is None:
                    shares_el = table.find(f"{ns}ShrsorPrnAmt")
                shares = 0
                if shares_el is not None:
                    for n in NS_PATTERNS:
                        s = shares_el.find(f"{n}sshPrnamt")
                        if s is None:
                            s = shares_el.find(f"{n}SshPrnamt")
                        if s is not None and s.text:
                            try:
                                shares = int(s.text.strip())
                            except ValueError:
                                pass
                            break

                holdings.append(
                    {
                        "name": g("nameOfIssuer"),
                        "cusip": g("cusip"),
                        "value": _safe_int(g("value")),
                        "shares": shares,
                        "put_call": g("putCall"),
                    }
                )
            break

    return holdings


def _parse_html_holdings(html_content: str) -> list[dict]:
    """Parse 13F holdings from the XSLT-transformed HTML cover page."""
    soup = BeautifulSoup(html_content, "html.parser")
    holdings: list[dict] = []

    tables = soup.find_all("table")
    data_table = None
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue
        header_text = " ".join(
            cell.get_text(strip=True).lower() for cell in rows[0].find_all(["th", "td"])
        )
        if "name of issuer" in header_text or "issuer" in header_text:
            data_table = table
            break

    if data_table is None:
        candidate = None
        max_rows = 0
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) > max_rows:
                max_rows = len(rows)
                candidate = table
        if candidate and max_rows >= 3:
            data_table = candidate

    if data_table is None:
        return holdings

    rows = data_table.find_all("tr")
    headers = [cell.get_text(strip=True).lower() for cell in rows[0].find_all(["th", "td"])]

    def col_index(predicates: tuple[str, ...]) -> int | None:
        for i, h in enumerate(headers):
            if any(p in h for p in predicates):
                return i
        return None

    name_i = col_index(("name of issuer", "issuer name", "name")) or 0
    cusip_i = col_index(("cusip",))
    value_i = col_index(("value",))
    shares_i = col_index(("shrs", "prn", "shares", "principal", "amount"))
    putcall_i = col_index(("put/call", "put call", "put_call"))

    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        cell_texts = [cell.get_text(strip=True) for cell in cells]

        def get(i: int | None) -> str:
            return cell_texts[i] if i is not None and i < len(cell_texts) else ""

        name = get(name_i)
        if not name or name.lower() in ("", "name of issuer", "issuer"):
            continue

        holdings.append(
            {
                "name": name,
                "cusip": get(cusip_i).upper(),
                "value": _safe_int(get(value_i).replace("$", "").replace(",", "")),
                "shares": _safe_int(get(shares_i).replace(",", "")),
                "put_call": get(putcall_i).upper(),
            }
        )

    return holdings


def _holdings_to_text(holdings: list[dict], period: str) -> str:
    lines = [f"13F Holdings — Period: {period}", f"Total positions: {len(holdings)}", ""]
    for h in holdings:
        lines.append(
            f"{h['name']} | CUSIP:{h['cusip']} | Value:${h['value']}K | Shares:{h['shares']}"
        )
    return "\n".join(lines)


def _period_label(report_date: str) -> str:
    """Convert '2024-09-30' → '2024-Q3'."""
    try:
        dt = datetime.strptime(report_date, "%Y-%m-%d")
        q = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{q}"
    except ValueError:
        return report_date


def _find_infotable_filename(items: list[dict]) -> str | None:
    for item in items:
        if item.get("type", "").upper() == "INFORMATION TABLE":
            name = item.get("name", "")
            if name.endswith(".xml"):
                return name
    for item in items:
        name = item.get("name", "")
        if name.endswith(".xml") and "primary_doc" not in name and not name.endswith("_htm.xml"):
            return name
    return None


def _find_infotable_url(index_html: str, base_url: str) -> str | None:
    for pattern in [
        r'href="([^"]*infotable[^"]*\.xml)"',
        r'href="([^"]*informationtable[^"]*\.xml)"',
    ]:
        m = re.search(pattern, index_html, re.IGNORECASE)
        if m:
            path = m.group(1)
            return path if path.startswith("http") else f"https://www.sec.gov{path}"
    return None


def _safe_int(val: str) -> int:
    try:
        return int(val.replace(",", ""))
    except (ValueError, AttributeError):
        return 0
