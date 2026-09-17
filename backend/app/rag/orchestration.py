from __future__ import annotations

from backend.app.ai.providers import BaseLLMProvider, DeterministicLLMProvider, LLMProviderError
from backend.app.rag.pipeline import Evidence, RagResult, Requirements, apply_policy, retrieve_candidates
from backend.app.rag.vector_store import EmbeddingProvider, VectorStore


def aggregate_candidates(query: str, requirements: Requirements, *, tenant_id: str, store: VectorStore, provider: EmbeddingProvider, top_k: int = 5, llm: BaseLLMProvider | None = None) -> list[RagResult]:
    llm = llm or DeterministicLLMProvider()
    results: list[RagResult] = []
    for record, score in retrieve_candidates(query, tenant_id=tenant_id, store=store, provider=provider, top_k=top_k):
        text = apply_policy(record.text)
        matching = [skill for skill in requirements.skills if skill in text.lower()]
        missing = [skill for skill in requirements.skills if skill not in matching]
        evidence = [Evidence(evidence_id=record.id, snippet=record.text[:400], score=max(0, min(1, score)))]
        degraded = False
        try:
            response = llm.complete(record.text[:1000])
        except LLMProviderError:
            response = DeterministicLLMProvider().complete(record.text[:1000])
            degraded = True
        explanation = response.get("explanation") if isinstance(response.get("explanation"), str) else "Grounded evidence requires human review."
        results.append(RagResult(resume_id=record.document_id, normalized_score=max(0, min(1, score)), matching_skills=matching, missing_skills=missing, experience_comparison="Experience requires human review", explanation=explanation, confidence=max(0, min(1, score)), degraded=degraded, evidence=evidence))
    return results


def orchestrate(query: str, requirements: Requirements, *, tenant_id: str, store: VectorStore, provider: EmbeddingProvider, top_k: int = 5, llm: BaseLLMProvider | None = None) -> dict[str, object]:
    try:
        results = aggregate_candidates(query, requirements, tenant_id=tenant_id, store=store, provider=provider, top_k=top_k, llm=llm)
        return {"results": results, "degraded": any(result.degraded for result in results)}
    except (LLMProviderError, ValueError, TypeError) as exc:
        return {"results": [], "degraded": True, "error": str(exc)}
