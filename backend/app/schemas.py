import uuid
from datetime import datetime
from typing import Optional

from app.utils.process_manager import ProcessStatus
from pydantic import BaseModel
from sqlmodel import SQLModel


class TopicBase(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None

class TopicResponse(TopicBase):
    weight: float
    words: dict[str, float]

class TopicsList(BaseModel):
    items: list[TopicBase]

class DocumentList(BaseModel):
    id: uuid.UUID
    filename: str
    upload_date: datetime
    processed: bool
    preview_url: str | None


class DocumentDetail(DocumentList):
    topics: list[TopicResponse]


class DocumentsPagination(BaseModel):
    items: list[DocumentList]
    total: int
    page: int
    limit: int
    n_not_processed: int


class DocumentProcess(BaseModel):
    message: str


class DocumentProcessStatus(BaseModel):
    status: ProcessStatus
    last_run_time: Optional[datetime] = None


class Document(SQLModel):
    id: uuid.UUID
    filename: str
    upload_date: datetime
    processed: bool

    @property
    def preview_url(self) -> str:
        """URL for thumbnail preview"""
        return f"/documents/{self.id}/preview?size=thumbnail"

    @property
    def detail_preview_url(self) -> str:
        """URL for detailed preview"""
        return f"/documents/{self.id}/preview?size=detail"

class ChatbotRequest(BaseModel):
    question: str
    conversation_history: list[list[str]] = []

class ChatbotResponse(BaseModel):
    answer: str
    sources: list[str]

class UserBase(BaseModel):
    username: str
    is_active: bool = True
    is_superuser: bool = False
    creation_date: datetime


class UserDetail(UserBase):
    id: uuid.UUID


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    username: str
    password: str
