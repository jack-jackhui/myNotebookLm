"""Centralized ordered LLM provider failover for text generation.

The router performs one bounded attempt per provider. It only advances for
transient/network/rate-limit failures; invalid requests, authentication and
configuration errors stop immediately. Prompt and response bodies are never
logged.
"""

from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
COMPATIBILITY_FEATURES = {"streaming", "structured_output", "tools", "citations", "previous_response_id"}


class ProviderRequestError(RuntimeError):
    """A sanitized provider failure safe to log."""

    def __init__(self, provider: str, model: str, reason: str, retryable: bool):
        super().__init__(f"{provider}/{model}: {reason}")
        self.provider = provider
        self.model = model
        self.reason = reason
        self.retryable = retryable


class ProviderChainExhausted(RuntimeError):
    """All eligible providers failed with retryable errors."""


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    kind: str
    model: str
    endpoint: str
    api_key: str
    account_id: Optional[str] = None


class OrderedLLMRouter:
    """Route simple non-streaming message requests through an ordered chain."""

    def __init__(
        self,
        providers: Sequence[ProviderConfig],
        timeout_seconds: float = 120.0,
        client: Optional[httpx.Client] = None,
    ):
        if not providers:
            raise ValueError("At least one LLM provider is required")
        self.providers = list(providers)
        self.timeout_seconds = timeout_seconds
        self.client = client or httpx.Client(timeout=timeout_seconds)

    @staticmethod
    def _secret(file_env: str, value_env: str) -> str:
        file_name = os.getenv(file_env)
        if file_name:
            path = Path(file_name)
            value = path.read_text(encoding="utf-8").strip()
        else:
            value = os.getenv(value_env, "").strip()
        if not value:
            raise ValueError(f"Missing credential configured by {file_env} or {value_env}")
        return value

    @staticmethod
    def _value_from_file(file_env: str, value_env: str) -> str:
        file_name = os.getenv(file_env)
        value = Path(file_name).read_text(encoding="utf-8").strip() if file_name else os.getenv(value_env, "").strip()
        if not value:
            raise ValueError(f"Missing configuration configured by {file_env} or {value_env}")
        return value

    @classmethod
    def from_env(cls, client: Optional[httpx.Client] = None) -> "OrderedLLMRouter":
        available: Dict[str, ProviderConfig] = {
            "azure": ProviderConfig(
                name="azure",
                kind="azure_responses",
                model=os.getenv("AZURE_RESPONSES_MODEL", "gpt-5.6-sol"),
                endpoint=os.getenv(
                    "AZURE_RESPONSES_ENDPOINT",
                    "https://jack-m2x0qyej-northcentralus.openai.azure.com/openai/responses?api-version=2025-04-01-preview",
                ),
                api_key=cls._secret("AZURE_RESPONSES_API_KEY_FILE", "AZURE_RESPONSES_API_KEY"),
            ),
            "gemini": ProviderConfig(
                name="gemini",
                kind="gemini_native",
                model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
                endpoint=os.getenv("GEMINI_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta"),
                api_key=cls._secret("GEMINI_API_KEY_FILE", "GEMINI_API_KEY"),
            ),
            "cloudflare": ProviderConfig(
                name="cloudflare",
                kind="cloudflare_workers",
                model=os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
                endpoint=os.getenv("CLOUDFLARE_ENDPOINT", "https://api.cloudflare.com/client/v4"),
                api_key=cls._secret("CLOUDFLARE_API_TOKEN_FILE", "CLOUDFLARE_API_TOKEN"),
                account_id=cls._value_from_file("CLOUDFLARE_ACCOUNT_ID_FILE", "CLOUDFLARE_ACCOUNT_ID"),
            ),
            "openrouter_ultra": ProviderConfig(
                name="openrouter_ultra",
                kind="openai_compatible",
                model=os.getenv("OPENROUTER_ULTRA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free"),
                endpoint=os.getenv("OPENROUTER_ENDPOINT", "https://openrouter.ai/api/v1"),
                api_key=cls._secret("OPENROUTER_API_KEY_FILE", "OPENROUTER_API_KEY"),
            ),
            "openrouter_super": ProviderConfig(
                name="openrouter_super",
                kind="openai_compatible",
                model=os.getenv("OPENROUTER_SUPER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free"),
                endpoint=os.getenv("OPENROUTER_ENDPOINT", "https://openrouter.ai/api/v1"),
                api_key=cls._secret("OPENROUTER_API_KEY_FILE", "OPENROUTER_API_KEY"),
            ),
        }
        names = [x.strip() for x in os.getenv(
            "LLM_PROVIDER_ORDER", "azure,gemini,cloudflare,openrouter_ultra,openrouter_super"
        ).split(",") if x.strip()]
        unknown = [name for name in names if name not in available]
        if unknown:
            raise ValueError(f"Unknown LLM providers in LLM_PROVIDER_ORDER: {', '.join(unknown)}")
        return cls(
            [available[name] for name in names],
            timeout_seconds=float(os.getenv("LLM_PROVIDER_TIMEOUT_SECONDS", "120")),
            client=client,
        )

    @property
    def chain_description(self) -> str:
        return " -> ".join(f"{p.name}/{p.model}" for p in self.providers)

    def complete(
        self,
        messages: List[dict],
        max_tokens: int,
        temperature: float = 0.7,
        compatibility_features: Optional[Iterable[str]] = None,
    ) -> str:
        features: Set[str] = set(compatibility_features or ())
        unknown_features = features - COMPATIBILITY_FEATURES
        if unknown_features:
            raise ValueError(f"Unknown compatibility features: {', '.join(sorted(unknown_features))}")

        # Non-Azure adapters intentionally cover the app's current simple text path.
        # Requests needing richer semantics stay on Azure rather than silently losing them.
        providers = self.providers[:1] if features else self.providers
        errors: List[str] = []
        for provider in providers:
            logger.info("LLM attempt provider=%s model=%s", provider.name, provider.model)
            try:
                text = self._complete_one(provider, messages, max_tokens, temperature)
                logger.info("LLM success provider=%s model=%s", provider.name, provider.model)
                return text
            except ProviderRequestError as exc:
                logger.warning(
                    "LLM failure provider=%s model=%s reason=%s retryable=%s",
                    provider.name, provider.model, exc.reason, exc.retryable,
                )
                if not exc.retryable:
                    raise
                errors.append(f"{provider.name}/{provider.model}: {exc.reason}")

        raise ProviderChainExhausted("LLM provider chain exhausted: " + "; ".join(errors))

    def _complete_one(self, provider: ProviderConfig, messages: List[dict], max_tokens: int, temperature: float) -> str:
        if provider.kind == "azure_responses":
            url = provider.endpoint
            headers = {"Authorization": f"Bearer {provider.api_key}"}
            payload = {
                "model": provider.model,
                "input": messages,
                "max_output_tokens": max(max_tokens, int(os.getenv("AZURE_MIN_OUTPUT_TOKENS", "16384"))),
            }
        elif provider.kind == "gemini_native":
            url = f"{provider.endpoint.rstrip('/')}/models/{provider.model}:generateContent"
            headers = {"x-goog-api-key": provider.api_key}
            system_text = "\n\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "system")
            contents = []
            for message in messages:
                if message.get("role") == "system":
                    continue
                role = "model" if message.get("role") == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": str(message.get("content", ""))}]})
            payload = {
                "contents": contents,
                "generationConfig": {"maxOutputTokens": min(max_tokens, 65536), "temperature": temperature},
            }
            if system_text:
                payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        elif provider.kind == "cloudflare_workers":
            url = f"{provider.endpoint.rstrip('/')}/accounts/{provider.account_id}/ai/run/{provider.model}"
            headers = {"Authorization": f"Bearer {provider.api_key}"}
            payload = {"messages": messages, "max_tokens": min(max_tokens, 8192), "temperature": temperature}
        elif provider.kind == "openai_compatible":
            url = f"{provider.endpoint.rstrip('/')}/chat/completions"
            headers = {"Authorization": f"Bearer {provider.api_key}"}
            payload = {"model": provider.model, "messages": messages, "max_tokens": min(max_tokens, 8192), "temperature": temperature}
        else:
            raise ProviderRequestError(provider.name, provider.model, "unsupported provider kind", retryable=False)

        try:
            response = self.client.post(url, headers={"Content-Type": "application/json", **headers}, json=payload, timeout=self.timeout_seconds)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderRequestError(provider.name, provider.model, type(exc).__name__, retryable=True) from None

        if response.status_code >= 400:
            reason = f"HTTP {response.status_code}"
            raise ProviderRequestError(
                provider.name, provider.model, reason,
                retryable=response.status_code in RETRYABLE_STATUS_CODES,
            )

        try:
            data = response.json()
            if provider.kind == "azure_responses":
                text = self._azure_text(data)
            elif provider.kind == "gemini_native":
                text = "".join(
                    part.get("text", "")
                    for part in data["candidates"][0]["content"]["parts"]
                    if isinstance(part, dict)
                )
            elif provider.kind == "cloudflare_workers":
                result = data.get("result") or {}
                text = result.get("response", "")
                if not text and result.get("choices"):
                    text = result["choices"][0]["message"]["content"]
            else:
                text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderRequestError(provider.name, provider.model, "invalid response schema", retryable=True) from None

        if not isinstance(text, str) or not text.strip():
            raise ProviderRequestError(provider.name, provider.model, "empty response", retryable=True)
        return text.strip()

    @staticmethod
    def _azure_text(data: dict) -> str:
        if isinstance(data.get("output_text"), str) and data["output_text"].strip():
            return data["output_text"]
        chunks: List[str] = []
        for item in data.get("output", []):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                    chunks.append(content.get("text", ""))
        return "".join(chunks)
