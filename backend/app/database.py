import os
from sqlmodel import SQLModel, create_engine, Session, select
from app.models import Document
from app.utils.space_word import space_between_word

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
        for file_path in os.listdir(DOCUMENT_STORAGE_PATH):
            file_name = os.path.splitext(file_path)[0]
            spaced_filename = space_between_word(file_name)
            if not session.exec(select(Document).where(Document.filename == file_name)).first():
                document = Document(filename=spaced_filename,
                                    path=os.path.join(DOCUMENT_STORAGE_PATH, file_path))
                session.add(document)
                session.commit()
                session.refresh(document)

    session.close()