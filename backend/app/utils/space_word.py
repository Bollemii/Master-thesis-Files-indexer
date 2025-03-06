import re
import fitz


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


def get_pdf_title(file_path: str) -> str | None:
    """
    Extract title from PDF metadata.
    If metadata title is not available, return None

    Args:
        file_path (str): Path to the PDF file

    Returns:
        str | None: The PDF title if available, None otherwise
    """
    try:
        with fitz.open(file_path) as pdf:
            metadata = pdf.metadata
            # print(f"Metadata: {metadata}")
            if metadata and metadata.get("title"):
                # print(f"Title extracted from PDF metadata: {metadata['title']}")
                return metadata["title"]
        return None
    except Exception as e:
        print(f"Error extracting PDF title: {str(e)}")
        return None
