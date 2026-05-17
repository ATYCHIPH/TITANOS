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
    status: str = "pending"
    created_at: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    expires_at: Optional[str] = None
    executed_at: Optional[str] = None
    execution_count: int = 0
    result_summary: Optional[str] = None

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
    created_at: Optional[str] = None
    result_summary: Optional[str] = None
    error_summary: Optional[str] = None

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

class AuditEventResponse(BaseModel):
    id: str
    ts: str
    event_type: str
    actor: Optional[str] = None
    run_id: Optional[str] = None
    approval_id: Optional[str] = None
    meta: Dict[str, Any] = {}

class AuditEventListResponse(BaseModel):
    events: List[AuditEventResponse]

class BackupFileResponse(BaseModel):
    id: str
    path: str
    original_path: str
    size: int
    modified_at: Optional[str] = None

class BackupListResponse(BaseModel):
    backups: List[BackupFileResponse]

class BackupRestoreResponse(BaseModel):
    status: str
    restored_path: str
    backup_id: str
    safety_backup: Optional[str] = None

class RuntimeDiagnosticsResponse(BaseModel):
    mode: str
    environment: str
    data_dir: str
    log_dir: str
    runtime_db: str
    schema_version: Optional[str] = None
    db_ok: bool
    pending_approvals: int
    recent_audit_events: int
    recent_runs: int
    active_sessions: int = 0
    registered_workspaces: int = 0
    provider_health: List[Dict[str, Any]] = []
    warnings: List[str] = []
    paths: Dict[str, str] = {}

class DiagnosticsExportResponse(BaseModel):
    path: str
    bytes: int
    redacted: bool = True

class ProviderConfigRequest(BaseModel):
    provider_id: str
    label: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    status: str = "saved"

class ProviderConfigResponse(BaseModel):
    provider_id: str
    label: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    masked_key: Optional[str] = None
    secret_ref: Optional[str] = None
    status: str = "saved"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ProviderConfigListResponse(BaseModel):
    providers: List[ProviderConfigResponse]

class ProviderPresetResponse(BaseModel):
    provider_id: str
    label: str
    base_url: str
    default_model: str
    protocol: str
    requires_key: bool
    role: str

class ProviderPresetListResponse(BaseModel):
    providers: List[ProviderPresetResponse]

class SessionTouchRequest(BaseModel):
    session_id: Optional[str] = None
    actor: str = "local-operator"
    mode: str = "desktop"
    metadata: Dict[str, Any] = {}

class SessionResponse(BaseModel):
    id: str
    actor: str
    mode: str
    status: str
    created_at: str
    last_seen_at: str
    metadata: Dict[str, Any] = {}

class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]

class WorkspaceRegisterRequest(BaseModel):
    root_path: str
    label: Optional[str] = None
    mode: str = "local"
    metadata: Dict[str, Any] = {}

class WorkspaceResponse(BaseModel):
    id: str
    label: str
    root_path: str
    mode: str
    status: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = {}

class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceResponse]

class UsageEventRequest(BaseModel):
    provider_id: str
    model: Optional[str] = None
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0.0, ge=0)
    run_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class UsageEventResponse(BaseModel):
    id: str
    provider_id: str
    model: Optional[str] = None
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    run_id: Optional[str] = None
    created_at: str
    metadata: Dict[str, Any] = {}

class UsageSummaryResponse(BaseModel):
    providers: List[Dict[str, Any]]
    total_events: int
    total_input_tokens: int
    total_output_tokens: int
    total_estimated_cost: float

class RuntimePolicyResponse(BaseModel):
    command_timeout_seconds: int
    approval_expiry_hours: int
    command_allowlist: List[str]
    command_denylist: List[str]
    protected_path_roots: List[str]
    writable_scope: str

class JobCreateRequest(BaseModel):
    goal: str
    context: List[str] = []

class JobResponse(BaseModel):
    id: str
    goal: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancel_requested: bool = False
    result: Optional[RunResponse] = None
    error: Optional[str] = None

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
