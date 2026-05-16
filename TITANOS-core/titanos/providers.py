from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from urllib.error import URLError
from urllib.request import Request, urlopen

from .config.settings import settings


@dataclass(frozen=True)
class AiProvider:
    key: str
    name: str
    role: str
    default_endpoint: str
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
        key="ollama",
        name="Ollama",
        role="local models and offline inference",
        default_endpoint="http://localhost:11434",
    ),
    AiProvider(
        key="google",
        name="Google",
        role="Gemini models and cloud reasoning",
        default_endpoint="https://generativelanguage.googleapis.com",
    ),
    AiProvider(
        key="nvidia",
        name="NVIDIA",
        role="NIM endpoints, GPU-backed inference, and local acceleration",
        default_endpoint="https://integrate.api.nvidia.com",
    ),
)


def provider_report() -> list[str]:
    return [
        f"{provider.name}: {provider.role} ({provider.status}, {provider.default_endpoint})"
        for provider in AI_PROVIDERS
    ]


def configured_model_provider() -> str:
    model_name = settings.TITANOS_MODEL
    if ":" in model_name:
        return model_name.split(":", 1)[0]
    return "custom"


def provider_health(timeout: float = 2.0) -> list[ProviderHealth]:
    return [_check_provider(provider, timeout=timeout) for provider in AI_PROVIDERS]


def provider_health_report(timeout: float = 2.0) -> list[str]:
    return [
        (
            f"{health.name}: {health.status} ({health.reason}, "
            f"{health.endpoint}, {health.latency_ms if health.latency_ms is not None else 'n/a'}ms)"
        )
        for health in provider_health(timeout=timeout)
    ]


def _check_provider(provider: AiProvider, *, timeout: float) -> ProviderHealth:
    endpoint = _configured_endpoint(provider)
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
    return provider.default_endpoint
