import os
import uuid
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.models import Document, User
from app.schemas import (
    DocumentDetail,
    DocumentProcess,
    DocumentProcessStatus,
    DocumentsPagination,
    DocumentList,
    TopicResponse,
)
from app.TopicModeling.topic_modeling_v3 import delete_document_from_cache
from app.utils.preview import PreviewManager
from app.utils.process_manager import ProcessManager
from app.utils.security import get_current_user
from app.utils.document_transformer import space_between_word
from app.database.documents import (
    get_document_by_id,
    create_document,
    get_document_topics_by_id,
    get_documents_by_filename_like,
    get_all_documents,
    get_document_count,
    delete_document as delete_document_db,
    update_document as update_document_db,
)

DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

router = APIRouter()

preview_manager = PreviewManager()
process_manager = ProcessManager()


@router.get("/documents/{document_id}/preview", status_code=200, tags=["preview"])
@router.head("/documents/{document_id}/preview", status_code=200, tags=["preview"])
async def get_document_preview(
    document_id: uuid.UUID,
    size: str = "thumbnail",
    _: User = Depends(get_current_user),
):
    """Get the preview image for a document with specified size"""
    try:
        document = get_document_by_id(str(document_id))
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
            raise HTTPException(
                status_code=500, detail="Failed to generate preview image"
            )

        return FileResponse(preview_path, media_type="image/webp")
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Generating preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/documents/", response_model=Document, status_code=201, tags=["documents"]
)
async def upload_document(
    file: UploadFile,
    _: User = Depends(get_current_user),
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

        base_filename = os.path.splitext(file.filename)[0]
        spaced_filename = space_between_word(base_filename)

        # Create document in the database
        document = create_document(
            filename=spaced_filename,
            document_path=file_path,
        )

        # Generate preview image
        preview_manager.generate_preview(document.path, str(document.id))

        return Document(
            id=uuid.UUID(document.id),
            filename=document.filename,
            path=document.path,
            processed=document.processed,
            upload_date=document.upload_date,
        )
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.get(
    "/documents/{document_id}", response_model=DocumentDetail, tags=["documents"]
)
async def get_document(
    document_id: uuid.UUID,
    _: User = Depends(get_current_user),
):
    """Retrieve document information by ID"""
    try:
        document = get_document_by_id(str(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        topics = get_document_topics_by_id(str(document_id))

        document_response = DocumentDetail(
            id=uuid.UUID(document.id),
            filename=document.filename,
            upload_date=document.upload_date,
            processed=document.processed,
            preview_url=(
                f"/documents/{document.id}/preview"
                if document.path.lower().endswith(".pdf")
                else None
            ),
            topics=[
                TopicResponse(
                    id=uuid.UUID(topic.id),
                    name=topic.name,
                    words=topic.words,
                    description=topic.description,
                    weight=topic.weight,
                )
                for topic in topics
            ],
        )

        return document_response
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Retrieving document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.get("/documents/", response_model=DocumentsPagination, tags=["documents"])
async def list_documents(
    q: str | None = None,
    page: int = 1,
    limit: int = 20,
    _: User = Depends(get_current_user),
):
    """List all documents with topics for each document"""
    try:
        total = get_document_count(q)
        documents = (
            get_documents_by_filename_like(q, page, limit)
            if q
            else get_all_documents(page, limit)
        )

        result = [
            DocumentList(
                id=uuid.UUID(document.id),
                filename=document.filename,
                upload_date=document.upload_date,
                processed=document.processed,
                preview_url=(
                    f"/documents/{document.id}/preview"
                    if document.path.lower().endswith(".pdf")
                    else None
                ),
            )
            for document in documents
        ]

        return {"items": result, "total": total, "page": page, "limit": limit}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.post(
    "/documents/process",
    status_code=202,
    response_model=DocumentProcess,
    tags=["process"],
)
def process_document(_: User = Depends(get_current_user)):
    """Process documents and extract topics"""

    if process_manager.is_running():
        raise HTTPException(status_code=409, detail="Process is already running")

    try:
        documents = get_all_documents()
        if not documents:
            raise HTTPException(status_code=404, detail="No documents available")

        if all(document.processed for document in documents):
            raise HTTPException(
                status_code=409, detail="All documents are already processed"
            )

        process_manager.run_process(documents)

        return {"message": "Processing started"}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Processing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.get(
    "/documents/process/status",
    status_code=200,
    response_model=DocumentProcessStatus,
    tags=["process"],
)
async def get_process_status(_: User = Depends(get_current_user)):
    """Get the status of the document processing task"""
    response = {
        "status": process_manager.status.value,
        "last_run_time": process_manager.last_run_time,
    }
    return response


@router.delete("/documents/{document_id}", tags=["documents"])
async def delete_document(
    document_id: uuid.UUID,
    _: User = Depends(get_current_user),
):
    """Delete a document by ID"""
    try:
        document = get_document_by_id(str(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        delete_document_from_cache(document.path)

        delete_document_db(str(document_id))

        return {"message": "Document deleted"}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.put("/documents/{document_id}", response_model=Document, tags=["documents"])
async def update_document(
    document_id: uuid.UUID,
    _: User = Depends(get_current_user),
    file: UploadFile = None,
):
    """Update a document's filename or content"""
    try:
        document = get_document_by_id(str(document_id))
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

        update_document_db(
            document_id=str(document_id),
            filename=spaced_filename,
            document_path=file_path,
            processed=False,
        )
        document.filename = spaced_filename
        document.path = file_path
        document.processed = False

        preview_manager.generate_preview(file_path, str(document_id), force=True)

        return Document(
            id=uuid.UUID(document.id),
            filename=document.filename,
            path=document.path,
            processed=document.processed,
            upload_date=document.upload_date,
        )
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Updating document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.put(
    "/documents/{document_id}/name", response_model=Document, tags=["documents"]
)
async def update_document_name(
    document_id: uuid.UUID,
    _: User = Depends(get_current_user),
    name: str = Form(None),
):
    """Update a document's filename"""
    try:
        document = get_document_by_id(str(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        update_document_db(
            str(document_id),
            filename=name,
        )
        document.filename = name

        return document
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Updating document name: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
