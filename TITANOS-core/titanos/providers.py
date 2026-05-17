from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import perf_counter
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config.settings import settings


@dataclass(frozen=True)
class AiProvider:
    key: str
    name: str
    role: str
    default_endpoint: str
    default_model: str
    protocol: str = "openai-compatible"
    requires_key: bool = True
    status: str = "configured"


@dataclass(frozen=True)
class ProviderHealth:
    key: str
    name: str
    endpoint: str
    status: str
    reason: str
    latency_ms: int | None = None


AI_PROVIDERS: tuple[AiProvider, ...] = (
    AiProvider(
        key="openai",
        name="OpenAI",
        role="GPT models and general reasoning",
        default_endpoint="https://api.openai.com/v1",
        default_model="gpt-4.1-mini",
    ),
    AiProvider(
        key="anthropic",
        name="Anthropic",
        role="Claude models and long-context reasoning",
        default_endpoint="https://api.anthropic.com/v1",
        default_model="claude-3-5-sonnet-latest",
        protocol="anthropic",
    ),
    AiProvider(
        key="google",
        name="Google Gemini",
        role="Gemini models and cloud reasoning",
        default_endpoint="https://generativelanguage.googleapis.com/v1beta",
        default_model="gemini-1.5-pro",
        protocol="google",
    ),
    AiProvider(
        key="groq",
        name="Groq",
        role="fast hosted OpenAI-compatible inference",
        default_endpoint="https://api.groq.com/openai/v1",
        default_model="llama-3.1-70b-versatile",
    ),
    AiProvider(
        key="openrouter",
        name="OpenRouter",
        role="router for many commercial and open models",
        default_endpoint="https://openrouter.ai/api/v1",
        default_model="openai/gpt-4o-mini",
    ),
    AiProvider(
        key="mistral",
        name="Mistral AI",
        role="Mistral hosted models",
        default_endpoint="https://api.mistral.ai/v1",
        default_model="mistral-large-latest",
    ),
    AiProvider(
        key="cohere",
        name="Cohere",
        role="Command models and enterprise RAG",
        default_endpoint="https://api.cohere.com/v2",
        default_model="command-r-plus",
        protocol="cohere",
    ),
    AiProvider(
        key="perplexity",
        name="Perplexity",
        role="hosted search-grounded models",
        default_endpoint="https://api.perplexity.ai",
        default_model="sonar-pro",
    ),
    AiProvider(
        key="deepseek",
        name="DeepSeek",
        role="DeepSeek chat and reasoning models",
        default_endpoint="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
    ),
    AiProvider(
        key="xai",
        name="xAI",
        role="Grok models",
        default_endpoint="https://api.x.ai/v1",
        default_model="grok-3-mini",
    ),
    AiProvider(
        key="together",
        name="Together AI",
        role="hosted open-weight models",
        default_endpoint="https://api.together.xyz/v1",
        default_model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    ),
    AiProvider(
        key="fireworks",
        name="Fireworks AI",
        role="fast hosted open-weight models",
        default_endpoint="https://api.fireworks.ai/inference/v1",
        default_model="accounts/fireworks/models/llama-v3p1-70b-instruct",
    ),
    AiProvider(
        key="huggingface",
        name="Hugging Face",
        role="Inference Providers and hosted endpoints",
        default_endpoint="https://router.huggingface.co/v1",
        default_model="meta-llama/Llama-3.1-70B-Instruct",
    ),
    AiProvider(
        key="replicate",
        name="Replicate",
        role="hosted model deployments",
        default_endpoint="https://api.replicate.com/v1",
        default_model="auto",
        protocol="replicate",
    ),
    AiProvider(
        key="azure-openai",
        name="Azure OpenAI",
        role="Azure-hosted OpenAI deployments",
        default_endpoint="",
        default_model="deployment-name",
        protocol="azure-openai",
    ),
    AiProvider(
        key="aws-bedrock",
        name="AWS Bedrock",
        role="AWS-hosted foundation models",
        default_endpoint="",
        default_model="anthropic.claude-3-5-sonnet",
        protocol="bedrock",
    ),
    AiProvider(
        key="vertex-ai",
        name="Google Vertex AI",
        role="Google Cloud Vertex AI model endpoints",
        default_endpoint="",
        default_model="gemini-1.5-pro",
        protocol="vertex-ai",
    ),
    AiProvider(
        key="ollama",
        name="Ollama",
        role="local models and offline inference",
        default_endpoint="http://localhost:11434/api",
        default_model="llama3.1",
        protocol="ollama",
        requires_key=False,
    ),
    AiProvider(
        key="ollama-cloud",
        name="Ollama Cloud",
        role="Ollama cloud-hosted models",
        default_endpoint="https://ollama.com/api",
        default_model="gpt-oss:120b",
        protocol="ollama",
    ),
    AiProvider(
        key="nvidia",
        name="NVIDIA",
        role="NIM endpoints, GPU-backed inference, and local acceleration",
        default_endpoint="https://integrate.api.nvidia.com/v1",
        default_model="meta/llama-3.1-70b-instruct",
    ),
    AiProvider(
        key="custom-openai",
        name="Custom OpenAI-Compatible",
        role="any provider exposing OpenAI-compatible /v1 endpoints",
        default_endpoint="",
        default_model="auto",
    ),
    AiProvider(
        key="custom-ollama",
        name="Custom Ollama-Compatible",
        role="any local or remote Ollama-compatible host",
        default_endpoint="http://localhost:11434/api",
        default_model="llama3.1",
        protocol="ollama",
        requires_key=False,
    ),
)


