"""Split documents into overlapping, paragraph-aware chunks with stable identifiers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.rag.document_loader import Document


@dataclass
class Chunk:
    chunk_id: str  # e.g. sample_clinic_faq.txt::0003
    source: str
    index: int
    text: str


def chunk_document(doc: Document, max_chars: int = 350, overlap_chars: int = 60) -> List[Chunk]:
    paras = [p.strip() for p in doc.text.split("\n\n") if p.strip()]
    pieces: List[str] = []
    for p in paras:
        if len(p) <= max_chars:
            pieces.append(p)
        else:  # split long paragraphs at sentence-ish boundaries
            buf = ""
            for sent in p.replace(". ", ".\n").split("\n"):
                if len(buf) + len(sent) + 1 > max_chars and buf:
                    pieces.append(buf.strip())
                    buf = buf[-overlap_chars:] + " " + sent
                else:
                    buf = (buf + " " + sent).strip()
            if buf:
                pieces.append(buf.strip())
    # merge a heading-only piece (short, no full stop) into the next piece so headings keep context
    merged: List[str] = []
    carry = ""
    for piece in pieces:
        if len(piece) < 60 and not piece.endswith(".") and not carry:
            carry = piece
            continue
        merged.append((carry + "\n" + piece).strip() if carry else piece)
        carry = ""
    if carry:
        merged.append(carry)
    return [Chunk(f"{doc.source}::{i:04d}", doc.source, i, t) for i, t in enumerate(merged)]


def chunk_documents(docs: List[Document], **kw) -> List[Chunk]:
    out: List[Chunk] = []
    for d in docs:
        out.extend(chunk_document(d, **kw))
    return out
