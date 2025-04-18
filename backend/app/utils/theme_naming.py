import logging
from typing import List, Tuple

import requests
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL
OLLAMA_TIMEOUT = settings.OLLAMA_TIMEOUT


def generate_name_for_topic(topic_words: List[Tuple[str, float]]) -> str:
    """Generates a name for a single topic using the configured Ollama model."""
    if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
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

    api_url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        # "options": {"num_predict": 15},
    }

    try:
        logger.info(
            f"Requesting topic name from {api_url} with model {OLLAMA_MODEL} for words: {top_words}"
        )
        response = requests.post(api_url, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()

        result = response.json()
        generated_name = (
            result.get("response", "").strip().replace('"', "").split("\n")[0]
        )

        if not generated_name:
            logger.warning(f"Ollama returned an empty name for words: {top_words}")
            return "Unnamed Topic"

        logger.info(f"Generated name: '{generated_name}' for words: {top_words}")
        return generated_name

    except requests.exceptions.Timeout:
        logger.error(f"Timeout error contacting Ollama at {api_url}")
        return "Error: Naming Timeout"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error contacting Ollama at {api_url}: {e}")
        return "Error: Naming Failed"
    except Exception as e:
        logger.error(f"Error processing Ollama response: {e}")
        return "Error: Processing Failed"


def get_topic_names(topics_with_words: List[List[Tuple[str, float]]]) -> List[str]:
    """Generates names for a list of topics."""
    topic_names = [generate_name_for_topic(words) for words in topics_with_words]
    return topic_names
