from __future__ import annotations

import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable


@dataclass
class JobRecord:
    id: str
    goal: str
    context: list[str]
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    cancel_requested: bool = False
    result: dict[str, Any] | None = None
    error: str | None = None
    future: Future | None = field(default=None, repr=False)

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "cancel_requested": self.cancel_requested,
            "result": self.result,
            "error": self.error,
        }


class JobManager:
    def __init__(self, *, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="titanos-job")
        self._lock = threading.Lock()
        self._jobs: dict[str, JobRecord] = {}

    def submit(
        self,
        *,
        goal: str,
        context: list[str],
        runner: Callable[[str, list[str]], dict[str, Any]],
    ) -> JobRecord:
        job = JobRecord(
            id=uuid.uuid4().hex,
            goal=goal,
            context=context,
            status="queued",
            created_at=_now(),
        )
        with self._lock:
            self._jobs[job.id] = job
        future = self._executor.submit(self._run_job, job.id, runner)
        with self._lock:
            job.future = future
        return job

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[JobRecord]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    def cancel(self, job_id: str) -> JobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.cancel_requested = True
            if job.status == "queued" and job.future and job.future.cancel():
                job.status = "cancelled"
                job.completed_at = _now()
            elif job.status in {"queued", "running"}:
                job.status = "cancelling"
            return job

    def _run_job(self, job_id: str, runner: Callable[[str, list[str]], dict[str, Any]]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            if job.cancel_requested:
                job.status = "cancelled"
                job.completed_at = _now()
                return
            job.status = "running"
            job.started_at = _now()
        try:
            result = runner(job.goal, job.context)
            with self._lock:
                job = self._jobs[job_id]
                job.result = result
                job.status = "cancelled" if job.cancel_requested else "completed"
                job.completed_at = _now()
        except Exception as exc:
            with self._lock:
                job = self._jobs[job_id]
                job.error = str(exc)
                job.status = "failed"
                job.completed_at = _now()


def _now() -> str:
    return datetime.now(UTC).isoformat()
