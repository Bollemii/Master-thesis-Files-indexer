from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Annotated
import uvicorn
from datetime import datetime
import uuid
import os
from sqlmodel import SQLModel, create_engine, Field, Session, select
# from sqlalchemy.dialects.sqlite import JSON
# from sqlalchemy.dialects.postgresql import JSON

# Pydantic models for data validation
class DocumentBase(SQLModel):
    filename: str
    upload_date: datetime
    processed: bool = False
    topics: str | None = Field(default=None)

class TopicResult(BaseModel):
    document_id: str
    topics: list[dict]

class Document(DocumentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)

# Set document storage path
DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Initialize FastAPI app
app = FastAPI(title="Document Processing API")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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
            processed=document.processed,
            topics=document.topics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: str, session: SessionDep):
    """Retrieve document information by ID"""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return Document(
        id=document.id,
        filename=document.filename,
        upload_date=document.upload_date,
        processed=document.processed,
        topics=document.topics
    )

@app.post("/documents/process")
async def process_document():
    """Process documents and extract topics"""
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/", response_model=list[Document])
async def list_documents(session: SessionDep):
    """List all documents"""
    documents = session.exec(select(Document)).all()
    return [
        Document(
            id=doc.id,
            filename=doc.filename,
            upload_date=doc.upload_date,
            processed=doc.processed,
            topics=doc.topics
        )
        for doc in documents
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)