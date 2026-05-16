from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class GoalRequest(BaseModel):
    goal: str
    session_id: Optional[str] = None
    context: List[str] = []

class RunResponse(BaseModel):
    system: str
    status: str
    summary: str
    artifacts: List[str] = []
    next_steps: List[str] = []
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    system: str
    status: str
    session_id: Optional[str] = None

class MemoryItem(BaseModel):
    id: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = {}

class MemoryCreateRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    id: str
    content: str
    text: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None

class ProviderHealthResponse(BaseModel):
    name: str
    endpoint: str
    status: str
    reason: Optional[str] = None
    latency_ms: Optional[float] = None

class ProviderHealthListResponse(BaseModel):
    providers: List[ProviderHealthResponse]

class DoctorResponse(BaseModel):
    cli: str
    version: str
    data_dir: str
    log_dir: str
    session_dir: str
    memory_db: str
    body_systems: int
    adapters: List[str]
    os: str
    root: str
    model: str
    warnings: List[str] = []
    paths: Dict[str, str] = {}
    providers: List[Dict[str, Any]] = []

class CommandClassifyRequest(BaseModel):
    command: str

class CommandClassifyResponse(BaseModel):
    risk: str
    reason: str

class ApprovalResponse(BaseModel):
    id: str
    command: str
    risk: str
    reason: str
    approved: bool

class ApprovalListResponse(BaseModel):
    approvals: List[ApprovalResponse]

class FileWriteRequest(BaseModel):
    path: str
    content: str

class FileEditRequest(BaseModel):
    path: str
    old_text: str
    new_text: str

class FilePreviewRequest(BaseModel):
    path: str
    content: Optional[str] = None
    old_text: Optional[str] = None
    new_text: Optional[str] = None

class DiffResponse(BaseModel):
    path: str
    diff: str
    backup: Optional[str] = None

class RunRecordResponse(BaseModel):
    id: str
    goal: str
    system: str
    confidence: float
    reason: str
    status: str
    duration: float
    artifacts: List[str]

class RunRecordListResponse(BaseModel):
    runs: List[RunRecordResponse]

class RouteExplainRequest(BaseModel):
    goal: str

class RouteExplainResponse(BaseModel):
    system: str
    confidence: float
    reason: str

class BodyHealthResponse(BaseModel):
    system: str
    status: str
    summary: str
    details: Dict[str, Any] = {}

class BodyHealthListResponse(BaseModel):
    systems: List[BodyHealthResponse]
