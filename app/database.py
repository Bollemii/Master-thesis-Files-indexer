import os
from sqlmodel import SQLModel, create_engine, Session, select
from app.models import Document

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
engine = create_engine(DATABASE_URL)

DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def add_existing_documents():
    with Session(engine) as session:
        for file_name in os.listdir(DOCUMENT_STORAGE_PATH):
            if not session.exec(select(Document).where(Document.filename == file_name)).first():
                document = Document(filename=file_name, path=os.path.join(DOCUMENT_STORAGE_PATH, file_name))
                session.add(document)
                session.commit()
                session.refresh(document)

    session.close()