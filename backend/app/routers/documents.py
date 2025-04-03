import os
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from app.database import get_session
from app.models import Document, Topic, DocumentTopicLink, User
from app.schemas import (
    DocumentList,
    DocumentDetail,
    DocumentProcess,
    DocumentProcessStatus,
    DocumentsPagination,
    TopicResponse,
)
from app.utils.process_manager import ProcessManager
from app.utils.space_word import space_between_word
from app.utils.preview import PreviewManager
from app.utils.security import get_current_user
from app.TopicModeling.topic_modeling_v3 import delete_document_from_cache

DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

preview_manager = PreviewManager()
process_manager = ProcessManager()


@router.get("/documents/{document_id}/preview", status_code=200, tags=["preview"])
@router.head("/documents/{document_id}/preview", status_code=200, tags=["preview"])
async def get_document_preview(
    document_id: uuid.UUID,
    session: SessionDep,
    size: str = "thumbnail",
    current_user: User = Depends(get_current_user),
):
    """Get the preview image for a document with specified size"""
    try:
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if size not in ["thumbnail", "detail"]:
            size = "thumbnail"

        if (
            str(document_id) in preview_manager.preview_cache
            and size in preview_manager.preview_cache[str(document_id)]
        ):
            preview_path = preview_manager.preview_cache[str(document_id)][size]
            if os.path.exists(preview_path):
                return FileResponse(preview_path, media_type="image/webp")

        preview_path = preview_manager.generate_preview(
            document.path, str(document_id), size
        )

        if not preview_path:
            raise HTTPException(status_code=404, detail="Preview not available")

        return FileResponse(preview_path, media_type="image/webp")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/documents/", response_model=Document, status_code=201, tags=["documents"]
)
async def upload_document(
    session: SessionDep,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
):
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

        # if file.filename.lower().endswith('.pdf'):
        #     pdf_title = get_pdf_title(file_path)
        #     if pdf_title:
        #         spaced_filename = pdf_title
        #     else:
        #         base_filename = os.path.splitext(file.filename)[0]
        #         spaced_filename = space_between_word(base_filename)
        # else:
        base_filename = os.path.splitext(file.filename)[0]
        spaced_filename = space_between_word(base_filename)

        document = Document(filename=spaced_filename, path=file_path)

        session.add(document)
        session.commit()
        session.refresh(document)

        preview_manager.generate_preview(document.path, str(document.id))

        return Document(
            id=document.id,
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed,
            path=document.path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/documents/{document_id}", response_model=DocumentDetail, tags=["documents"]
)
async def get_document(
    document_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
):
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
                    words=topic.words,
                )
                topic_responses.append(topic_response)

        document_response = DocumentDetail(
            id=document.id,
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed,
            preview_url=(
                f"/documents/{document.id}/preview"
                if document.path.lower().endswith(".pdf")
                else None
            ),
            topics=topic_responses,
        )

        return document_response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/", response_model=DocumentsPagination, tags=["documents"])
async def list_documents(
    session: SessionDep,
    q: str | None = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """List all documents with topics for each document"""
    try:
        query = select(Document)

        if q:
            search = f"%{q}%"
            query = query.where(Document.filename.ilike(search))

        total = len(session.exec(query).all())
        query = query.offset((page - 1) * limit).limit(limit)

        result = []
        documents = session.exec(query)
        for document in documents:
            document_response = DocumentList(
                id=document.id,
                filename=document.filename,
                upload_date=document.upload_date,
                preview_url=(
                    f"/documents/{document.id}/preview"
                    if document.path.lower().endswith(".pdf")
                    else None
                ),
                processed=document.processed,
            )
            result.append(document_response)

        return {"items": result, "total": total, "page": page, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/documents/process",
    status_code=202,
    response_model=DocumentProcess,
    tags=["process"],
)
def process_document(
    session: SessionDep, current_user: User = Depends(get_current_user)
):
    """Process documents and extract topics"""

    if process_manager.is_running():
        raise HTTPException(status_code=409, detail="Process is already running")

    try:
        documents = session.exec(select(Document)).all()
        if not documents:
            raise HTTPException(status_code=404, detail="No documents available")

        elif all(document.processed for document in documents):
            raise HTTPException(
                status_code=409, detail="All documents are already processed"
            )

        process_manager.run_process()

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Processing started"}


@router.get(
    "/documents/process/status",
    status_code=200,
    response_model=DocumentProcessStatus,
    tags=["process"],
)
async def get_process_status(current_user: User = Depends(get_current_user)):
    """Get the status of the document processing task"""
    response = {
        "status": process_manager.status.value,
        "last_run_time": process_manager.last_run_time,
    }
    return response


@router.delete("/documents/{document_id}", tags=["documents"])
async def delete_document(
    document_id: uuid.UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
):
    """Delete a document by ID"""
    try:
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        delete_document_from_cache(document.path)

        session.delete(document)
        session.commit()

        return {"message": "Document deleted"}
    except Exception:
        raise


@router.put("/documents/{document_id}", response_model=Document, tags=["documents"])
async def update_document(
    session: SessionDep,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    file: UploadFile = None,
):
    """Update a document's filename or content"""
    try:
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = os.path.join(DOCUMENT_STORAGE_PATH, file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        base_filename = os.path.splitext(file.filename)[0]
        spaced_filename = space_between_word(base_filename)

        document.filename = spaced_filename
        document.path = file_path
        document.processed = False

        session.commit()
        session.refresh(document)

        preview_manager.generate_preview(document.path, str(document.id), force=True)

        return document
    except Exception:
        raise


@router.put(
    "/documents/{document_id}/name", response_model=Document, tags=["documents"]
)
async def update_document_name(
    session: SessionDep,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    name: str = Form(None),
):
    """Update a document's filename"""
    try:
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        document.filename = name
        session.commit()
        session.refresh(document)

        return document
    except Exception:
        raise
