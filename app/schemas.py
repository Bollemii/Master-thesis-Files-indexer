from pydantic import BaseModel
from datetime import datetime
import uuid

class TopicResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    words: dict[str, int]

class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    upload_date: datetime
    processed: bool
    topics: list[TopicResponse]