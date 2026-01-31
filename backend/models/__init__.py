from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    ACTIVE = "active"
    BUSY = "busy"
    INACTIVE = "inactive"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageType(str, Enum):
    TASK = "task"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    BUG = "bug"


class AgentCreate(BaseModel):
    agent_id: str
    name: str
    role: str


class AgentResponse(BaseModel):
    id: int
    agent_id: str
    name: str
    role: str
    status: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    task_id: str
    title: str
    description: str
    priority: int = 0
    code_content: Optional[str] = None
    target_files: Optional[str] = None
    parameters: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    task_id: str
    title: str
    description: str
    status: str
    priority: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    agent_id: Optional[int]
    result_summary: Optional[str] = None
    
    class Config:
        from_attributes = True


class ToolCreate(BaseModel):
    tool_id: str
    name: str
    description: str
    category: str


class ToolResponse(BaseModel):
    id: int
    tool_id: str
    name: str
    description: str
    category: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    message_id: str
    sender_id: str
    receiver_id: str
    content: str
    message_type: MessageType


class MessageResponse(BaseModel):
    id: int
    message_id: str
    sender_id: str
    receiver_id: str
    content: str
    message_type: str
    created_at: datetime
    is_read: bool
    
    class Config:
        from_attributes = True


class AuditResultCreate(BaseModel):
    result_id: str
    task_id: str
    severity: Severity
    category: Category
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None


class AuditResultResponse(BaseModel):
    id: int
    result_id: str
    task_id: str
    task_title: Optional[str] = None
    severity: str
    category: str
    description: str
    file_path: Optional[str]
    line_number: Optional[int]
    code_snippet: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ToolExecutionCreate(BaseModel):
    execution_id: str
    tool_id: str
    task_id: str
    input_params: str


class ToolExecutionResponse(BaseModel):
    id: int
    execution_id: str
    tool_id: str
    task_id: str
    status: str
    input_params: str
    output_result: str
    error_message: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentMessage(BaseModel):
    sender_id: str
    receiver_id: str
    content: str
    message_type: MessageType
    timestamp: datetime = Field(default_factory=datetime.now)