def provider_report() -> list[str]:
    return [
        f"{provider.name}: {provider.role} ({provider.status}, {provider.default_endpoint})"
        for provider in AI_PROVIDERS
    ]


def provider_presets() -> list[dict[str, object]]:
    return [
        {
            "provider_id": provider.key,
            "label": provider.name,
            "base_url": provider.default_endpoint,
            "default_model": provider.default_model,
            "protocol": provider.protocol,
            "requires_key": provider.requires_key,
            "role": provider.role,
        }
        for provider in AI_PROVIDERS
    ]


def provider_preset(provider_id: str) -> AiProvider | None:
    normalized = provider_id.lower()
    return next((provider for provider in AI_PROVIDERS if provider.key == normalized), None)


def provider_default_model(provider_id: str) -> str:
    preset = provider_preset(provider_id)
    return preset.default_model if preset else "auto"


def provider_default_endpoint(provider_id: str) -> str:
    preset = provider_preset(provider_id)
    return preset.default_endpoint if preset else ""


def configured_model_provider() -> str:
    model_name = settings.TITANOS_MODEL
    if ":" in model_name:
        return model_name.split(":", 1)[0]
    return "custom"


def provider_health(timeout: float = 2.0) -> list[ProviderHealth]:
    with ThreadPoolExecutor(max_workers=min(12, len(AI_PROVIDERS))) as executor:
        futures = {
            executor.submit(_check_provider, provider, timeout=timeout): index
            for index, provider in enumerate(AI_PROVIDERS)
        }
        indexed: list[tuple[int, ProviderHealth]] = []
        for future in as_completed(futures):
            indexed.append((futures[future], future.result()))
    health = [result for _, result in sorted(indexed, key=lambda item: item[0])]
    health.extend(_configured_provider_health(timeout=timeout))
    return health


def provider_health_report(timeout: float = 2.0) -> list[str]:
    return [
        (
            f"{health.name}: {health.status} ({health.reason}, "
            f"{health.endpoint}, {health.latency_ms if health.latency_ms is not None else 'n/a'}ms)"
        )
        for health in provider_health(timeout=timeout)
    ]


def check_saved_provider_config(
    config: dict[str, object],
    *,
    api_key: str | None,
    timeout: float = 5.0,
) -> ProviderHealth:
    provider_id = str(config["provider_id"])
    label = str(config.get("label") or provider_id)
    base_url = str(config.get("base_url") or provider_default_endpoint(provider_id) or "")
    model = str(config.get("model") or provider_default_model(provider_id))
    preset = provider_preset(provider_id)
    protocol = preset.protocol if preset else "openai-compatible"
    requires_key = preset.requires_key if preset else True

    if requires_key and not api_key:
        return ProviderHealth(provider_id, label, base_url, "missing", "API key is required")
    if not base_url:
        return ProviderHealth(provider_id, label, base_url, "needs_config", "Base URL is required")

    endpoint, headers = _auth_probe(provider_id, protocol, base_url, api_key, model)
    start = perf_counter()
    try:
        request = Request(endpoint, headers=headers, method="GET")
        with urlopen(request, timeout=timeout) as response:
            latency_ms = int((perf_counter() - start) * 1000)
            if response.status in {401, 403}:
                return ProviderHealth(provider_id, label, endpoint, "error", f"Auth HTTP {response.status}", latency_ms)
            if response.status < 500:
                return ProviderHealth(provider_id, label, endpoint, "healthy", f"HTTP {response.status}", latency_ms)
            return ProviderHealth(provider_id, label, endpoint, "degraded", f"HTTP {response.status}", latency_ms)
    except HTTPError as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        reason = f"Auth HTTP {exc.code}" if exc.code in {401, 403} else f"HTTP {exc.code}"
        status = "error" if exc.code < 500 else "degraded"
        return ProviderHealth(provider_id, label, endpoint, status, reason, latency_ms)
    except Exception as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return ProviderHealth(provider_id, label, endpoint, "error", exc.__class__.__name__, latency_ms)


