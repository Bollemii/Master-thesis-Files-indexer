import os
import uuid
import pandas as pd
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Document, Topic, DocumentTopicLink
from app.schemas import DocumentResponse, TopicResponse
from app.TopicModeling import topic_modeling_v3

# Document storage setup
DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

process_running = False

@router.post("/documents/", response_model=Document)
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
        
        # Create document record
        document = Document(
            filename=file.filename,
            path=file_path
        )
        
        # Save to database
        session.add(document)
        session.commit()
        session.refresh(document)

        # Create a fake topic with some words
        fake_topic = Topic(
            name="Fake Topic",
            description="This is a fake topic for testing.",
            words={"word1": 10, "word2": 5, "word3": 2}
        )
        
        session.add(fake_topic)
        session.commit()
        session.refresh(fake_topic)
        
        # Create a link between the document and the fake topic
        document_topic_link = DocumentTopicLink(
            document_id=document.id,
            topic_id=fake_topic.id,
            weight=1.0
        )
        
        session.add(document_topic_link)
        session.commit()
        
        return Document(
            id=document.id,
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed,
            path=document.path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: uuid.UUID, session: SessionDep):
    """Retrieve document information by ID"""
    try:
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Retrieve topics associated with the document
        topics = session.exec(
            select(Topic)
            .join(DocumentTopicLink)
            .where(DocumentTopicLink.document_id == document.id)
        ).all()
        
        topic_responses = [
            TopicResponse(
                id=topic.id,
                name=topic.name,
                description=topic.description,
                words=topic.words
            ) for topic in topics
        ]
        
        document_response = DocumentResponse(
            id=document.id,
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed,
            topics=topic_responses
        )
        
        return document_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/process")
async def process_document(session: SessionDep):
    """Process documents and extract topics"""
    global process_running
    if process_running:
        raise HTTPException(status_code=409, detail="Process is already running")
    
    process_running = True
    try:
        doc_df = pd.DataFrame()
        documents = session.exec(select(Document)).all()
        for document in documents:
            doc_df = doc_df.append({
                "file_path": document.path,
                "creation_time": datetime.timestamp(document.upload_date),
                "file_size": os.path.getsize(document.path)
            }, ignore_index=True)
        topics, doc_topics = topic_modeling_v3.run(doc_df)

        # Store topics in database and associate with documents
        for topic_idx, topic_words_frequencies in enumerate(topics):
            topic = Topic(
                name=f"Topic {topic_idx}",
                words={word: frequency for word, frequency in topic_words_frequencies}
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)

            for doc_idx, topic_dist in enumerate(doc_topics):
                document = session.get(Document, doc_idx)
                if topic_dist[1][topic_idx] > 0.1:
                    document_topic_link = DocumentTopicLink(
                        document_id=document.id,
                        topic_id=topic.id,
                        weight=topic_dist[1][topic_idx]
                    )
                    session.add(document_topic_link)
                    session.commit()
                    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        process_running = False

@router.get("/documents/", response_model=list[DocumentResponse])
async def list_documents(session: SessionDep):
    """List all documents with topics for each document"""
    try:
        result = []
        documents = session.exec(select(Document)).all()
        for document in documents:
            topics = session.exec(
                select(Topic)
                .join(DocumentTopicLink)
                .where(DocumentTopicLink.document_id == document.id)
            ).all()
            topic_responses = [
                TopicResponse(
                    id=topic.id,
                    name=topic.name,
                    description=topic.description,
                    words=topic.words
                ) for topic in topics
            ]
            document_response = DocumentResponse(
                id=document.id,
                filename=document.filename,
                upload_date=document.upload_date,
                processed=document.processed,
                topics=topic_responses
            )
            result.append(document_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result