import os
from passlib.context import CryptContext
from sqlmodel import SQLModel, create_engine, Session, select
from app.models import Document, User
from app.utils.space_word import get_pdf_title, space_between_word

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
engine = create_engine(DATABASE_URL)

DOCUMENT_STORAGE_PATH = os.getenv("DOCUMENT_STORAGE_PATH", "./documents")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def add_existing_documents():
    with Session(engine) as session:
        for file_path in os.listdir(DOCUMENT_STORAGE_PATH):
            complete_file_path = os.path.join(DOCUMENT_STORAGE_PATH, file_path)

            if os.path.isdir(complete_file_path):
                continue
            if file_path.startswith("."):
                continue

            base_filename = os.path.splitext(file_path)[0]
            spaced_filename = space_between_word(base_filename)

            if not session.exec(
                select(Document).where(Document.filename == spaced_filename)
            ).first():
                document = Document(filename=spaced_filename, path=complete_file_path)
                session.add(document)
                session.commit()
                session.refresh(document)

    session.close()


def create_admin_user():
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.username == "admin")).first()
        if not admin:
            admin = User(
                username="admin",
                hashed_password=pwd_context.hash("admin"),
                is_superuser=True,
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
    session.close()
