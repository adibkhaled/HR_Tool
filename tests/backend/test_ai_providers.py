import pytest

from backend.app.ai.providers import AzureOpenAIProvider, DeterministicLLMProvider, LLMProviderError, OllamaProvider, OpenAIProvider


def test_deterministic_provider_is_injectable() -> None:
    assert "indexed resume evidence" in DeterministicLLMProvider().complete("resume")["explanation"]


def test_provider_retries_timeout_and_redacts_failure() -> None:
    attempts = 0

    def transport(prompt: str, max_tokens: int, timeout: float) -> dict[str, object]:
        nonlocal attempts
        attempts += 1
        raise TimeoutError("secret prompt content")

    with pytest.raises(LLMProviderError, match="timed out") as error:
        OpenAIProvider(transport=transport, max_retries=2).complete("private resume")
    assert attempts == 3
    assert "secret" not in str(error.value)


def test_provider_rejects_malformed_transport_output() -> None:
    with pytest.raises(Exception, match="malformed"):
        OpenAIProvider(transport=lambda prompt, max_tokens, timeout: []) .complete("resume")


def test_provider_success_clamps_tokens_and_azure_is_injectable() -> None:
    calls: list[tuple[str, int, float]] = []

    def transport(prompt: str, max_tokens: int, timeout: float) -> dict[str, object]:
        calls.append((prompt, max_tokens, timeout))
        return {"explanation": "grounded"}

    provider = AzureOpenAIProvider(deployment="hr-ranking", max_tokens=64, transport=transport)
    assert provider.complete("resume", max_tokens=1200) == {"explanation": "grounded"}
    assert provider.model_version == "azure:hr-ranking"
    assert calls == [("resume", 64, 10.0)]


def test_provider_redacts_outage_diagnostics() -> None:
    def transport(prompt: str, max_tokens: int, timeout: float) -> dict[str, object]:
        raise RuntimeError("provider token and private resume")

    with pytest.raises(LLMProviderError, match="unavailable") as error:
        OpenAIProvider(transport=transport, max_retries=0).complete("private resume")
    assert "private" not in str(error.value)


def test_ollama_provider_parses_json_and_uses_local_chat_contract() -> None:
    calls: list[tuple[str, int, float]] = []

    def transport(prompt: str, max_tokens: int, timeout: float) -> dict[str, object]:
        calls.append((prompt, max_tokens, timeout))
        return {"explanation": "grounded locally"}

    provider = OllamaProvider(model="qwen2.5:7b", transport=transport)
    assert provider.complete("resume", max_tokens=64) == {"explanation": "grounded locally"}
    assert provider.model_version == "qwen2.5:7b"
    assert calls == [("resume", 64, 10.0)]