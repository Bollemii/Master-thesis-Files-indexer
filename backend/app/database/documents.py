import json

from app.database.main import execute_neo4j_query, generate_id, get_current_timestamp
from app.database.models import Document, DocumentTopic

def get_document_count(filename : str | None = None) -> int:
    """Get the count of documents in the database"""
    if filename is not None:
        result = execute_neo4j_query(
            "MATCH (d:Document) WHERE d.filename CONTAINS $filename RETURN COUNT(d) as count;",
            parameters={"filename": filename},
        )
    else:
        result = execute_neo4j_query(
            "MATCH (d:Document) RETURN COUNT(d) as count;",
        )
    return result[0]["count"] if result else 0

def get_all_documents(page: int | None = None, limit: int | None = None) -> list[Document]:
    """Get all documents from the database"""
    if page is not None and limit is not None:
        result = execute_neo4j_query(
            "MATCH (d:Document) RETURN d SKIP $skip LIMIT $limit;",
            parameters={"skip": (page - 1) * limit, "limit": limit},
        )
    else:
        result = execute_neo4j_query(
            "MATCH (d:Document) RETURN d;",
        )
    return [
        Document(
            identifier=doc["d"]["id"],
            filename=doc["d"]["filename"],
            path=doc["d"]["path"],
            processed=doc["d"]["processed"],
            upload_date=doc["d"]["upload_date"],
        )
        for doc in result
    ] if result else []

def get_document_by_id(document_id: str) -> Document | None:
    """Get a document by its ID"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    result = execute_neo4j_query(
        "MATCH (d:Document {id: $id}) RETURN d;",
        parameters={"id": document_id},
    )
    return Document(
        identifier=result[0]["d"]["id"],
        filename=result[0]["d"]["filename"],
        path=result[0]["d"]["path"],
        processed=result[0]["d"]["processed"],
        upload_date=result[0]["d"]["upload_date"],
    ) if result else None

def get_document_by_filename(filename: str) -> Document | None:
    """Get a document by its filename"""
    if not filename:
        raise ValueError("Filename must be provided.")
    result = execute_neo4j_query(
        "MATCH (d:Document {filename: $filename}) RETURN d;",
        parameters={"filename": filename},
    )
    return Document(
        identifier=result[0]["d"]["id"],
        filename=result[0]["d"]["filename"],
        path=result[0]["d"]["path"],
        processed=result[0]["d"]["processed"],
        upload_date=result[0]["d"]["upload_date"],
    ) if result else None


def get_documents_by_filename_like(
    filename: str, page: int | None = None, limit: int | None = None
) -> list[Document]:
    """Get documents by a partial filename match"""
    if not filename:
        raise ValueError("Filename must be provided.")

    if page is not None or limit is not None:
        result = execute_neo4j_query(
            "MATCH (d:Document) WHERE d.filename CONTAINS $filename RETURN d SKIP $skip LIMIT $limit;",
            parameters={
                "filename": filename,
                "skip": (page - 1) * limit,
                "limit": limit,
            },
        )
    else:
        result = execute_neo4j_query(
            "MATCH (d:Document) WHERE d.filename CONTAINS $filename RETURN d;",
            parameters={"filename": filename},
        )
    return [
        Document(
            identifier=doc["d"]["id"],
            filename=doc["d"]["filename"],
            path=doc["d"]["path"],
            processed=doc["d"]["processed"],
            upload_date=doc["d"]["upload_date"],
        )
        for doc in result
    ] if result else []


def get_document_topics_by_id(document_id: str) -> list[DocumentTopic]:
    """Get topics associated with a document by its ID"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    result = execute_neo4j_query(
        "MATCH (d:Document {id: $id})-[l:HAS_TOPIC]->(t:Topic) RETURN t as topic, l.weight as weight;",
        parameters={"id": document_id},
    )
    return [
        DocumentTopic(
            topic_id=topic["topic"]["id"],
            name=topic["topic"]["name"],
            words=json.loads(topic["topic"]["words"]),
            weight=topic["weight"],
            description=topic["topic"]["description"],
        )
        for topic in result
    ] if result else []


def create_document(
    filename: str, document_path: str, processed: bool = False
) -> Document:
    """Create a new document in the database"""
    if not filename or not document_path:
        raise ValueError("Filename and document path must be provided.")

    documents = get_all_documents()
    if any(doc.filename == filename for doc in documents):
        raise ValueError("Document with this filename already exists.")

    identifier = generate_id()
    upload_date = get_current_timestamp()
    execute_neo4j_query(
        "CREATE (d:Document {id: $id, filename: $filename, path: $path, processed: $processed, upload_date: $upload_date});",
        parameters={
            "id": identifier,
            "filename": filename,
            "path": document_path,
            "processed": processed,
            "upload_date": upload_date,
        },
    )
    return Document(identifier, filename, document_path, processed, upload_date)

def link_document_to_topic(
    document_id: str, topic_id: str, weight: float = 1.0
) -> None:
    """Link a document to a topic with a specified weight"""
    if not document_id or not topic_id:
        raise ValueError("Document ID and Topic ID must be provided.")
    execute_neo4j_query(
        "MATCH (d:Document {id: $document_id}), (t:Topic {id: $topic_id}) CREATE (d)-[l:HAS_TOPIC {weight: $weight}]->(t);",
        parameters={"document_id": document_id, "topic_id": topic_id, "weight": weight},
    )

def update_document(
    document_id: str, filename: str | None = None, document_path: str | None = None, processed: bool | None = None
) -> Document:
    """Update an existing document in the database"""
    if not document_id:
        raise ValueError("Document ID must be provided.")

    document = get_document_by_id(document_id)
    if not document:
        raise ValueError("Document not found.")

    updates = {}
    if filename is not None:
        updates["filename"] = filename
    if document_path is not None:
        updates["path"] = document_path
    if processed is not None:
        updates["processed"] = processed

    if not updates:
        return document

    set_clause = ", ".join([f"d.{key} = ${key}" for key in updates])
    parameters = {**updates, "id": document_id}

    execute_neo4j_query(
        f"MATCH (d:Document {{id: $id}}) SET {set_clause};",
        parameters=parameters,
    )
    return Document(
        document_id,
        updates.get("filename", document.filename),
        document_path if document_path else document.path,
        updates.get("processed", document.processed),
        document.upload_date,
    )

def process_document(document_id: str) -> None:
    """Mark a document as processed"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    execute_neo4j_query(
        "MATCH (d:Document {id: $id}) SET d.processed = true;",
        parameters={"id": document_id},
    )

def update_weight_of_document_topic_link(
    document_id: str, topic_id: str, weight: float
) -> None:
    """Update the weight of a document-topic link"""
    if not document_id or not topic_id:
        raise ValueError("Document ID and Topic ID must be provided.")
    execute_neo4j_query(
        "MATCH (d:Document {id: $document_id})-[l:HAS_TOPIC]->(t:Topic {id: $topic_id}) SET l.weight = $weight;",
        parameters={"document_id": document_id, "topic_id": topic_id, "weight": weight},
    )

def delete_document(document_id: str) -> None:
    """Delete a document by its ID"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    execute_neo4j_query(
        "MATCH (d:Document {id: $id}) DETACH DELETE d;",
        parameters={"id": document_id},
    )
