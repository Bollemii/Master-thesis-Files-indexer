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
from app.schemas import DocumentResponse, TopicResponse
from app.TopicModeling import topic_modeling_v3

DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

process_running = False

def run_process_document(documents, session: Session):
    try:
        file_path_list = []
        file_name_list = []
        time_list = []
        size_list = []

        for document in documents:
            if os.path.isfile(document.path) and pathlib.Path(document.path).suffix in ['.pdf']:
                file_path_list.append(document.path)
                file_name_list.append(document.filename)
                time_list.append(datetime.timestamp(document.upload_date))
                size_list.append(os.path.getsize(document.path))

        doc_df = pd.DataFrame({
                'file_path': file_path_list,
                'file_name': file_name_list, 
                'creation_time': time_list,
                'file_size': size_list
            })

        topics, doc_topics = topic_modeling_v3.run(doc_df)

        for topic_idx, topic_words_frequencies in enumerate(topics):
            try:
                topic = session.exec(select(Topic).where(Topic.name == f"Topic {topic_idx}")).first()
                if topic:
                    topic.words = {word: int(frequency) for word, frequency in topic_words_frequencies}
                else:
                    topic = Topic(
                        name=f"Topic {topic_idx}",
                        words={word: int(frequency) for word, frequency in topic_words_frequencies}
                    )
                    session.add(topic)
                session.commit()
                session.refresh(topic)
            except Exception as e:
                print(f"Error processing topic {topic_idx}: {str(e)}")
                session.rollback()
                continue
        
        for doc_topic in doc_topics:
            try:
                document = session.exec(select(Document).where(Document.filename == doc_topic[0])).first()
                if document:
                    for topic_idx, weight in enumerate(doc_topic[1]):
                        topic = session.exec(select(Topic).where(Topic.name == f"Topic {topic_idx}")).first()
                        document_topic_link = session.exec(
                            select(DocumentTopicLink)
                            .where(DocumentTopicLink.document_id == document.id)
                            .where(DocumentTopicLink.topic_id == topic.id)
                        ).first()
                        if document_topic_link:
                            document_topic_link.weight = float(weight)
                        else:
                            document_topic_link = DocumentTopicLink(
                                document_id=document.id,
                                topic_id=topic.id,
                                weight=float(weight)
                            )
                            session.add(document_topic_link)
                        session.commit()

                document.processed = True
                session.add(document)
                session.commit()
            except Exception as e:
                print(f"Error processing document {doc_topic[0]}: {str(e)}")
                session.rollback()
                continue

    except Exception as e:
        print(f"Process error: {str(e)}")
        session.rollback()
    finally:
        session.close()
        print("Processing completed")

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

@router.get("/documents/{document_id}", response_model=DocumentResponse)
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

@router.post("/documents/process", status_code=202)
async def process_document(session: SessionDep, background_tasks: BackgroundTasks):
    """Process documents and extract topics"""
    global process_running
    if process_running:
        raise HTTPException(status_code=500, detail="Process is already running")
    
    process_running = True
    try:
        documents = session.exec(select(Document)).all()
        if not documents:
            raise HTTPException(status_code=500, detail="No documents available")

        elif all(document.processed for document in documents):
            raise HTTPException(status_code=500, detail="All documents are already processed")

        background_tasks.add_task(run_process_document, documents, session)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        process_running = False
    return {"message": "Processing started"}

@router.get("/documents/", response_model=list[DocumentResponse])
async def list_documents(session: SessionDep, q: str | None = None):
    """List all documents with topics for each document"""
    try:
        query = select(Document)

        if q:
            search = f"%{q}%"
            query = query.where(Document.filename.ilike(search))

        result = []
        documents = session.exec(query).all()
        for document in documents:
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