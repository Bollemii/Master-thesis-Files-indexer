from concurrent.futures import ProcessPoolExecutor
import os
import pathlib
import uuid
import pandas as pd
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from app.database import get_session
from app.models import Document, Topic, DocumentTopicLink
from app.schemas import DocumentList, DocumentDetail, DocumentsPagination, TopicResponse
from app.utils.process_manager import ProcessManager

DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

process_manager = ProcessManager()

@router.post("/documents/", response_model=Document, status_code=201)
async def upload_document(session: SessionDep, file: UploadFile):
    """Upload a new document"""
    try:
        # Save document to local storage
        # overwriting if file already exists
        file_path = os.path.join(DOCUMENT_STORAGE_PATH, file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        document = Document(
            filename=os.path.splitext(file.filename)[0],
            path=file_path
        )
        
        session.add(document)
        session.commit()
        session.refresh(document)
        
        return Document(
            id=document.id,
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed,
            path=document.path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def get_document(document_id: uuid.UUID, session: SessionDep):
    """Retrieve document information by ID"""
    try:
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        topics = session.exec(
            select(Topic)
            .join(DocumentTopicLink)
            .where(DocumentTopicLink.document_id == document.id)
        ).all()
        
        topic_responses = []
        for topic in topics:
            document_topic_link = session.exec(
            select(DocumentTopicLink)
            .where(DocumentTopicLink.document_id == document.id)
            .where(DocumentTopicLink.topic_id == topic.id)
            ).first()
            if document_topic_link:
                topic_response = TopicResponse(
                    id=topic.id,
                    name=topic.name,
                    description=topic.description,
                    weight=document_topic_link.weight,
                    words=topic.words
                )
                topic_responses.append(topic_response)
        
        document_response = DocumentDetail(
            id=document.id,
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed,
            topics=topic_responses
        )
        
        return document_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/", response_model=DocumentsPagination)
async def list_documents(session: SessionDep,
                         q: str | None = None,
                         page: int = 0,
                         limit: int = 50):
    """List all documents with topics for each document"""
    try:
        query = select(Document)

        if q:
            search = f"%{q}%"
            query = query.where(Document.filename.ilike(search))

        total = len(session.exec(query).all())
        query = query.offset(page * limit).limit(limit)

        result = []
        documents = session.exec(query)
        for document in documents:
            document_response = DocumentList(
                id=document.id,
                filename=document.filename,
                upload_date=document.upload_date,
                processed=document.processed,
            )
            result.append(document_response)
        
        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/documents/process", status_code=202)
def process_document(session: SessionDep):
    """Process documents and extract topics"""
    
    if process_manager.is_running():
        raise HTTPException(
            status_code=409,
            detail="Process is already running"
        )
    
    try:
        documents = session.exec(select(Document)).all()
        if not documents:
            raise HTTPException(status_code=500, detail="No documents available")

        elif all(document.processed for document in documents):
            raise HTTPException(status_code=500, detail="All documents are already processed")
        
        process_manager.run_process()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Processing started"}

@router.get("/documents/process/status")
async def get_process_status():
    """Get the status of the document processing task"""
    response = {
        "status": process_manager.status.value,
        "last_run_time": process_manager.last_run_time
    }
    return response