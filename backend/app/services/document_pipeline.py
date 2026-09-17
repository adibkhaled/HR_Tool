from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from io import BytesIO
from xml.etree import ElementTree

SUPPORTED_TYPES = {
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    start: int
    end: int


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_text(content: bytes, content_type: str) -> str:
    if content_type == "text/plain":
        return normalize_text(content.decode("utf-8-sig"))
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with zipfile.ZipFile(BytesIO(content)) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        return normalize_text(" ".join(node.text or "" for node in root.iter()))
    if content_type == "application/pdf":
        if not content.startswith(b"%PDF"):
            raise ValueError("The PDF content signature is invalid")
        raw = content.decode("latin-1", errors="ignore")
        return normalize_text(" ".join(re.findall(r"\(([^()]*)\)", raw)))
    raise ValueError("Unsupported document type")


def chunk_text(text: str, *, size: int = 800, overlap: int = 80) -> list[DocumentChunk]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    chunks: list[DocumentChunk] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        chunks.append(DocumentChunk(normalized[start:end], start, end))
        if end == len(normalized):
            break
        start = max(start + 1, end - overlap)
    return chunks


def parse_skills(text: str) -> list[str]:
    match = re.search(r"(?:skills?|technologies)\s*:\s*([^\n]+)", text, re.IGNORECASE)
    if not match:
        return []
    return sorted({item.strip().lower() for item in re.split(r",|;|\|", match.group(1)) if item.strip()})
