"""List, fetch, or clean local publication caches for tool papers.

This script uses `toolspec.publication` references (typically DOI URLs) to create
local analysis caches under:

  components/inference_tools_dev/tools/<tool_id>/papers/<publication_slug>/

For each publication it tries to:
1) store DOI/citation metadata,
2) resolve the landing page,
3) download a PDF when directly accessible,
4) extract `article.txt` from `source.pdf` using `pdftotext` when available.

Exit codes:
- 0: requested action completed for all selected tools
- 1: one or more fetch/clean operations failed
- 2: usage/runtime error (invalid catalog/tool roots, unknown tool ids, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from shared.catalog_tools import (
    DEFAULT_CATALOG_TOOLS_ROOT,
    DEFAULT_TOOL_SOURCES_ROOT,
    discover_tool_source_dirs,
    load_toolspec_publications,
    select_tools,
)
from shared.paper_text import extract_pdf_to_text

DEFAULT_USER_AGENT = "GENECI-inference-tools-dev/1.0 (+https://github.com/adriansegura99/GENECI)"
DEFAULT_TIMEOUT_SECONDS = 30
HTML_ACCEPT = "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"
PDF_ACCEPT = "application/pdf,application/octet-stream;q=0.9,*/*;q=0.1"
CSL_JSON_ACCEPT = "application/vnd.citationstyles.csl+json"
DOI_URL_RE = re.compile(r"^https?://(?:dx\.)?doi\.org/(10\.\S+)$", re.IGNORECASE)
RAW_DOI_RE = re.compile(r"^(10\.\S+)$", re.IGNORECASE)
PDF_CANDIDATE_RE = re.compile(r"(\.pdf(?:$|[?#]))|(/pdf(?:$|[/?#]))", re.IGNORECASE)
ABSTRACT_META_KEYS = (
    "citation_abstract",
    "description",
    "dc.description",
    "dc.description.abstract",
    "twitter:description",
    "og:description",
)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    final_url: str
    content_type: str
    body: bytes


class PublicationHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, list[str]] = {}
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value for key, value in attrs if value is not None}
        if tag.lower() == "meta":
            key = attr_map.get("name") or attr_map.get("property")
            content = attr_map.get("content")
            if key and content:
                normalized_key = key.strip().lower()
                self.meta.setdefault(normalized_key, []).append(content.strip())
        if tag.lower() == "a":
            href = attr_map.get("href")
            if href:
                self.hrefs.append(href.strip())


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List, fetch, or clean local publication caches under "
            "components/inference_tools_dev/tools/<tool_id>/papers."
        )
    )
    parser.add_argument(
        "action",
        choices=("list", "fetch", "clean"),
        help="Action to perform on publication caches.",
    )
    parser.add_argument(
        "--catalog-tools-root",
        type=Path,
        default=DEFAULT_CATALOG_TOOLS_ROOT,
        help=f"Path to catalog tools directory. Default: {DEFAULT_CATALOG_TOOLS_ROOT}",
    )
    parser.add_argument(
        "--tool-sources-root",
        type=Path,
        default=DEFAULT_TOOL_SOURCES_ROOT,
        help=f"Path to tool source directories. Default: {DEFAULT_TOOL_SOURCES_ROOT}",
    )
    parser.add_argument(
        "--tool",
        action="append",
        default=[],
        help="Tool id to operate on (repeatable). If omitted, uses all tool source dirs.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"HTTP timeout in seconds. Default: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch publications even if local cache metadata already exists.",
    )
    parser.add_argument(
        "--keep-html",
        action="store_true",
        help="Persist landing_page.html for debugging.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed fetch/clean action.",
    )
    return parser.parse_args(argv)


def papers_root_for(tool_source_dir: Path) -> Path:
    return tool_source_dir / "papers"


def normalize_reference_url(reference: str) -> str:
    token = reference.strip()
    doi_match = DOI_URL_RE.match(token)
    if doi_match:
        return f"https://doi.org/{doi_match.group(1)}"

    raw_doi_match = RAW_DOI_RE.match(token)
    if raw_doi_match:
        return f"https://doi.org/{raw_doi_match.group(1)}"

    return token


def reference_slug(reference: str, index: int) -> str:
    parsed = urlparse(reference)
    doi_match = DOI_URL_RE.match(reference)
    if doi_match:
        slug_source = doi_match.group(1)
    elif parsed.scheme and parsed.netloc:
        slug_source = parsed.netloc + parsed.path
    else:
        slug_source = reference

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug_source).strip("_").lower()
    if not slug:
        slug = f"publication_{index:02d}"
    return f"{index:02d}_{slug}"


def http_get(
    *,
    url: str,
    timeout: int,
    accept: str,
) -> HttpResponse:
    req = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": DEFAULT_USER_AGENT,
        },
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
            return HttpResponse(
                status=getattr(response, "status", 200),
                final_url=response.geturl(),
                content_type=content_type.strip().lower(),
                body=response.read(),
            )
    except HTTPError as exc:
        content_type = exc.headers.get("Content-Type", "").split(";", 1)[0]
        return HttpResponse(
            status=exc.code,
            final_url=exc.geturl(),
            content_type=content_type.strip().lower(),
            body=exc.read(),
        )
    except URLError as exc:
        raise RuntimeError(f"request failed for {url}: {exc.reason}") from exc


def decode_text(payload: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=True)
        fh.write("\n")


def parse_html_document(html_text: str) -> PublicationHTMLParser:
    parser = PublicationHTMLParser()
    parser.feed(html_text)
    return parser


def select_abstract(meta: dict[str, list[str]]) -> str | None:
    for key in ABSTRACT_META_KEYS:
        values = meta.get(key, [])
        for value in values:
            normalized = value.strip()
            if normalized:
                return normalized
    return None


def extract_pdf_candidates(*, base_url: str, parser: PublicationHTMLParser) -> list[str]:
    candidates: list[str] = []

    def add_candidate(raw_url: str) -> None:
        normalized = raw_url.strip()
        if not normalized:
            return
        absolute = urljoin(base_url, normalized)
        if absolute not in candidates:
            candidates.append(absolute)

    for key in ("citation_pdf_url", "pdf_url"):
        for value in parser.meta.get(key, []):
            add_candidate(value)

    for href in parser.hrefs:
        if PDF_CANDIDATE_RE.search(href):
            add_candidate(href)

    return candidates


def maybe_write_text(path: Path, text: str | None) -> None:
    if not text:
        return
    normalized = text.strip()
    if not normalized:
        return
    path.write_text(normalized + "\n", encoding="utf-8")


def fetch_doi_metadata(*, reference_url: str, timeout: int) -> dict[str, Any] | None:
    response = http_get(url=reference_url, timeout=timeout, accept=CSL_JSON_ACCEPT)
    if response.status != 200 or "json" not in response.content_type:
        return None

    try:
        payload = json.loads(decode_text(response.body))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None

    payload["_source_url"] = reference_url
    payload["_final_url"] = response.final_url
    return payload


def try_download_pdf(
    *,
    url: str,
    timeout: int,
    pdf_path: Path,
) -> tuple[bool, str | None, str | None]:
    response = http_get(url=url, timeout=timeout, accept=PDF_ACCEPT)
    if response.status != 200:
        return False, None, f"http_status={response.status}"
    if response.content_type != "application/pdf":
        return False, response.final_url, f"content_type={response.content_type or 'unknown'}"

    pdf_path.write_bytes(response.body)
    return True, response.final_url, None


def fetch_publication(
    *,
    tool_id: str,
    reference: str,
    publication_dir: Path,
    timeout: int,
    keep_html: bool,
    force: bool,
) -> bool:
    metadata_path = publication_dir / "metadata.json"
    if metadata_path.exists() and not force:
        print(f"  - {publication_dir.name}: SKIP (already fetched)")
        return True

    if publication_dir.exists() and force:
        shutil.rmtree(publication_dir)
    publication_dir.mkdir(parents=True, exist_ok=True)

    reference_url = normalize_reference_url(reference)
    pdf_path = publication_dir / "source.pdf"
    article_txt_path = publication_dir / "article.txt"
    abstract_txt_path = publication_dir / "abstract.txt"
    landing_url_path = publication_dir / "landing_url.txt"
    reference_path = publication_dir / "reference.txt"
    fetch_report_path = publication_dir / "fetch_report.json"

    reference_path.write_text(reference_url + "\n", encoding="utf-8")

    report: dict[str, Any] = {
        "tool_id": tool_id,
        "reference": reference,
        "reference_url": reference_url,
        "fetched_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "landing_url": None,
        "pdf_url": None,
        "pdf_downloaded": False,
        "article_txt_extracted": False,
        "abstract_saved": False,
        "metadata_saved": False,
        "warnings": [],
    }

    doi_metadata = fetch_doi_metadata(reference_url=reference_url, timeout=timeout)
    if doi_metadata is not None:
        save_json(publication_dir / "citation_metadata.json", doi_metadata)
        report["metadata_saved"] = True

    pdf_ok, pdf_final_url, pdf_error = try_download_pdf(
        url=reference_url,
        timeout=timeout,
        pdf_path=pdf_path,
    )
    if pdf_ok:
        report["pdf_url"] = pdf_final_url or reference_url
        report["pdf_downloaded"] = True
    elif pdf_error:
        report["warnings"].append(f"direct_pdf_fetch: {pdf_error}")

    landing_response: HttpResponse | None = None
    parser: PublicationHTMLParser | None = None
    if not report["pdf_downloaded"]:
        landing_response = http_get(url=reference_url, timeout=timeout, accept=HTML_ACCEPT)
        if landing_response.status != 200:
            report["warnings"].append(f"landing_page_http_status={landing_response.status}")
        else:
            report["landing_url"] = landing_response.final_url
            landing_url_path.write_text(landing_response.final_url + "\n", encoding="utf-8")
            if landing_response.content_type == "application/pdf":
                pdf_path.write_bytes(landing_response.body)
                report["pdf_url"] = landing_response.final_url
                report["pdf_downloaded"] = True
            else:
                html_text = decode_text(landing_response.body)
                parser = parse_html_document(html_text)
                if keep_html:
                    (publication_dir / "landing_page.html").write_text(
                        html_text, encoding="utf-8"
                    )

                abstract = select_abstract(parser.meta)
                if abstract:
                    maybe_write_text(abstract_txt_path, abstract)
                    report["abstract_saved"] = True

                pdf_candidates = extract_pdf_candidates(
                    base_url=landing_response.final_url,
                    parser=parser,
                )
                for candidate_url in pdf_candidates:
                    pdf_ok, pdf_final_url, pdf_error = try_download_pdf(
                        url=candidate_url,
                        timeout=timeout,
                        pdf_path=pdf_path,
                    )
                    if pdf_ok:
                        report["pdf_url"] = pdf_final_url or candidate_url
                        report["pdf_downloaded"] = True
                        break
                if not report["pdf_downloaded"] and pdf_candidates:
                    report["warnings"].append("pdf_candidate_fetch_failed")

    if not report["landing_url"]:
        if landing_response is not None and landing_response.final_url:
            report["landing_url"] = landing_response.final_url
            landing_url_path.write_text(landing_response.final_url + "\n", encoding="utf-8")
        else:
            landing_url_path.write_text(reference_url + "\n", encoding="utf-8")

    if report["pdf_downloaded"]:
        extracted, extract_error = extract_pdf_to_text(
            pdf_path=pdf_path,
            output_path=article_txt_path,
        )
        report["article_txt_extracted"] = extracted
        if not extracted and extract_error:
            report["warnings"].append(f"pdf_to_text: {extract_error}")

    save_json(fetch_report_path, report)
    metadata_payload = {
        "tool_id": tool_id,
        "reference": reference,
        "reference_url": reference_url,
        "landing_url": report["landing_url"],
        "pdf_url": report["pdf_url"],
        "paths": {
            "reference": reference_path.name,
            "landing_url": landing_url_path.name,
            "citation_metadata": "citation_metadata.json"
            if report["metadata_saved"]
            else None,
            "pdf": pdf_path.name if report["pdf_downloaded"] else None,
            "article_txt": article_txt_path.name
            if report["article_txt_extracted"]
            else None,
            "abstract_txt": abstract_txt_path.name if report["abstract_saved"] else None,
            "fetch_report": fetch_report_path.name,
        },
    }
    save_json(metadata_path, metadata_payload)

    if report["metadata_saved"] or report["landing_url"] or report["pdf_downloaded"]:
        suffix = []
        if report["pdf_downloaded"]:
            suffix.append("pdf")
        if report["article_txt_extracted"]:
            suffix.append("txt")
        if report["abstract_saved"]:
            suffix.append("abstract")
        details = ",".join(suffix) if suffix else "metadata-only"
        print(f"  - {publication_dir.name}: OK ({details})")
        return True

    print(f"  - {publication_dir.name}: FAILED")
    return False


def clean_publications(*, tool_id: str, papers_root: Path) -> bool:
    if not papers_root.exists():
        print(f"[{tool_id}] SKIP: papers directory does not exist")
        return True

    print(f"[{tool_id}] removing {papers_root}")
    try:
        shutil.rmtree(papers_root)
    except OSError as exc:
        print(f"  FAILED: {exc}")
        return False

    print("  OK")
    return True


def list_publications(
    *,
    tool_id: str,
    tool_source_dir: Path,
    publications: list[str],
) -> None:
    papers_root = papers_root_for(tool_source_dir)
    print(f"- {tool_id}: papers_dir={papers_root}")
    for index, reference in enumerate(publications, start=1):
        publication_dir = papers_root / reference_slug(reference, index)
        status = "missing"
        if (publication_dir / "metadata.json").exists():
            status = "cached"
        elif publication_dir.exists():
            status = "partial"
        print(f"    [{index}] {reference} -> {publication_dir.name} ({status})")


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.timeout <= 0:
        raise RuntimeError("--timeout must be a positive integer.")

    discovered = discover_tool_source_dirs(args.tool_sources_root)
    if not discovered:
        raise RuntimeError(
            f"No tool source directories found under: {args.tool_sources_root}"
        )

    selected = select_tools(discovered, args.tool)

    if args.action == "list":
        for tool_id, tool_source_dir in selected:
            publications = load_toolspec_publications(
                tool_id=tool_id,
                catalog_tools_root=args.catalog_tools_root,
            )
            list_publications(
                tool_id=tool_id,
                tool_source_dir=tool_source_dir,
                publications=publications,
            )
        return 0

    failures = 0
    for tool_id, tool_source_dir in selected:
        papers_root = papers_root_for(tool_source_dir)
        if args.action == "clean":
            ok = clean_publications(tool_id=tool_id, papers_root=papers_root)
            if not ok:
                failures += 1
                if args.fail_fast:
                    break
            continue

        publications = load_toolspec_publications(
            tool_id=tool_id,
            catalog_tools_root=args.catalog_tools_root,
        )
        print(f"[{tool_id}] fetching {len(publications)} publication(s)")
        tool_ok = True
        for index, reference in enumerate(publications, start=1):
            publication_dir = papers_root / reference_slug(reference, index)
            ok = fetch_publication(
                tool_id=tool_id,
                reference=reference,
                publication_dir=publication_dir,
                timeout=args.timeout,
                keep_html=args.keep_html,
                force=args.force,
            )
            if ok:
                continue
            tool_ok = False
            if args.fail_fast:
                break

        if tool_ok:
            continue
        failures += 1
        if args.fail_fast:
            break

    print()
    print(
        "Summary: selected={selected} succeeded={succeeded} failed={failed}".format(
            selected=len(selected),
            succeeded=len(selected) - failures,
            failed=failures,
        )
    )
    return 0 if failures == 0 else 1


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
