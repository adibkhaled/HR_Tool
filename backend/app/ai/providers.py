from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LLMProviderError(RuntimeError):
    """Safe, provider-neutral failure surfaced to the RAG layer."""


class LLMResponseError(LLMProviderError):
    pass


Transport = Callable[[str, int, float], dict[str, Any]]


class BaseLLMProvider(ABC):
    model_version: str

    @abstractmethod
    def complete(self, prompt: str, *, max_tokens: int = 1200) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class DeterministicLLMProvider(BaseLLMProvider):
    model_version: str = "deterministic-llm-v1"

    def complete(self, prompt: str, *, max_tokens: int = 1200) -> dict[str, Any]:
        return {"explanation": "Ranking is based only on indexed resume evidence and job requirements."}

FakeLLMProvider = DeterministicLLMProvider


@dataclass
class OpenAIProvider:
    model: str = "gpt-4o-mini"
    timeout_seconds: float = 10.0
    max_retries: int = 2
    api_key: str | None = None
    max_tokens: int = 1200
    base_url: str = "https://api.openai.com/v1/chat/completions"
    transport: Transport | None = None

    @property
    def model_version(self) -> str:
        return self.model

    def complete(self, prompt: str, *, max_tokens: int = 1200) -> dict[str, Any]:
        if not prompt.strip():
            raise LLMResponseError("LLM prompt must not be empty")
        requested_tokens = min(max(1, max_tokens), self.max_tokens)
        if self.transport is None and not self.api_key:
            raise LLMProviderError("OpenAI provider is not configured")
        for attempt in range(self.max_retries + 1):
            try:
                response = self._call(prompt, requested_tokens)
                if not isinstance(response, dict):
                    raise LLMResponseError("LLM returned malformed output")
                return response
            except (TimeoutError, httpx.TimeoutException) as exc:
                logger.warning("llm provider timeout provider=%s model=%s attempt=%s", type(self).__name__, self.model_version, attempt + 1)
                if attempt >= self.max_retries:
                    raise LLMProviderError("LLM provider timed out") from exc
            except LLMResponseError:
                raise
            except Exception as exc:
                logger.warning("llm provider outage provider=%s model=%s attempt=%s error=%s", type(self).__name__, self.model_version, attempt + 1, type(exc).__name__)
                if attempt >= self.max_retries:
                    raise LLMProviderError("LLM provider unavailable") from exc
        raise LLMProviderError("LLM provider unavailable")

    def _call(self, prompt: str, max_tokens: int) -> dict[str, Any]:
        if self.transport is not None:
            return self.transport(prompt, max_tokens, self.timeout_seconds)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
        response = httpx.post(self.base_url, headers=headers, json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        body = response.json()
        content = body.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(content, str):
            raise LLMResponseError("LLM returned malformed output")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {"explanation": content}
        if not isinstance(parsed, dict):
            raise LLMResponseError("LLM returned malformed output")
        return parsed


@dataclass
class OllamaProvider(OpenAIProvider):
    base_url: str = "http://localhost:11434/api/chat"

    def _call(self, prompt: str, max_tokens: int) -> dict[str, Any]:
        if self.transport is not None:
            return self.transport(prompt, max_tokens, self.timeout_seconds)
        response = httpx.post(
            self.base_url,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        content = body.get("message", {}).get("content")
        if not isinstance(content, str):
            raise LLMResponseError("LLM returned malformed output")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {"explanation": content}
        if not isinstance(parsed, dict):
            raise LLMResponseError("LLM returned malformed output")
        return parsed


@dataclass
@dataclass
class AzureOpenAIProvider(OpenAIProvider):
    deployment: str = "default"
    api_version: str = "2024-10-21"

    @property
    def model_version(self) -> str:
        return f"azure:{self.deployment}"

    def _call(self, prompt: str, max_tokens: int) -> dict[str, Any]:
        if self.transport is not None:
            return self.transport(prompt, max_tokens, self.timeout_seconds)
        if not self.api_key:
            raise LLMProviderError("Azure OpenAI provider is not configured")
        endpoint = f"{self.base_url.rstrip('/')}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
        response = httpx.post(endpoint, headers={"api-key": self.api_key}, json={"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}, timeout=self.timeout_seconds)
        response.raise_for_status()
        body = response.json()
        content = body.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(content, str):
            raise LLMResponseError("LLM returned malformed output")
        return {"explanation": content}