"""Extract local simulator paper PDFs into plain-text sidecars.

This script operates on local evidence directories under:

  components/generate_data/<simulator_id>/papers/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from shared.catalog_simulators import (
    DEFAULT_SIMULATOR_EVIDENCE_ROOT,
    discover_evidence_dirs,
    select_simulators,
)
from shared.paper_text import (
    extract_pdf_to_text,
    output_path_for_pdf,
    resolve_pdftotext_bin,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract local simulator paper PDFs into .txt sidecars."
    )
    parser.add_argument(
        "--simulator-evidence-root",
        type=Path,
        default=DEFAULT_SIMULATOR_EVIDENCE_ROOT,
        help=f"Path to simulator evidence directories. Default: {DEFAULT_SIMULATOR_EVIDENCE_ROOT}",
    )
    parser.add_argument(
        "--simulator",
        action="append",
        default=[],
        help="Simulator id/evidence directory to operate on (repeatable). If omitted, scans every evidence dir.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-extract text even if the output .txt already exists.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed extraction.",
    )
    return parser.parse_args(argv)


def papers_root_for(evidence_dir: Path) -> Path:
    return evidence_dir / "papers"


def extract_pdf(
    *,
    pdf_path: Path,
    output_path: Path,
    force: bool,
    pdftotext: str,
) -> str:
    existed_before = output_path.exists()
    if existed_before and not force:
        return "skipped"

    ok, error = extract_pdf_to_text(
        pdf_path=pdf_path,
        output_path=output_path,
        pdftotext_bin=pdftotext,
    )
    if not ok:
        raise RuntimeError(error or "unknown pdftotext error")
    return "updated" if existed_before else "created"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        pdftotext = resolve_pdftotext_bin()
        discovered = discover_evidence_dirs(args.simulator_evidence_root)
        selected = select_simulators(discovered, args.simulator)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    failures: list[str] = []
    counts = {"created": 0, "updated": 0, "skipped": 0, "missing": 0}

    for simulator_id, evidence_dir in selected:
        papers_root = papers_root_for(evidence_dir)
        if not papers_root.exists():
            counts["missing"] += 1
            print(f"[{simulator_id}] no papers directory: {papers_root}")
            continue

        pdf_paths = sorted(papers_root.rglob("*.pdf"))
        if not pdf_paths:
            print(f"[{simulator_id}] no PDFs found under {papers_root}")
            continue

        for pdf_path in pdf_paths:
            output_path = output_path_for_pdf(pdf_path)
            try:
                status = extract_pdf(
                    pdf_path=pdf_path,
                    output_path=output_path,
                    force=args.force,
                    pdftotext=pdftotext,
                )
                counts[status] += 1
                print(f"[{simulator_id}] {status}: {output_path}")
            except RuntimeError as exc:
                failures.append(f"{pdf_path}: {exc}")
                print(f"[{simulator_id}] FAILED: {pdf_path}: {exc}", file=sys.stderr)
                if args.fail_fast:
                    break
        if failures and args.fail_fast:
            break

    print(
        "Paper extraction summary: "
        f"created={counts['created']} updated={counts['updated']} "
        f"skipped={counts['skipped']} missing_dirs={counts['missing']}"
    )
    if failures:
        print("Paper extraction failures:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
