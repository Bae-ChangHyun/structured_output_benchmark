from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class FileInfo(BaseModel):
    filename: str
    size: int
    content_type: str
    upload_path: str
