import logging
from typing import List, Tuple
from ollama import Client, ResponseError

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_LLM_MODEL = settings.OLLAMA_LLM_MODEL
OLLAMA_EMBEDDING_MODEL = settings.OLLAMA_EMBEDDING_MODEL
OLLAMA_TIMEOUT = settings.OLLAMA_TIMEOUT

ollama_client = Client(
    host=OLLAMA_BASE_URL,
    timeout=(
        OLLAMA_TIMEOUT if OLLAMA_TIMEOUT > 0 else None
    ),  # Set timeout to negative to disable it
)


def generate_name_for_topic(topic_words: List[Tuple[str, float]]) -> str:
    """Generates a name for a single topic using the configured Ollama model."""
    if not OLLAMA_BASE_URL or not OLLAMA_LLM_MODEL:
        logger.warning("Ollama URL or model not configured. Skipping naming.")
        return "Unnamed Topic"

    top_words = [word for word, _ in topic_words]
    if not top_words:
        return "Empty Topic"

    prompt = (
        f"Generate a concise (2-4 words) descriptive name for a topic "
        f"characterized by these keywords: {', '.join(top_words)}."
        f"Only output the topic name."
    )

    print("Prompt:", prompt)

    try:
        logger.info(
            "Requesting topic name with model %s for words: %s",
            OLLAMA_LLM_MODEL,
            top_words,
        )

        response = ollama_client.generate(
            model=OLLAMA_LLM_MODEL,
            prompt=prompt,
            stream=False,
        )

        generated_name = (
            response.get("response", "").strip().replace('"', "").split("\n")[0]
        )

        if not generated_name:
            logger.warning("Ollama returned an empty name for words: %s", top_words)
            return "Unnamed Topic"

        logger.info("Generated name: '%s' for words: %s", generated_name, top_words)
        return generated_name

    except ResponseError as e:
        logger.error("Ollama error: %s", e)
        return "Error: Naming Failed"
    except Exception as e:
        logger.error("Error processing Ollama response: %s", e)
        return "Error: Processing Failed"


def generate_embedding_for_texts(texts: list[str]) -> list[list[float]]:
    """Generates an embedding for a given text using the configured Ollama model."""
    if not OLLAMA_BASE_URL or not OLLAMA_EMBEDDING_MODEL:
        logger.warning(
            "Ollama URL or embedding model not configured. Skipping embedding."
        )
        return []

    try:
        logger.info(
            "Requesting embedding with model %s for %s texts",
            OLLAMA_EMBEDDING_MODEL,
            len(texts),
        )

        response = ollama_client.embed(
            model=OLLAMA_EMBEDDING_MODEL,
            input=texts,
        )
        embedding = response.get("embeddings", [])

        if not isinstance(embedding, list):
            logger.error("Ollama returned an invalid embedding format: %s", embedding)
            return []

        return embedding

    except ResponseError as e:
        logger.error("Ollama error: %s", e)
        return []
    except Exception as e:
        logger.error("Error processing Ollama response: %s", e)
        return []


def answer_question_with_context(
    question: str, context: list[str], history: list[(str, str)] | None = None
) -> str:
    """Generates an answer to a question using the configured Ollama model."""
    if not OLLAMA_BASE_URL or not OLLAMA_LLM_MODEL:
        logger.warning("Ollama URL or model not configured. Skipping answering.")
        return "Ollama URL or model not configured."

    if not question or not context:
        logger.warning("Question or context is empty. Skipping answering.")
        return "Question or context is empty."

    prompt = (
        f"Given the conversation history with the user:\n{history}\n\n"
        f"He asked the following question:\n{question}\n\n"
        f"Based on the context provided:\n{context}\n\n"
        f"Please provide a detailed answer to the question above using the context.\n\n"
        f"Only output the answer, do not include any other text.\n\n"
        f"If the context is not sufficient to answer the question, please say 'I don't know'.\n\n"
    )

    try:
        logger.info(
            "Requesting answer with model %s for question: %s",
            OLLAMA_LLM_MODEL,
            question,
        )

        response = ollama_client.generate(
            model=OLLAMA_LLM_MODEL,
            prompt=prompt,
            stream=False,
        )

        answer = response.get("response", "").strip()

        if not answer:
            logger.warning("Ollama returned an empty answer for question: %s", question)
            return "No answer generated."

        logger.info("Generated answer: '%s' for question: %s", answer, question)
        return answer

    except ResponseError as e:
        logger.error("Ollama error: %s", e)
        return "Error: Answering Failed"
    except Exception as e:
        logger.error("Error processing Ollama response: %s", e)
        return "Error: Processing Failed"
