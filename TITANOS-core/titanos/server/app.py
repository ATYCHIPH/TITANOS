import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
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
from ..providers import provider_health as check_provider_health

from .auth import get_current_user
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
    BodyHealthListResponse
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting up TITANOS Server...")
    yield
    logger.info("Shutting down TITANOS Server gracefully...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TITANOS Operator API",
    lifespan=lifespan,
)

if Instrumentator is not None:
    Instrumentator().instrument(app).expose(app)

# CORS
origins = settings.CORS_ALLOW_ORIGINS.split(",")
if settings.ENVIRONMENT == "development" and "*" not in origins:
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TITANOS Brain instance
brain = create_titanos()

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

@app.post("/run", response_model=RunResponse)
async def run_goal(request: GoalRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    result = brain.run(request.goal, context=request.context)
    return RunResponse(
        system=result.system.value,
        status=result.status,
        summary=result.summary,
        artifacts=result.artifacts,
        next_steps=result.next_steps,
        session_id=brain.session.session_id if brain.session else request.session_id,
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: GoalRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    result = brain.run(request.goal, context=request.context)
    return ChatResponse(
        response=result.summary,
        system=result.system.value,
        status=result.status,
        session_id=brain.session.session_id if brain.session else request.session_id,
    )

@app.get("/sessions")
async def sessions():
    return {"sessions": session_manager.list_sessions()}

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
    results = check_provider_health()
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
        providers=[health.__dict__ for health in check_provider_health()],
    )

@app.get("/hands/approvals", response_model=ApprovalListResponse)
async def list_approvals(current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    return ApprovalListResponse(
        approvals=[
            ApprovalResponse(
                id=a.id,
                command=a.command,
                risk=a.risk,
                reason=a.reason,
                approved=a.approved
            )
            for a in hands.approvals.values()
        ]
    )

@app.post("/hands/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_command(approval_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    hands = hands_adapter()
    result = hands.approve_command(approval_id)
    if result.status == "failed":
        raise HTTPException(status_code=404, detail=result.summary)
    record = result.raw
    return ApprovalResponse(
        id=record.id,
        command=record.command,
        risk=record.risk,
        reason=record.reason,
        approved=record.approved
    )

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

@app.get("/hands/backups")
async def list_backups(current_user: Dict[str, Any] = Depends(get_current_user)):
    from ..sources import project_root
    backup_root = project_root() / ".titanos" / "backups"
    if not backup_root.exists():
        return {"backups": []}
    
    backups = []
    for p in backup_root.rglob("*"):
        if p.is_file():
            backups.append({
                "id": p.parent.name,
                "path": str(p.relative_to(backup_root)),
                "full_path": str(p)
            })
    return {"backups": backups}

@app.get("/runs", response_model=RunRecordListResponse)
async def list_runs(current_user: Dict[str, Any] = Depends(get_current_user)):
    return RunRecordListResponse(
        runs=[
            RunRecordResponse(
                id=str(i),
                goal=r.goal,
                system=r.route.system.value,
                confidence=r.route.confidence,
                reason=r.route.reason,
                status=r.status,
                duration=float(r.duration_ms) / 1000.0,
                artifacts=r.artifacts
            )
            for i, r in enumerate(brain.run_records)
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
