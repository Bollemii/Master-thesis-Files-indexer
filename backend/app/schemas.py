from pydantic import BaseModel
from datetime import datetime
import uuid

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