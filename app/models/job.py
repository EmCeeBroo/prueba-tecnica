from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Job(BaseModel):
    id: UUID
    status: JobStatus
    created_at: datetime
    updated_at: datetime | None = None
    error_message: str | None = None