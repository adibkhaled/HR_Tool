from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator

from backend.app.rag.vector_store import EmbeddingProvider, VectorStore

PROTECTED_ATTRIBUTES = {"age", "date of birth", "gender", "sex", "race", "ethnicity", "religion", "disability", "nationality", "marital status"}


@dataclass(frozen=True)
class Requirements:
    skills: tuple[str, ...]
    minimum_experience: int | None


def extract_requirements(text: str) -> Requirements:
    skills_match = re.search(r"(?:skills?|technologies|required skills?)\s*:\s*([^\n;]+)", text, re.IGNORECASE)
    skills = tuple(sorted({skill.strip().lower() for skill in re.split(r",|;|\|", skills_match.group(1)) if skill.strip()})) if skills_match else ()
    experience_match = re.search(r"(\d+)\+?\s+years?", text, re.IGNORECASE)
    return Requirements(skills, int(experience_match.group(1)) if experience_match else None)


def apply_policy(text: str) -> str:
    return " ".join(word for word in text.split() if word.lower().strip(".,:;()") not in PROTECTED_ATTRIBUTES)


class Evidence(BaseModel):
    evidence_id: str
    snippet: str
    score: float = Field(ge=0, le=1)


class RagResult(BaseModel):
    resume_id: str
    normalized_score: float = Field(ge=0, le=1)
    matching_skills: list[str]
    missing_skills: list[str]
    experience_comparison: str
    explanation: str
    confidence: float = Field(ge=0, le=1)
    degraded: bool = False
    evidence: list[Evidence]

    @field_validator("matching_skills", "missing_skills")
    @classmethod
    def normalize_skills(cls, values: list[str]) -> list[str]:
        return sorted({value.lower().strip() for value in values if value.strip()})


def retrieve_candidates(query: str, *, tenant_id: str, store: VectorStore, provider: EmbeddingProvider, top_k: int = 5) -> list[tuple[object, float]]:
    if top_k < 1 or top_k > 50:
        raise ValueError("top_k must be between 1 and 50")
    return store.similarity_search(provider.embed([apply_policy(query)])[0], tenant_id=tenant_id, top_k=top_k)
