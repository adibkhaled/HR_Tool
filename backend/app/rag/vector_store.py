from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VectorRecord:
    id: str
    tenant_id: str
    document_id: str
    document_type: str
    text: str
    embedding: tuple[float, ...]
    source_offset_start: int | None = None
    source_offset_end: int | None = None
    ready: bool = True
    archived: bool = False
    eligible: bool = True


class EmbeddingProvider(Protocol):
    dimension: int
    model_version: str

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]: ...


class HashEmbeddingProvider:
    """Deterministic local provider used for tests and development."""

    model_version = "hash-embedding-v1"

    def __init__(self, dimension: int = 32) -> None:
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
            values = [digest[index % len(digest)] / 255 for index in range(self.dimension)]
            norm = math.sqrt(sum(value * value for value in values)) or 1
            vectors.append(tuple(value / norm for value in values))
        return vectors


class VectorStore(Protocol):
    def upsert(self, records: list[VectorRecord]) -> None: ...

    def similarity_search(
        self,
        query: tuple[float, ...],
        *,
        tenant_id: str,
        top_k: int = 10,
        document_type: str = "resume",
    ) -> list[tuple[VectorRecord, float]]: ...


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.records: dict[str, VectorRecord] = {}

    def upsert(self, records: list[VectorRecord]) -> None:
        self.records.update({record.id: record for record in records})

    def similarity_search(self, query: tuple[float, ...], *, tenant_id: str, top_k: int = 10, document_type: str = "resume") -> list[tuple[VectorRecord, float]]:
        candidates = [record for record in self.records.values() if record.tenant_id == tenant_id and record.document_type == document_type and record.ready and not record.archived and record.eligible]
        scored = [(record, sum(left * right for left, right in zip(query, record.embedding))) for record in candidates]
        return sorted(scored, key=lambda item: item[1], reverse=True)[: max(0, top_k)]


class PgVectorStore(InMemoryVectorStore):
    """Adapter seam for the PostgreSQL/pgvector implementation.

    The in-memory behavior makes API and provider contracts usable without a running database.
    """

