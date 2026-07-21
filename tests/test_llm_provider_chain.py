import json

import httpx
import pytest

from llm_provider_chain import (
    OrderedLLMRouter,
    ProviderChainExhausted,
    ProviderConfig,
    ProviderRequestError,
)


def providers():
    return [
        ProviderConfig("azure", "azure_responses", "gpt-5.6-sol", "https://azure.test/responses", "a"),
        ProviderConfig("gemini", "gemini_native", "gemini-3.5-flash", "https://gemini.test/v1beta", "g"),
        ProviderConfig("cloudflare", "cloudflare_workers", "@cf/meta/llama", "https://cf.test/client/v4", "c", "acct"),
        ProviderConfig("openrouter_ultra", "openai_compatible", "ultra:free", "https://or.test/v1", "o"),
        ProviderConfig("openrouter_super", "openai_compatible", "super:free", "https://or.test/v1", "o"),
    ]


def success_body(provider):
    if provider == "azure":
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": "OK"}]}]}
    if provider == "gemini":
        return {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}
    if provider == "cloudflare":
        return {"success": True, "result": {"response": "OK"}}
    return {"choices": [{"message": {"content": "OK"}}]}


def provider_for_request(request):
    url = str(request.url)
    if "azure.test" in url:
        return "azure"
    if "gemini.test" in url:
        return "gemini"
    if "cf.test" in url:
        return "cloudflare"
    body = json.loads(request.content)
    return "openrouter_ultra" if body["model"] == "ultra:free" else "openrouter_super"


def make_router(statuses):
    calls = []

    def handler(request):
        provider = provider_for_request(request)
        calls.append((provider, request))
        status = statuses.get(provider, 200)
        return httpx.Response(status, json=success_body(provider) if status == 200 else {"error": {"message": "not logged"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OrderedLLMRouter(providers(), client=client), calls


def run(router, **kwargs):
    return router.complete(
        [{"role": "system", "content": "Be concise"}, {"role": "user", "content": "Say OK"}],
        max_tokens=32,
        **kwargs,
    )


def test_exact_order_and_successful_primary():
    router, calls = make_router({})
    assert [p.name for p in router.providers] == [
        "azure", "gemini", "cloudflare", "openrouter_ultra", "openrouter_super"
    ]
    assert run(router) == "OK"
    assert [name for name, _ in calls] == ["azure"]


@pytest.mark.parametrize(
    "statuses,expected",
    [
        ({"azure": 503}, ["azure", "gemini"]),
        ({"azure": 503, "gemini": 429}, ["azure", "gemini", "cloudflare"]),
        ({"azure": 503, "gemini": 503, "cloudflare": 429}, ["azure", "gemini", "cloudflare", "openrouter_ultra"]),
        ({"azure": 503, "gemini": 503, "cloudflare": 503, "openrouter_ultra": 429}, ["azure", "gemini", "cloudflare", "openrouter_ultra", "openrouter_super"]),
    ],
)
def test_each_fallback_transition(statuses, expected):
    router, calls = make_router(statuses)
    assert run(router) == "OK"
    assert [name for name, _ in calls] == expected


def test_non_retryable_failure_stops_chain():
    router, calls = make_router({"azure": 400})
    with pytest.raises(ProviderRequestError) as exc:
        run(router)
    assert exc.value.retryable is False
    assert [name for name, _ in calls] == ["azure"]


def test_exhaustion_attempts_each_provider_once():
    router, calls = make_router({p.name: 503 for p in providers()})
    with pytest.raises(ProviderChainExhausted):
        run(router)
    assert [name for name, _ in calls] == [p.name for p in providers()]


def test_compatibility_sensitive_path_is_azure_only():
    router, calls = make_router({"azure": 503})
    with pytest.raises(ProviderChainExhausted):
        run(router, compatibility_features={"tools", "previous_response_id"})
    assert [name for name, _ in calls] == ["azure"]


def test_azure_uses_responses_input_and_gemini_preserves_system_instruction(monkeypatch):
    monkeypatch.setenv("AZURE_MIN_OUTPUT_TOKENS", "64")
    router, calls = make_router({"azure": 503})
    assert run(router) == "OK"
    azure_payload = json.loads(calls[0][1].content)
    gemini_payload = json.loads(calls[1][1].content)
    assert "input" in azure_payload and "messages" not in azure_payload
    assert azure_payload["input"][0]["role"] == "system"
    assert gemini_payload["systemInstruction"]["parts"][0]["text"] == "Be concise"
    assert gemini_payload["contents"][0]["role"] == "user"


def test_azure_generator_uses_ordered_router_when_configured(monkeypatch):
    from azure_content_generator import AzureContentGenerator

    class FakeRouter:
        providers = [ProviderConfig("azure", "azure_responses", "gpt-5.6-sol", "https://azure.test", "key")]
        chain_description = "azure/gpt-5.6-sol"

        def __init__(self):
            self.calls = []

        def complete(self, messages, max_tokens, temperature):
            self.calls.append((messages, max_tokens, temperature))
            return "OK"

    fake_router = FakeRouter()
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "azure")
    monkeypatch.setattr(OrderedLLMRouter, "from_env", classmethod(lambda cls, client=None: fake_router))

    generator = AzureContentGenerator(conversation_config={})
    result = generator._call_llm(
        [{"role": "user", "content": "Say OK"}],
        max_tokens=32,
        temperature=0.0,
    )

    assert generator.provider_router is fake_router
    assert result == "OK"
    assert len(fake_router.calls) == 1
    # GPT-5.x reasoning headroom is applied before routing.
    assert fake_router.calls[0][1] == 1000
