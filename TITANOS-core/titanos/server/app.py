import asyncio
import os
import json
import time
import uuid
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Dict, Any
from contextlib import asynccontextmanager
try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:
    Instrumentator = None

from ..config.settings import settings
from ..utils.logging import logger
from ..memory.session import session_manager
from ..defaults import create_titanos
from ..contracts import BodySystem
from ..providers import (
    check_saved_provider_config,
    provider_health as check_provider_health,
    provider_presets,
)
from .. import store as _store

from .auth import get_current_user, require_role
from .jobs import JobManager
from .logging import setup_logging
from .schemas import (
    GoalRequest, 
    RunResponse, 
    ChatResponse, 
    MemoryItem, 
    MemoryCreateRequest, 
    MemoryUpdateRequest, 
    MemoryResponse,
    DoctorResponse,
    ProviderHealthListResponse,
    ProviderHealthResponse,
    CommandClassifyRequest,
    CommandClassifyResponse,
    ApprovalResponse,
    ApprovalListResponse,
    FileWriteRequest,
    FileEditRequest,
    FilePreviewRequest,
    DiffResponse,
    RunRecordResponse,
    RunRecordListResponse,
    RouteExplainRequest,
    RouteExplainResponse,
    BodyHealthResponse,
    BodyHealthListResponse,
    AuditEventResponse,
    AuditEventListResponse,
    BackupFileResponse,
    BackupListResponse,
    BackupRestoreResponse,
    RuntimeDiagnosticsResponse,
    DiagnosticsExportResponse,
    ProviderConfigRequest,
    ProviderConfigResponse,
    ProviderConfigListResponse,
    ProviderPresetListResponse,
    ProviderPresetResponse,
    SessionTouchRequest,
    SessionResponse,
    SessionListResponse,
    WorkspaceRegisterRequest,
    WorkspaceResponse,
    WorkspaceListResponse,
    UsageEventRequest,
    UsageEventResponse,
    UsageSummaryResponse,
    RuntimePolicyResponse,
    JobCreateRequest,
    JobResponse,
    JobListResponse,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    _store.workspace_register(root_path=str(Path.cwd()), label=Path.cwd().name)
    _store.audit_log("server_started", meta={"version": settings.VERSION, "cwd": str(Path.cwd())})
    logger.info("Starting up TITANOS Server...")
    yield
    _store.audit_log("server_stopped", meta={"version": settings.VERSION})
    logger.info("Shutting down TITANOS Server gracefully...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TITANOS Operator API",
    lifespan=lifespan,
)

if Instrumentator is not None:
    Instrumentator().instrument(app).expose(app)

desktop_mode = os.getenv("TITANOS_DESKTOP_MODE") == "1"

# CORS
origins = [origin.strip() for origin in settings.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]
allow_origin_regex = None
if desktop_mode:
    origins = ["http://127.0.0.1", "http://localhost"]
    allow_origin_regex = r"^(file://|null$|http://127\.0\.0\.1:\d+$|http://localhost:\d+$)"
elif settings.ENVIRONMENT == "development" and "*" not in origins:
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-titanos-duration-ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
    return response

# TITANOS Brain instance
brain = create_titanos()
jobs = JobManager()

def memory_adapter():
    adapter = next(
        (body for body in brain.body if body.info.name == BodySystem.MEMORY),
        None,
    )
    if adapter is None:
        raise HTTPException(status_code=503, detail="TITANOS Memory is not available")
    return adapter

def hands_adapter():
    adapter = next(
        (body for body in brain.body if body.info.name == BodySystem.HANDS),
        None,
    )
    if adapter is None:
        raise HTTPException(status_code=503, detail="TITANOS Hands is not available")
    return adapter

def approval_response(row: Dict[str, Any]) -> ApprovalResponse:
    return ApprovalResponse(
        id=row["id"],
        command=row["command"],
        risk=row["risk"],
        reason=row["reason"],
        approved=row["status"] in {"approved", "executed"},
        status=row["status"],
        created_at=row.get("created_at"),
        approved_at=row.get("approved_at"),
        rejected_at=row.get("rejected_at"),
        expires_at=row.get("expires_at"),
        executed_at=row.get("executed_at"),
        execution_count=row.get("execution_count", 0),
        result_summary=row.get("result_summary"),
    )

def provider_config_response(row: Dict[str, Any]) -> ProviderConfigResponse:
    return ProviderConfigResponse(
        provider_id=row["provider_id"],
        label=row["label"],
        base_url=row.get("base_url"),
        model=row.get("model"),
        masked_key=row.get("masked_key"),
        secret_ref=row.get("secret_ref"),
        status=row.get("status", "saved"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )

def session_response(row: Dict[str, Any]) -> SessionResponse:
    return SessionResponse(
        id=row["id"],
        actor=row["actor"],
        mode=row["mode"],
        status=row["status"],
        created_at=row["created_at"],
        last_seen_at=row["last_seen_at"],
        metadata=row.get("metadata") or {},
    )

def workspace_response(row: Dict[str, Any]) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=row["id"],
        label=row["label"],
        root_path=row["root_path"],
        mode=row["mode"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        metadata=row.get("metadata") or {},
    )

def usage_event_response(row: Dict[str, Any]) -> UsageEventResponse:
    return UsageEventResponse(
        id=row["id"],
        provider_id=row["provider_id"],
        model=row.get("model"),
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        estimated_cost=row["estimated_cost"],
        run_id=row.get("run_id"),
        created_at=row["created_at"],
        metadata=row.get("metadata") or {},
    )

def run_response(result, session_id: str | None = None) -> RunResponse:
    return RunResponse(
        system=result.system.value,
        status=result.status,
        summary=result.summary,
        artifacts=result.artifacts,
        next_steps=result.next_steps,
        session_id=brain.session.session_id if brain.session else session_id,
    )

def job_response(row: Dict[str, Any]) -> JobResponse:
    return JobResponse(**row)

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def phantom_connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/")
async def get():
    return {"status": "TITANOS Online", "version": settings.VERSION}

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    return {"status": "ready"}

@app.get("/status")
async def get_status():
    return {
        "identity": "TITANOS",
        "brain": "active",
        "memory": "ready",
        "hands": "ready",
        "cortex": "ready"
    }

@app.get("/runtime")
async def runtime_info():
    meta = _store.runtime_meta()
    return {
        "mode": "desktop" if desktop_mode else "server",
        "host": settings.HOST,
        "port": settings.PORT,
        "data_dir": str(settings.DATA_DIR),
        "log_dir": str(settings.LOG_PATH),
        "runtime_db": str(settings.RUNTIME_DB),
        "schema_version": meta.get("schema_version"),
        "environment": settings.ENVIRONMENT,
        "cors": "desktop-loopback" if desktop_mode else settings.CORS_ALLOW_ORIGINS,
    }

@app.get("/runtime/policy", response_model=RuntimePolicyResponse)
async def runtime_policy(current_user: Dict[str, Any] = Depends(get_current_user)):
    return RuntimePolicyResponse(
        command_timeout_seconds=settings.COMMAND_TIMEOUT_SECONDS,
        approval_expiry_hours=settings.APPROVAL_EXPIRY_HOURS,
        command_allowlist=[
            item.strip() for item in settings.COMMAND_ALLOWLIST.split(",") if item.strip()
        ],
        command_denylist=[
            item.strip() for item in settings.COMMAND_DENYLIST.split(",") if item.strip()
        ],
        protected_path_roots=[".git", ".titanos", "__pycache__"],
        writable_scope="project-root-only",
    )

@app.get("/runtime/diagnostics", response_model=RuntimeDiagnosticsResponse)
async def runtime_diagnostics(current_user: Dict[str, Any] = Depends(get_current_user)):
    return _runtime_diagnostics()

@app.post("/runtime/diagnostics/export", response_model=DiagnosticsExportResponse)
async def export_runtime_diagnostics(current_user: Dict[str, Any] = Depends(get_current_user)):
    bundle = {
        "runtime": _runtime_diagnostics().model_dump(),
        "recent_audit_events": _store.audit_list(limit=100),
        "recent_runs": _store.run_record_list(limit=50),
        "approvals": _store.approval_list(),
        "logs": _log_metadata(),
    }
    redacted = _redact(bundle)
    export_dir = settings.DATA_DIR / "diagnostics"
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"diagnostics-{int(time.time())}.json"
    export_path.write_text(json.dumps(redacted, indent=2), encoding="utf-8")
    return DiagnosticsExportResponse(path=str(export_path), bytes=export_path.stat().st_size)

@app.post("/run", response_model=RunResponse)
async def run_goal(request: GoalRequest, current_user: Dict[str, Any] = Depends(require_role("operator"))):
    result = await asyncio.to_thread(brain.run, request.goal, context=request.context, session_id=request.session_id)
    return run_response(result, request.session_id)

@app.post("/jobs", response_model=JobResponse)
async def create_job(request: JobCreateRequest, current_user: Dict[str, Any] = Depends(require_role("operator"))):
    actor = current_user.get("sub")

    def runner(goal: str, context: List[str]) -> Dict[str, Any]:
        result = brain.run(goal, context=context)
        return run_response(result).model_dump()

    job = jobs.submit(goal=request.goal, context=request.context, runner=runner)
    _store.audit_log("job_created", actor=actor, meta={"job_id": job.id, "goal": request.goal})
    return job_response(job.public())

@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(current_user: Dict[str, Any] = Depends(require_role("operator"))):
    return JobListResponse(jobs=[job_response(job.public()) for job in jobs.list()])

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, current_user: Dict[str, Any] = Depends(require_role("operator"))):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job_response(job.public())

@app.post("/jobs/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str, current_user: Dict[str, Any] = Depends(require_role("operator"))):
    job = jobs.cancel(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    _store.audit_log("job_cancel_requested", actor=current_user.get("sub"), meta={"job_id": job_id})
    return job_response(job.public())

@app.post("/chat", response_model=ChatResponse)
async def chat(request: GoalRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    result = await asyncio.to_thread(brain.run, request.goal, context=request.context, session_id=request.session_id)
    return ChatResponse(
        response=result.summary,
        system=result.system.value,
        status=result.status,
        session_id=brain.session.session_id if brain.session else request.session_id,
    )

@app.get("/sessions", response_model=SessionListResponse)
async def sessions(current_user: Dict[str, Any] = Depends(get_current_user)):
    actor = current_user.get("sub") or current_user.get("username") or "local-operator"
    _store.session_touch(actor=actor, mode=current_user.get("mode", "server"))
    rows = _store.session_list()
    return SessionListResponse(sessions=[session_response(row) for row in rows])

@app.post("/sessions", response_model=SessionResponse)
async def touch_session(
    request: SessionTouchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    actor = current_user.get("sub") or request.actor
    row = _store.session_touch(
        session_id=request.session_id,
        actor=actor,
        mode=request.mode,
        metadata=request.metadata,
    )
    _store.audit_log("session_touched", actor=actor, meta={"session_id": row["id"]})
    return session_response(row)

@app.post("/sessions/{session_id}/close", response_model=SessionResponse)
async def close_session(session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    row = _store.session_close(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    _store.audit_log("session_closed", actor=current_user.get("sub"), meta={"session_id": session_id})
    return session_response(row)

@app.get("/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces(current_user: Dict[str, Any] = Depends(get_current_user)):
    return WorkspaceListResponse(
        workspaces=[workspace_response(row) for row in _store.workspace_list()]
    )

@app.post("/workspaces", response_model=WorkspaceResponse)
async def register_workspace(
    request: WorkspaceRegisterRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    row = _store.workspace_register(
        root_path=request.root_path,
        label=request.label,
        mode=request.mode,
        metadata=request.metadata,
    )
    _store.audit_log(
        "workspace_registered",
        actor=current_user.get("sub"),
        meta={"workspace_id": row["id"], "root_path": row["root_path"]},
    )
    return workspace_response(row)

@app.get("/usage", response_model=UsageSummaryResponse)
async def usage_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UsageSummaryResponse(**_store.usage_summary())

@app.post("/usage/events", response_model=UsageEventResponse)
async def record_usage_event(
    request: UsageEventRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    row = _store.usage_event_record(
        provider_id=request.provider_id,
        model=request.model,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
        estimated_cost=request.estimated_cost,
        run_id=request.run_id,
        metadata=request.metadata,
    )
    _store.audit_log(
        "usage_event_recorded",
        actor=current_user.get("sub"),
        run_id=request.run_id,
        meta={"provider_id": request.provider_id, "model": request.model},
    )
    return usage_event_response(row)

@app.get("/memory", response_model=Dict[str, List[MemoryResponse]])
async def list_memory():
    return {
        "memories": [
            MemoryResponse(
                id=str(record.id),
                content=record.text,
                text=record.text,
                metadata={"kind": record.kind},
                created_at=record.created_at
            )
            for record in memory_adapter().list_records()
        ]
    }

@app.post("/memory", response_model=MemoryResponse)
async def add_memory(item: MemoryCreateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    record = memory_adapter().add_record(item.content, kind=item.metadata.get("kind", "note"))
    return MemoryResponse(
        id=str(record.id),
        content=record.text,
        text=record.text,
        metadata={"kind": record.kind},
        created_at=record.created_at
    )

@app.get("/memory/search", response_model=Dict[str, List[MemoryResponse]])
async def search_memory(q: str = ""):
    return {
        "memories": [
            MemoryResponse(
                id=str(record.id),
                content=record.text,
                text=record.text,
                metadata={"kind": record.kind},
                created_at=record.created_at
            )
            for record in memory_adapter().search_records(q)
        ]
    }

@app.patch("/memory/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: str, item: MemoryUpdateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        mid = int(memory_id.lstrip("#"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID")
    
    if item.content is None:
        raise HTTPException(status_code=400, detail="Content is required for update")
        
    record = memory_adapter().update_record(mid, item.content)
    if record is None:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    return MemoryResponse(
        id=str(record.id),
        content=record.text,
        text=record.text,
        metadata={"kind": record.kind},
        created_at=record.created_at
    )

@app.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        mid = int(memory_id.lstrip("#"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID")
        
    if not memory_adapter().delete_record(mid):
        raise HTTPException(status_code=404, detail="Memory not found")
        
    return {"status": "deleted", "deleted": True, "id": memory_id}

@app.get("/health/providers", response_model=ProviderHealthListResponse)
async def provider_health_endpoint():
    results = await asyncio.to_thread(check_provider_health, timeout=0.75)
    return ProviderHealthListResponse(
        providers=[
            ProviderHealthResponse(
                name=h.name,
                endpoint=h.endpoint,
                status=h.status,
                reason=h.reason,
                latency_ms=float(h.latency_ms) if h.latency_ms is not None else None
            )
            for h in results
        ]
    )

@app.get("/doctor", response_model=DoctorResponse)
async def doctor_report():
    from ..providers import configured_model_provider
    
    warnings = []
    if settings.JWT_SECRET == "super-secret-dev-key":
        warnings.append("Using development JWT secret")
    if settings.CORS_ALLOW_ORIGINS == "*":
        warnings.append("CORS allows all origins")
        
    return DoctorResponse(
        cli="ok",
        version=settings.VERSION,
        data_dir=str(settings.DATA_DIR),
        log_dir=str(settings.LOG_PATH),
        session_dir=str(settings.DATA_DIR / "sessions"),
        memory_db=str(settings.DATA_DIR / "memory.sqlite"),
        body_systems=len(brain.body),
        adapters=[
            f"{entry.system.value}: {entry.status} - {entry.summary}"
            for entry in brain.health_report()
        ],
        os=os.name,
        root=str(Path.cwd()),
        model=settings.TITANOS_MODEL,
        warnings=warnings,
        paths={
            "data": str(settings.DATA_DIR),
            "logs": str(settings.LOG_PATH),
            "memory": str(settings.DATA_DIR / "memory.sqlite"),
            "sessions": str(settings.DATA_DIR / "sessions"),
        },
        providers=[
            health.__dict__
            for health in await asyncio.to_thread(check_provider_health, timeout=0.75)
        ],
    )

@app.get("/hands/approvals", response_model=ApprovalListResponse)
async def list_approvals(current_user: Dict[str, Any] = Depends(get_current_user)):
    rows = _store.approval_list()
    return ApprovalListResponse(
        approvals=[approval_response(r) for r in rows]
    )

@app.get("/hands/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    row = _store.approval_get(approval_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Approval not found: {approval_id}")
    return approval_response(row)

@app.post("/hands/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_command(approval_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    result = hands.approve_command(approval_id)
    if result.status == "failed":
        raise HTTPException(status_code=404, detail=result.summary)
    record = result.raw
    row = _store.approval_get(record.id)
    return approval_response(row) if row else approval_response(record.__dict__)

@app.post("/hands/approvals/{approval_id}/reject", response_model=ApprovalResponse)
async def reject_command(approval_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    result = hands.reject_command(approval_id)
    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.summary)
    row = _store.approval_get(approval_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Approval not found: {approval_id}")
    return approval_response(row)

@app.post("/hands/approvals/{approval_id}/run", response_model=RunResponse)
async def run_approved_command(approval_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    result = hands.run_approved_command(approval_id)
    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.summary)
    return RunResponse(
        system=result.system.value,
        status=result.status,
        summary=result.summary,
        artifacts=result.artifacts,
        session_id=brain.session.session_id if brain.session else None
    )

@app.post("/hands/commands/classify", response_model=CommandClassifyResponse)
async def classify_command(request: CommandClassifyRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    risk, reason = hands.classify_command(request.command)
    return CommandClassifyResponse(risk=risk, reason=reason)

@app.post("/hands/commands/preview", response_model=RunResponse)
async def preview_command(request: CommandClassifyRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    return RunResponse(
        system="Hands",
        status="success",
        summary=f"Dry run preview for: {request.command}",
        artifacts=[],
        session_id=None
    )

@app.post("/hands/files/write-preview", response_model=DiffResponse)
async def write_file_preview(request: FileWriteRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    result = hands.write_file(request.path, request.content, preview=True)
    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.summary)
    return DiffResponse(path=request.path, diff=result.summary)

@app.post("/hands/files/write", response_model=DiffResponse)
async def write_file(request: FileWriteRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    result = hands.write_file(request.path, request.content, preview=False)
    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.summary)
    return DiffResponse(
        path=request.path,
        diff=result.raw.get("diff", ""),
        backup=result.raw.get("backup")
    )

@app.post("/hands/files/edit-preview", response_model=DiffResponse)
async def edit_file_preview(request: FileEditRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    result = hands.edit_file(request.path, request.old_text, request.new_text, preview=True)
    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.summary)
    return DiffResponse(path=request.path, diff=result.summary)

@app.post("/hands/files/edit", response_model=DiffResponse)
async def edit_file(request: FileEditRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    result = hands.edit_file(request.path, request.old_text, request.new_text, preview=False)
    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.summary)
    return DiffResponse(
        path=request.path,
        diff=result.raw.get("diff", ""),
        backup=result.raw.get("backup")
    )

@app.get("/providers/config", response_model=ProviderConfigListResponse)
async def list_provider_configs(current_user: Dict[str, Any] = Depends(get_current_user)):
    return ProviderConfigListResponse(
        providers=[provider_config_response(row) for row in _store.provider_config_list()]
    )

@app.get("/providers/presets", response_model=ProviderPresetListResponse)
async def list_provider_presets(current_user: Dict[str, Any] = Depends(get_current_user)):
    return ProviderPresetListResponse(
        providers=[ProviderPresetResponse(**preset) for preset in provider_presets()]
    )

@app.post("/providers/config", response_model=ProviderConfigResponse)
async def save_provider_config(request: ProviderConfigRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    row = _store.provider_config_save(
        provider_id=request.provider_id,
        label=request.label or request.provider_id.title(),
        base_url=request.base_url,
        model=request.model,
        api_key=request.api_key,
        status=request.status,
    )
    _store.audit_log("provider_config_saved", meta={"provider_id": request.provider_id})
    return provider_config_response(row)

@app.delete("/providers/config/{provider_id}")
async def delete_provider_config(provider_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    deleted = _store.provider_config_delete(provider_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Provider config not found: {provider_id}")
    _store.audit_log("provider_config_deleted", meta={"provider_id": provider_id})
    return {"status": "deleted", "deleted": True, "provider_id": provider_id}

@app.post("/providers/config/{provider_id}/test", response_model=ProviderConfigResponse)
async def test_provider_config(provider_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    row = _store.provider_config_get(provider_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Provider config not found: {provider_id}")
    api_key = _store.provider_secret_reveal(provider_id)
    health = await asyncio.to_thread(check_saved_provider_config, row, api_key=api_key, timeout=5.0)
    provider_status = health.status
    updated = _store.provider_config_save(
        provider_id=row["provider_id"],
        label=row["label"],
        base_url=row.get("base_url"),
        model=row.get("model"),
        status=provider_status,
    )
    _store.audit_log(
        "provider_config_tested",
        meta={"provider_id": provider_id, "status": provider_status, "reason": health.reason},
    )
    return provider_config_response(updated)

@app.get("/hands/backups", response_model=BackupListResponse)
async def list_backups(current_user: Dict[str, Any] = Depends(get_current_user)):
    return BackupListResponse(backups=_backup_records())

@app.get("/hands/backups/{backup_id:path}", response_model=BackupFileResponse)
async def get_backup(backup_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    backup = next((item for item in _backup_records() if item.id == backup_id), None)
    if backup is None:
        raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")
    return backup

@app.post("/hands/backups/{backup_id:path}/restore", response_model=BackupRestoreResponse)
async def restore_backup(backup_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    result = hands_adapter().restore_backup(backup_id)
    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.summary)
    return BackupRestoreResponse(
        status=result.status,
        restored_path=result.raw["restored_path"],
        backup_id=result.raw["backup_id"],
        safety_backup=result.raw.get("safety_backup"),
    )

@app.get("/runs", response_model=RunRecordListResponse)
async def list_runs(current_user: Dict[str, Any] = Depends(get_current_user)):
    rows = _store.run_record_list()
    return RunRecordListResponse(
        runs=[
            RunRecordResponse(
                id=r["id"],
                goal=r["goal"],
                system=r["system"],
                confidence=r["confidence"],
                reason=r["route_reason"],
                status=r["status"],
                duration=float(r["duration_ms"]) / 1000.0,
                artifacts=r["artifacts"],
                created_at=r["created_at"],
                result_summary=r["result_summary"],
                error_summary=r["error_summary"],
            )
            for r in rows
        ]
    )

@app.get("/runs/{run_id}", response_model=RunRecordResponse)
async def get_run(run_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    row = _store.run_record_get(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return RunRecordResponse(
        id=row["id"],
        goal=row["goal"],
        system=row["system"],
        confidence=row["confidence"],
        reason=row["route_reason"],
        status=row["status"],
        duration=float(row["duration_ms"]) / 1000.0,
        artifacts=row["artifacts"],
        created_at=row["created_at"],
        result_summary=row["result_summary"],
        error_summary=row["error_summary"],
    )

@app.get("/audit/events", response_model=AuditEventListResponse)
async def list_audit_events(current_user: Dict[str, Any] = Depends(get_current_user)):
    rows = _store.audit_list()
    return AuditEventListResponse(
        events=[
            AuditEventResponse(
                id=r["id"],
                ts=r["ts"],
                event_type=r["event_type"],
                actor=r["actor"],
                run_id=r["run_id"],
                approval_id=r["approval_id"],
                meta=r["meta"],
            )
            for r in rows
        ]
    )

@app.post("/route/explain", response_model=RouteExplainResponse)
async def explain_route(request: RouteExplainRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    route = brain.explain_route(request.goal)
    return RouteExplainResponse(
        system=route.system.value,
        confidence=route.confidence,
        reason=route.reason
    )

@app.get("/body/health", response_model=BodyHealthListResponse)
async def body_health():
    report = brain.health_report()
    return BodyHealthListResponse(
        systems=[
            BodyHealthResponse(
                system=h.system.value,
                status=h.status,
                summary=h.summary,
                details=h.details or {}
            )
            for h in report
        ]
    )

def _backup_records() -> List[BackupFileResponse]:
    from ..sources import project_root
    root = project_root()
    backup_root = root / ".titanos" / "backups"
    if not backup_root.exists():
        return []
    records: List[BackupFileResponse] = []
    for path in backup_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(backup_root)
            snapshot = relative.parts[0]
            original = Path(*relative.parts[1:]).as_posix()
            stat = path.stat()
        except (ValueError, IndexError):
            continue
        records.append(
            BackupFileResponse(
                id=f"{snapshot}::{original}",
                path=str(relative).replace("\\", "/"),
                original_path=original,
                size=stat.st_size,
                modified_at=str(stat.st_mtime),
            )
        )
    return sorted(records, key=lambda item: item.id, reverse=True)


def _runtime_diagnostics() -> RuntimeDiagnosticsResponse:
    warnings = []
    meta = _store.runtime_meta()
    sessions = _store.session_list()
    workspaces = _store.workspace_list()
    if settings.JWT_SECRET == "super-secret-dev-key":
        warnings.append("Using development JWT secret")
    if settings.CORS_ALLOW_ORIGINS == "*" and not desktop_mode:
        warnings.append("CORS allows all origins")
    try:
        provider_health = [health.__dict__ for health in check_provider_health(timeout=1.0)]
    except Exception as exc:
        provider_health = [{"status": "error", "reason": str(exc)}]
    return RuntimeDiagnosticsResponse(
        mode="desktop" if desktop_mode else "server",
        environment=settings.ENVIRONMENT,
        data_dir=str(settings.DATA_DIR),
        log_dir=str(settings.LOG_PATH),
        runtime_db=str(settings.RUNTIME_DB),
        schema_version=meta.get("schema_version"),
        db_ok=settings.RUNTIME_DB.exists(),
        pending_approvals=len(_store.approval_list(status="pending")),
        recent_audit_events=len(_store.audit_list(limit=100)),
        recent_runs=len(_store.run_record_list(limit=100)),
        active_sessions=len([row for row in sessions if row.get("status") == "active"]),
        registered_workspaces=len(workspaces),
        provider_health=_redact(provider_health),
        warnings=warnings,
        paths={
            "data": str(settings.DATA_DIR),
            "logs": str(settings.LOG_PATH),
            "runtime_db": str(settings.RUNTIME_DB),
            "sessions": str(settings.SESSIONS_PATH),
        },
    )


def _log_metadata() -> List[Dict[str, Any]]:
    if not settings.LOG_PATH.exists():
        return []
    logs = []
    for path in settings.LOG_PATH.glob("*"):
        if path.is_file():
            logs.append({"name": path.name, "bytes": path.stat().st_size})
    return logs


def _redact(value: Any) -> Any:
    secret_markers = ("secret", "token", "api_key", "apikey", "authorization", "password", "key")
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in secret_markers):
                redacted[key] = "[REDACTED]" if item else item
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        for env_name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "NVIDIA_API_KEY", "TITANOS_JWT_SECRET"):
            secret = os.getenv(env_name)
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value
    return value

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.phantom_connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming WS messages
            logger.info(f"WS received: {data}")
            await manager.broadcast({"type": "pulse", "data": "active"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WS Client disconnected")

# Serve UI
UI_DIR = Path(__file__).parent.parent.parent / "ui"
if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
