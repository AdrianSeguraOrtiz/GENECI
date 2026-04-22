"""Shared helpers for converting local simulator PDFs into plain text."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def resolve_pdftotext_bin() -> str:
    binary = shutil.which("pdftotext")
    if binary is None:
        raise RuntimeError("pdftotext not available in PATH")
    return binary


def output_path_for_pdf(pdf_path: Path) -> Path:
    if pdf_path.name == "source.pdf":
        return pdf_path.with_name("article.txt")
    return pdf_path.with_suffix(".txt")


def extract_pdf_to_text(
    *,
    pdf_path: Path,
    output_path: Path,
    pdftotext_bin: str | None = None,
) -> tuple[bool, str | None]:
    binary = pdftotext_bin
    if binary is None:
        try:
            binary = resolve_pdftotext_bin()
        except RuntimeError as exc:
            return False, str(exc)

    result = subprocess.run(
        [binary, "-layout", str(pdf_path), str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return (
            False,
            result.stderr.strip() or result.stdout.strip() or "pdftotext failed",
        )
    return True, None
