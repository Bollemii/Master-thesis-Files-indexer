import re
import os
from langchain.text_splitter import CharacterTextSplitter

from app.config import settings
from app.TopicModeling.miner_v2 import Miner
from app.TopicModeling.Reader import process_single_file
from app.TopicModeling.topic_modeling_v3 import delete_eol
from app.utils.ai_model import generate_embedding_for_texts
from app.database.documents import (
    create_document,
    set_text_of_document,
    create_document_chunks,
)
from app.database.models import Document

LIBREOFFICE_PATH = settings.LIBREOFFICE_PATH
if not LIBREOFFICE_PATH:
    raise ValueError("LIBREOFFICE_PATH must be set in environment variables.")
TESSERACT_PATH = settings.TESSERACT_PATH
if not TESSERACT_PATH:
    raise ValueError("TESSERACT_PATH must be set in environment variables.")

miner = Miner()

def space_between_word(text):
    # Replace underscores with spaces
    result = text.replace("_", " ")

    # Split on uppercase letters, numbers, and dots
    result = re.sub(
        r"([a-z])([A-Z])|([0-9])([A-Z])|([A-Z])([0-9])|\.", r"\1\3\5 \2\4\6", result
    )

    # Add space between numbers and letters
    result = re.sub(r"([a-zA-Z])([0-9])", r"\1 \2", result)

    # Add space between lowercase and numbers
    result = re.sub(r"([0-9])([a-zA-Z])", r"\1 \2", result)

    # Clean up any multiple spaces
    result = re.sub(r"\s+", " ", result)

    # Capitalize first letter of each word
    result = " ".join(
        word[0].upper() + word[1:] if word else "" for word in result.split()
    )

    return result.strip()


def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    """Split text into chunks of a specified size."""

    text_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=chunk_size,
        chunk_overlap=200,
    )

    return text_splitter.split_text(text)


def extract_document_text(file_path: str) -> str:
    """Extract text from a document."""
    config = {
        "file_path": file_path,
        "doc_reader_path": LIBREOFFICE_PATH,
        "tesseract_path": TESSERACT_PATH,
        "image_resolution": 150,
    }
    _, content, error, _, _ = process_single_file(config)
    if error:
        print(f"Error extracting text from {file_path}: {error}")
        return None
    cleaned_content = delete_eol(content)
    mined_content = miner.mine_text(cleaned_content)
    return cleaned_content, mined_content

def preprocess_document(file_path: str, filename: str, stored_documents: list) -> Document:
    """Preprocess the document by extracting text, mining it, chunking it, and generating embeddings."""
    base_filename = os.path.splitext(filename)[0]
    spaced_filename = space_between_word(base_filename)

    document_found = stored_documents and any(
        doc.filename == spaced_filename for doc in stored_documents
    )
    if not document_found:
        created_document = create_document(
            spaced_filename, file_path
        )

        # Extract text from the document
        text, mined_text = extract_document_text(file_path)
        if text is not None:
            # Save the extracted text to the database
            set_text_of_document(
                document_id=created_document.id,
                text=text,
                mined_text=mined_text,
            )
            # Prepare text for RAG
            chunks = chunk_text(text)
            embeddings = generate_embedding_for_texts(chunks)
            # Save chunks to the database
            create_document_chunks(
                document_id=created_document.id,
                chunks=chunks,
                embedding=embeddings,
            )
        else:
            print("Error: No text extracted from the document.")

        return created_document

    return document_found
