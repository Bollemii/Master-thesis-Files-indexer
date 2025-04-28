import re
from langchain.text_splitter import CharacterTextSplitter


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
