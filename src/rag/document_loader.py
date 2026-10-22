"""Load TXT and PDF knowledge documents from a folder."""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from src.utils.exceptions import KnowledgeBaseError

log = logging.getLogger(__name__)
SUPPORTED = {".txt", ".pdf"}


@dataclass
class Document:
    source: str  # filename
    text: str
    sha256: str


def clean_text(text: str) -> str:
    """Normalise whitespace but keep paragraph breaks (used for chunking)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [" ".join(line.split()) for line in text.split("\n")]
    out, blank = [], 0
    for line in lines:
        if not line:
            blank += 1
            if blank == 1:
                out.append("")
        else:
            blank = 0
            out.append(line)
    return "\n".join(out).strip()


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise KnowledgeBaseError("pypdf is required to read PDF files (pip install pypdf).") from exc
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def load_file(path: Path) -> Document:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise KnowledgeBaseError(f"Unsupported file type: {path.name}")
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace") if suffix == ".txt" else _read_pdf(path)
    return Document(path.name, clean_text(text), hashlib.sha256(raw).hexdigest())


def load_documents(folder: Path) -> Tuple[List[Document], List[str]]:
    """Return (documents, warnings). One bad file never stops the others."""
    docs: List[Document] = []
    warnings: List[str] = []
    if not folder.exists():
        raise KnowledgeBaseError(f"Knowledge-base folder not found: {folder}")
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in SUPPORTED or path.name.startswith("."):
            continue
        try:
            doc = load_file(path)
            if not doc.text:
                warnings.append(f"{path.name}: no extractable text (scanned PDF?) - skipped")
                continue
            docs.append(doc)
        except Exception as exc:  # noqa: BLE001 - report and continue
            log.warning("Could not load %s: %s", path.name, exc)
            warnings.append(f"{path.name}: {exc}")
    return docs, warnings
