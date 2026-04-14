from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskState(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class TaskCreate(BaseModel):
    data: str = Field(..., min_length=1, max_length=1000)


class TaskStatus(BaseModel):
    id: str
    status: TaskState
    result: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
