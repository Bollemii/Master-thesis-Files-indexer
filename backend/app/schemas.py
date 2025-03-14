from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

from sqlmodel import SQLModel

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
    preview_url: str | None


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