def _check_provider(provider: AiProvider, *, timeout: float) -> ProviderHealth:
    endpoint = _configured_endpoint(provider)
    if not endpoint:
        return ProviderHealth(
            provider.key,
            provider.name,
            endpoint,
            "needs_config",
            "Base URL is configured per account or deployment",
            None,
        )
    start = perf_counter()
    try:
        request = Request(endpoint, method="GET")
        with urlopen(request, timeout=timeout) as response:
            latency_ms = int((perf_counter() - start) * 1000)
            if response.status < 500:
                return ProviderHealth(
                    provider.key,
                    provider.name,
                    endpoint,
                    "online",
                    f"HTTP {response.status}",
                    latency_ms,
                )
            return ProviderHealth(
                provider.key,
                provider.name,
                endpoint,
                "degraded",
                f"HTTP {response.status}",
                latency_ms,
            )
    except HTTPError as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        status = "offline" if exc.code in {401, 403, 404} else "degraded"
        reason = f"HTTP {exc.code}"
        return ProviderHealth(provider.key, provider.name, endpoint, status, reason, latency_ms)
    except (OSError, URLError, TimeoutError) as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return ProviderHealth(
            provider.key,
            provider.name,
            endpoint,
            "offline",
            exc.__class__.__name__,
            latency_ms,
        )


def _configured_endpoint(provider: AiProvider) -> str:
    if provider.key == "ollama":
        return f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    if provider.protocol == "ollama" and provider.default_endpoint:
        return f"{provider.default_endpoint.rstrip('/')}/tags"
    if provider.protocol == "openai-compatible" and provider.default_endpoint:
        return f"{provider.default_endpoint.rstrip('/')}/models"
    return provider.default_endpoint


def _configured_provider_health(*, timeout: float) -> list[ProviderHealth]:
    try:
        from . import store
        configs = store.provider_config_list()
    except Exception:
        return []
    static_keys = {provider.key for provider in AI_PROVIDERS}
    results: list[ProviderHealth] = []
    for config in configs:
        provider_id = config["provider_id"]
        if provider_id in static_keys or not config.get("base_url"):
            continue
        start = perf_counter()
        endpoint = _probe_endpoint(provider_id, config["base_url"])
        try:
            request = Request(endpoint, method="GET")
            with urlopen(request, timeout=timeout) as response:
                latency_ms = int((perf_counter() - start) * 1000)
                status = "online" if response.status < 500 else "degraded"
                results.append(
                    ProviderHealth(
                        provider_id,
                        config["label"],
                        endpoint,
                        status,
                        f"HTTP {response.status}",
                        latency_ms,
                    )
                )
        except HTTPError as exc:
            latency_ms = int((perf_counter() - start) * 1000)
            results.append(
                ProviderHealth(
                    provider_id,
                    config["label"],
                    endpoint,
                    "offline" if exc.code in {401, 403, 404} else "degraded",
                    f"HTTP {exc.code}",
                    latency_ms,
                )
            )
        except (OSError, URLError, TimeoutError) as exc:
            latency_ms = int((perf_counter() - start) * 1000)
            results.append(
                ProviderHealth(
                    provider_id,
                    config["label"],
                    endpoint,
                    "offline",
                    exc.__class__.__name__,
                    latency_ms,
                )
            )
    return results


def _probe_endpoint(provider_id: str, base_url: str) -> str:
    base = base_url.rstrip("/")
    preset = provider_preset(provider_id)
    protocol = preset.protocol if preset else "openai-compatible"
    if protocol == "ollama":
        return f"{base}/tags" if base.endswith("/api") else f"{base}/api/tags"
    if protocol == "openai-compatible":
        return f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
    return base


def _auth_probe(
    provider_id: str,
    protocol: str,
    base_url: str,
    api_key: str | None,
    model: str,
) -> tuple[str, dict[str, str]]:
    base = base_url.rstrip("/")
    headers = {"Accept": "application/json"}
    if protocol == "ollama":
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        endpoint = f"{base}/tags" if base.endswith("/api") else f"{base}/api/tags"
        return endpoint, headers
    if protocol == "google":
        query = urlencode({"key": api_key or ""})
        return f"{base}/models?{query}", headers
    if protocol == "anthropic":
        headers["x-api-key"] = api_key or ""
        headers["anthropic-version"] = "2023-06-01"
        return f"{base}/models", headers
    if protocol == "cohere":
        headers["Authorization"] = f"Bearer {api_key or ''}"
        return f"{base}/models", headers
    if protocol in {"azure-openai", "bedrock", "vertex-ai", "replicate"}:
        headers["Authorization"] = f"Bearer {api_key or ''}"
        return base, headers
    headers["Authorization"] = f"Bearer {api_key or ''}"
    endpoint = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
    return endpoint, headers
