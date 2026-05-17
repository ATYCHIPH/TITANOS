from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from .contracts import (
    BodyAdapter,
    BodyHealth,
    BodyResult,
    BodySystem,
    BodyTask,
    ChatMessage,
    RouteDecision,
    RunRecord,
)
from .config.settings import settings
from .memory.policy import MemoryWritePolicy
from .memory.session import Session, session_manager
from .utils.logging import get_logger
from . import store as _store


logger = get_logger(__name__)


@dataclass
class TitanosBrain:
    """The single public agent identity.

    TITANOS owns intent, routing, verification, and final synthesis. Body
    systems are internal capabilities, not user-facing agent personas.
    """

    body: list[BodyAdapter] = field(default_factory=list)
    session: Session | None = None
    memory_policy: MemoryWritePolicy = field(default_factory=MemoryWritePolicy)
    run_records: list[RunRecord] = field(default_factory=list)

    def attach(self, adapter: BodyAdapter) -> None:
        self.body.append(adapter)

    def initialize(self) -> None:
        for adapter in self.body:
            initialize = getattr(adapter, "initialize", None)
            if initialize:
                initialize()

    def shutdown(self) -> None:
        for adapter in reversed(self.body):
            shutdown = getattr(adapter, "shutdown", None)
            if shutdown:
                shutdown()

    def health_report(self) -> list[BodyHealth]:
        report: list[BodyHealth] = []
        for adapter in self.body:
            health = getattr(adapter, "health", None)
            if health:
                try:
                    report.append(health())
                except Exception as exc:
                    report.append(
                        BodyHealth(
                            system=adapter.info.name,
                            status="error",
                            summary=f"Health check failed: {exc}",
                        )
                    )
            else:
                report.append(
                    BodyHealth(
                        system=adapter.info.name,
                        status="unknown",
                        summary="Adapter does not expose health.",
                    )
                )
        return report

    def run(
        self,
        goal: str,
        *,
        context: list[str] | None = None,
        session_id: str | None = None,
    ) -> BodyResult:
        started = perf_counter()
        if settings.SESSION_HISTORY_ENABLED and self.session is None:
            self.session = session_manager.get_session(session_id) if session_id else session_manager.create_session()
        elif settings.SESSION_HISTORY_ENABLED and session_id and self.session and self.session.session_id != session_id:
            self.session = session_manager.get_session(session_id)
        history = self._history_messages()
        if self.session:
            self.session.add_interaction("user", goal)

        task = BodyTask(goal=goal, context=context or [], history=history)
        adapter, route = self._route(task)
        logger.info(
            "Routing goal",
            extra={
                "extra": {
                    "system": adapter.info.name.value,
                    "goal": goal,
                    "confidence": route.confidence,
                    "reason": route.reason,
                }
            },
        )
        result = adapter.run(task)
        result = self._synthesize(result)
        duration_ms = int((perf_counter() - started) * 1000)
        # Persist to durable store
        _store.run_record_create(
            goal=goal,
            system=route.system.value,
            confidence=route.confidence,
            route_reason=route.reason,
            status=result.status,
            duration_ms=duration_ms,
            result_summary=result.summary,
            error_summary=result.summary if result.status == "failed" else None,
            artifacts=result.artifacts,
        )
        # Keep in-memory list for backward-compat (current-process reads)
        in_mem = RunRecord(
            goal=goal,
            route=route,
            status=result.status,
            summary=result.summary,
            duration_ms=duration_ms,
            artifacts=result.artifacts,
        )
        self.run_records.append(in_mem)
        if self.session:
            self.session.add_interaction(
                "titanos",
                result.summary,
                {
                    "system": result.system.value,
                    "status": result.status,
                    "artifacts": result.artifacts,
                    "route": {
                        "system": route.system.value,
                        "confidence": route.confidence,
                        "reason": route.reason,
                    },
                    "duration_ms": duration_ms,
                },
            )
        self._capture_memory_candidates(result)
        return result

    def _route(self, task: BodyTask) -> tuple[BodyAdapter, RouteDecision]:
        candidates: list[tuple[float, BodyAdapter, str]] = []
        for adapter in self.body:
            if adapter.info.name != BodySystem.CORTEX and adapter.can_handle(task):
                candidates.append((0.9, adapter, "direct body-system intent match"))

        if candidates:
            confidence, adapter, reason = max(
                candidates,
                key=lambda candidate: (candidate[0], -self.body.index(candidate[1])),
            )
            route = RouteDecision(adapter.info.name, confidence, reason)
            _store.audit_log(
                "route_decision_made",
                meta={"system": route.system.value, "confidence": route.confidence, "reason": route.reason},
            )
            return adapter, route

        cortex = next(
            (adapter for adapter in self.body if adapter.info.name == BodySystem.CORTEX),
            None,
        )
        if cortex:
            route = RouteDecision(
                BodySystem.CORTEX,
                0.4,
                "no direct body match; using Cortex fallback",
            )
            _store.audit_log(
                "route_decision_made",
                meta={"system": route.system.value, "confidence": route.confidence, "reason": route.reason},
            )
            return cortex, route

        raise RuntimeError(f"No TITANOS body system can handle: {task.goal}")

    def explain_route(self, goal: str) -> RouteDecision:
        task = BodyTask(goal=goal, history=self._history_messages())
        _, route = self._route(task)
        return route

    def _history_messages(self) -> list[ChatMessage]:
        if not self.session:
            return []
        messages: list[ChatMessage] = []
        for entry in self.session.history[-20:]:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            if role == "titanos":
                role = "assistant"
            if content:
                messages.append(ChatMessage(role=role, content=content))
        return messages

    def _synthesize(self, result: BodyResult) -> BodyResult:
        if result.status not in {"success", "failed", "needs_input", "error"}:
            return BodyResult(
                system=BodySystem.CORTEX,
                status="failed",
                summary=f"Body system returned invalid status: {result.status}",
                raw=result,
            )
        return result

    def _capture_memory_candidates(self, result: BodyResult) -> None:
        if result.status != "success" or result.system == BodySystem.MEMORY:
            return
        memory = next(
            (adapter for adapter in self.body if adapter.info.name == BodySystem.MEMORY),
            None,
        )
        if memory is None or not result.memory_candidates:
            return
        for candidate in result.memory_candidates:
            decision = self.memory_policy.evaluate(candidate)
            if not decision.accepted:
                logger.info(
                    "Memory candidate rejected",
                    extra={"extra": {"reason": decision.reason}},
                )
                continue
            memory.run(BodyTask(goal=f"remember {decision.text}"))
