import uuid
from sqlmodel import SQLModel, Field, Relationship, Column
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


# Association table for many-to-many relationship between Document and Topic
class DocumentTopicLink(SQLModel, table=True):
    document_id: uuid.UUID | None = Field(
        default=None, 
        foreign_key="document.id", 
        primary_key=True
    )
    topic_id: uuid.UUID | None = Field(
        default=None, 
        foreign_key="topic.id", 
        primary_key=True
    )
    weight: float = Field(default=0.0)

class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    creation_date: datetime = Field(default=datetime.now())

class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    documents: list["Document"] = Relationship(back_populates="owner")

class DocumentBase(SQLModel):
    filename: str = Field(unique=True, index=True)
    path: str
    processed: bool = False
    upload_date: datetime = Field(default=datetime.now())

class Document(DocumentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    owner: User | None = Relationship(back_populates="documents")
    topics: list["Topic"] | None = Relationship(back_populates="document",
                                         link_model=DocumentTopicLink)

class TopicBase(SQLModel):
    name: str = Field(unique=True, index=True)
    description: str | None = None
    words: dict[str, float] = Field(default={}, sa_column=Column("words",JSON))

class Topic(TopicBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document: list["Document"] = Relationship(back_populates="topics",
                                              link_model=DocumentTopicLink)
