from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from typing import Annotated
import uvicorn
from datetime import datetime
import uuid
import os
from sqlmodel import SQLModel, create_engine, Field, Session, select


# Pydantic models for database and data validation
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str
    role: str
    creation_date: datetime = Field(default=datetime.now())

class DocumentBase(SQLModel):
    filename: str
    processed: bool = False
    upload_user: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    upload_date: datetime

class Document(DocumentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

class Topics(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    topics: str
    document: uuid.UUID = Field(foreign_key="document.id")

class DocumentWithTopics(BaseModel):
    document: Document
    topics: list[str] | None = None

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
engine = create_engine(DATABASE_URL)

# Document storage setup
DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# Initialize FastAPI app
app = FastAPI(title="Document Processing API", lifespan=lifespan)

# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()

@app.post("/documents/", response_model=Document)
async def upload_document(session: SessionDep, file: UploadFile):
    """Upload a new document"""
    try:
        # Save document to local storage
        file_path = os.path.join(DOCUMENT_STORAGE_PATH, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create document record
        document = Document(
            filename=file.filename,
            upload_date=datetime.now()
        )
        
        # Store document record in database
        session.add(document)
        session.commit()
        session.refresh(document)
        
        return Document(
            id=document.id,
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}", response_model=DocumentWithTopics)
async def get_document(document_id: uuid.UUID, session: SessionDep):
    """Retrieve document information by ID"""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    topics = session.exec(select(Topics).where(Topics.document == document.id)).all()
    result = DocumentWithTopics(
        document=Document(
            id=document.id,
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed,
            upload_user=document.upload_user
        ),
        topics=[topic.topics for topic in topics] if topics else None
    )
    return result

@app.post("/documents/process")
async def process_document():
    """Process documents and extract topics"""
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/", response_model=list[DocumentWithTopics])
async def list_documents(session: SessionDep):
    """List all documents with topics for each document"""
    documents = session.exec(select(Document)).all()
    result = []
    for doc in documents:
        topics = session.exec(select(Topics).where(Topics.document == doc.id)).all()
        result.append(DocumentWithTopics(
            document=Document(
                id=doc.id,
                filename=doc.filename,
                upload_date=doc.upload_date,
                processed=doc.processed,
                upload_user=doc.upload_user
            ),
            topics=[topic.topics for topic in topics] if topics else None
        ))
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)