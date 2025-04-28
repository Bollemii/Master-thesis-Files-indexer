from typing import List, Union
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Document Processing API"
    API_V1_STR: str = "/api/v1"
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = False
    # Token settings
    SECRET_KEY: str = "740b6ea71528914a03a0404f5a9573236410dd68b4c00de3913575b4aed9a924"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Database settings
    NEO4J_URL: str = "neo4j://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    DOCUMENT_STORAGE_PATH: str = "./documents"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_LLM_MODEL: str = "gemma3:4b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 60
    # Document processing settings
    LDA_NB_TOPICS: int = 5
    LDA_NB_TOP_WORDS: int = 10
    LDA_TRESHOLD_LINK: float = 0.01

    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:80",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
