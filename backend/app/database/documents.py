import json

from app.database.main import execute_neo4j_query, generate_id, get_current_timestamp
from app.database.models import Document, DocumentTopic

# =================================================
# Document Management Functions
# =================================================

def get_document_count(filename: str | None = None) -> int:
    """Get the count of documents in the database"""
    if filename is not None:
        result = execute_neo4j_query(
            "MATCH (d:Document) WHERE tolower(d.filename) CONTAINS tolower($filename) RETURN COUNT(d) as count;",
            parameters={"filename": filename},
        )
    else:
        result = execute_neo4j_query(
            "MATCH (d:Document) RETURN COUNT(d) as count;",
        )
    return result[0]["count"] if result else 0


def get_all_documents(
    page: int | None = None, limit: int | None = None
) -> list[Document]:
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
    return (
        [
            Document(
                identifier=doc["d"]["id"],
                filename=doc["d"]["filename"],
                path=doc["d"]["path"],
                processed=doc["d"]["processed"],
                upload_date=doc["d"]["upload_date"],
            )
            for doc in result
        ]
        if result
        else []
    )


def get_document_by_id(document_id: str) -> Document | None:
    """Get a document by its ID"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    result = execute_neo4j_query(
        "MATCH (d:Document {id: $id}) RETURN d;",
        parameters={"id": document_id},
    )
    if result:
        doc = result[0]["d"]
        return Document(
            identifier=doc["id"],
            filename=doc["filename"],
            path=doc["path"],
            processed=doc["processed"],
            upload_date=doc["upload_date"],
        )
    return None


def get_document_by_filename(filename: str) -> Document | None:
    """Get a document by its filename"""
    if not filename:
        raise ValueError("Filename must be provided.")
    result = execute_neo4j_query(
        "MATCH (d:Document {filename: $filename}) RETURN d;",
        parameters={"filename": filename},
    )
    if result:
        doc = result[0]["d"]
        return Document(
            identifier=doc["id"],
            filename=doc["filename"],
            path=doc["path"],
            processed=doc["processed"],
            upload_date=doc["upload_date"],
        )
    return None


def get_documents_by_filename_like(
    filename: str, page: int | None = None, limit: int | None = None
) -> list[Document]:
    """Get documents by a partial filename match"""
    if not filename:
        raise ValueError("Filename must be provided.")

    if page is not None or limit is not None:
        result = execute_neo4j_query(
            "MATCH (d:Document) WHERE tolower(d.filename) CONTAINS tolower($filename) RETURN d SKIP $skip LIMIT $limit;",
            parameters={
                "filename": filename,
                "skip": (page - 1) * limit,
                "limit": limit,
            },
        )
    else:
        result = execute_neo4j_query(
            "MATCH (d:Document) WHERE tolower(d.filename) CONTAINS tolower($filename) RETURN d;",
            parameters={"filename": filename},
        )
    return (
        [
            Document(
                identifier=doc["d"]["id"],
                filename=doc["d"]["filename"],
                path=doc["d"]["path"],
                processed=doc["d"]["processed"],
                upload_date=doc["d"]["upload_date"],
            )
            for doc in result
        ]
        if result
        else []
    )


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


def update_document(
    document_id: str,
    filename: str | None = None,
    document_path: str | None = None,
    processed: bool | None = None,
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


def set_text_of_document(
    document_id: str, text: str | None = None, mined_text: str | None = None
) -> None:
    """Set the text of a document"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    if text is None and mined_text is None:
        raise ValueError("Either text or mined_text must be provided.")

    set_clause = []
    parameters = {"id": document_id}
    if text is not None:
        set_clause.append("d.text = $text")
        parameters["text"] = text
    if mined_text is not None:
        set_clause.append("d.mined_text = $mined_text")
        parameters["mined_text"] = mined_text

    set_clause_str = ", ".join(set_clause)
    execute_neo4j_query(
        f"MATCH (d:Document {{id: $id}}) SET {set_clause_str};",
        parameters=parameters,
    )


def set_document_processed(document_id: str) -> None:
    """Mark a document as processed"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    execute_neo4j_query(
        "MATCH (d:Document {id: $id}) SET d.processed = true;",
        parameters={"id": document_id},
    )


def delete_document(document_id: str) -> None:
    """Delete a document by its ID"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    execute_neo4j_query(
        "MATCH (d:Document {id: $id}) DETACH DELETE d;",
        parameters={"id": document_id},
    )

# =================================================
# Document Topic Management Functions
# =================================================

def get_document_topics_by_id(document_id: str) -> list[DocumentTopic]:
    """Get topics associated with a document by its ID"""
    if not document_id:
        raise ValueError("Document ID must be provided.")
    result = execute_neo4j_query(
        "MATCH (d:Document {id: $id})-[l:HAS_TOPIC]->(t:Topic) RETURN t as topic, l.weight as weight;",
        parameters={"id": document_id},
    )
    return (
        [
            DocumentTopic(
                topic_id=topic["topic"]["id"],
                name=topic["topic"]["name"],
                words=json.loads(topic["topic"]["words"]),
                weight=topic["weight"],
                description=topic["topic"]["description"],
            )
            for topic in result
        ]
        if result
        else []
    )


def link_document_to_topic(
    document_id: str, topic_id: str, weight: float = 1.0
) -> None:
    """Link a document to a topic with a specified weight"""
    if not document_id or not topic_id:
        raise ValueError("Document ID and Topic ID must be provided.")
    execute_neo4j_query(
        """
        OPTIONAL MATCH (d:Document {id: $document_id})
        OPTIONAL MATCH (t:Topic {id: $topic_id})
        WITH d, t
        WHERE d IS NOT NULL AND t IS NOT NULL
        CREATE (d)-[l:HAS_TOPIC {weight: $weight}]->(t);
        """,
        parameters={"document_id": document_id, "topic_id": topic_id, "weight": weight},
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

# =================================================
# Chunk Management Functions
# =================================================

def create_chunks_embedding_index() -> None:
    """Recreate the index for chunk embeddings"""
    execute_neo4j_query(
        """
        CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
        FOR (c:Chunk) ON c.embedding
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }}
        """,
    )


def create_document_chunks(
    document_id: str, chunks: list[str], embedding: list[list[float]] | None = None
) -> None:
    """Create chunks for a document"""
    if not document_id or not chunks:
        raise ValueError("Document ID and chunks must be provided.")

    if get_document_by_id(document_id) is None:
        raise ValueError("Document not found.")

    if len(chunks) != len(embedding):
        print("Chunks and embeddings must have the same length (chunks: %d, embeddings: %d)", len(chunks), len(embedding))
        return

    for i, chunk in enumerate(chunks):
        chunk_id = f"{document_id}_chunk_{i}"
        # Create the chunk node
        execute_neo4j_query(
            "CREATE (c:Chunk {id: $id, text: $text, embedding: $embedding});",
            parameters={
                "id": chunk_id,
                "text": chunk,
                "embedding": json.dumps(embedding[i]) if embedding else None,
            },
        )
        # Link the chunk to the document
        execute_neo4j_query(
            """
            OPTIONAL MATCH (d:Document {id: $document_id})
            OPTIONAL MATCH (c:Chunk {id: $chunk_id})
            WITH d, c
            WHERE d IS NOT NULL AND c IS NOT NULL
            CREATE (d)-[:HAS_CHUNK]->(c);
            """,
            parameters={"document_id": document_id, "chunk_id": chunk_id},
        )
        # Embedding index is automatically updated in Neo4j on chunk creation
