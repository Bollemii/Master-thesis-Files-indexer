from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

from app.utils.process_manager import ProcessStatus

class TopicResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    weight: float
    words: dict[str, float]

class DocumentList(BaseModel):
    id: uuid.UUID
    filename: str
    upload_date: datetime
    processed: bool

class DocumentDetail(DocumentList):
    topics: list[TopicResponse]

class DocumentsPagination(BaseModel):
    items: list[DocumentList]
    total: int
    page: int
    limit: int

class DocumentProcess(BaseModel):
    message: str

class DocumentProcessStatus(BaseModel):
    status: ProcessStatus
    last_run_time: Optional[datetime] = None