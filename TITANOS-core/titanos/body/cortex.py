import os
import re
import urllib.error
import urllib.request
from typing import Any

from dotenv import load_dotenv

from ..config.settings import settings
from ..contracts import BodyHealth, BodyResult, BodySystem, BodyTask, ChatMessage
from ..utils.logging import get_logger
from .base import info

# Load environment variables from .env
load_dotenv()
logger = get_logger(__name__)


class CortexAdapter:
    """The central reasoning engine for TITANOS."""

    info = info(
        BodySystem.CORTEX,
        "TITANOS Cortex",
        "pydantic-ai graft",
        "master reasoning engine, tool orchestration, goal decomposition",
        always_on=True,
    )

    def __init__(self, model_name: str | None = None, tools: list[Any] | None = None) -> None:
        self.model_name = model_name or settings.TITANOS_MODEL
        self._agent: Any | None = None
        self._body_tools = tools or []

    def register_tools(self, tools: list[Any]) -> None:
        """Register other body systems as tools for the Cortex."""
        self._body_tools = tools

    def initialize(self) -> None:
        return None

    def health(self) -> BodyHealth:
        provider_error = self._provider_error()
        return BodyHealth(
            system=BodySystem.CORTEX,
            status="degraded" if provider_error else "ready",
            summary=provider_error or "Cortex provider is reachable.",
            details={"model": self.model_name},
        )

    def shutdown(self) -> None:
        return None

    def _get_agent(self) -> Agent[Any, str]:
        from pydantic_ai import Agent
        from pydantic_ai.models.ollama import OllamaModel
        from pydantic_ai.providers.ollama import OllamaProvider

        if self._agent is None:
            if self.model_name.startswith("ollama:"):
                base_url = settings.OLLAMA_BASE_URL
                api_key = settings.OLLAMA_API_KEY
                
                provider = OllamaProvider(base_url=base_url, api_key=api_key)
                model = OllamaModel(
                    self.model_name.replace("ollama:", ""),
                    provider=provider
                )
            else:
                model = self.model_name

            self._agent = Agent(
                model,
                system_prompt=(
                    "You are the TITANOS Cortex, the central reasoning engine of an agentic system. "
                    "You have access to a body of systems (Hands, Memory, Eyes, etc.). "
                    "Decompose goals and call the appropriate tools."
                ),
            )
            # Register tools
            for tool in self._body_tools:
                # We use a trick to bind the tool instance to the function scope properly
                def create_tool_func(t):
                    def titanos_tool(goal: str) -> str:
                        """Call a TITANOS body system."""
                        res = t.run(BodyTask(goal=goal))
                        return f"[{res.system.value}] {res.summary}"
                    
                    tool_name = re.sub(r"[^a-zA-Z0-9_]+", "_", t.info.public_name).strip("_")
                    titanos_tool.__name__ = tool_name.lower() or t.info.name.value
                    titanos_tool.__doc__ = t.info.purpose
                    return titanos_tool

                self._agent.tool_plain(create_tool_func(tool))

        return self._agent

    def run(self, task: BodyTask) -> BodyResult:
        provider_error = self._provider_error()
        if provider_error:
            return BodyResult(
                system=BodySystem.CORTEX,
                status="needs_input",
                summary=provider_error,
                next_steps=[
                    "Start the configured model provider or choose a direct body command.",
                    "Use 'python -m titanos doctor' to inspect local runtime health.",
                ],
            )

        agent = self._get_agent()
        
        # Convert history to pydantic-ai format if needed
        # (Simplified for now)
        try:
            result = agent.run_sync(task.goal)
            return BodyResult(
                system=BodySystem.CORTEX,
                status="success",
                summary=result.data,
                next_steps=[],
            )
        except Exception as e:
            logger.exception("Cortex reasoning failed")
            return BodyResult(
                system=BodySystem.CORTEX,
                status="error",
                summary=f"Cortex reasoning failed: {str(e)}",
                next_steps=["Check your AI provider connection and .env settings."],
            )

    def _provider_error(self) -> str | None:
        if not self.model_name.startswith("ollama:"):
            return None
        try:
            with urllib.request.urlopen(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags",
                timeout=2,
            ) as response:
                if response.status < 400:
                    return None
        except (urllib.error.URLError, TimeoutError, OSError):
            return (
                "Cortex model provider is offline or unreachable: "
                f"{settings.OLLAMA_BASE_URL}"
            )
        return f"Cortex model provider returned an unhealthy response: {settings.OLLAMA_BASE_URL}"
