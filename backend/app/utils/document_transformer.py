import re
from langchain.text_splitter import CharacterTextSplitter

from app.config import settings
from app.TopicModeling.miner_v2 import Miner
from app.TopicModeling.Reader import process_single_file
from app.TopicModeling.topic_modeling_v3 import delete_eol

LIBREOFFICE_PATH = settings.LIBREOFFICE_PATH
if not LIBREOFFICE_PATH:
    raise ValueError("LIBREOFFICE_PATH must be set in environment variables.")
TESSERACT_PATH = settings.TESSERACT_PATH
if not TESSERACT_PATH:
    raise ValueError("TESSERACT_PATH must be set in environment variables.")

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
    mined_content = Miner().mine_text(cleaned_content)
    return cleaned_content, mined_content
