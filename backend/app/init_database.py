import os
from passlib.context import CryptContext

from app.config import settings
from app.utils.space_word import space_between_word
from app.database.documents import get_all_documents, create_document
from app.database.users import get_all_users, create_user

DOCUMENT_STORAGE_PATH = settings.DOCUMENT_STORAGE_PATH
if not DOCUMENT_STORAGE_PATH:
    raise ValueError("DOCUMENT_STORAGE_PATH must be set in environment variables.")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def add_existing_documents():
    stored_documents = get_all_documents()
    dir_list = os.listdir(DOCUMENT_STORAGE_PATH)

    if not dir_list or len(dir_list) <= len(stored_documents):
        print("No new documents to add")
        return

    print("Adding existing documents, this may take a while...")
    for file_path in dir_list:
        complete_file_path = os.path.join(DOCUMENT_STORAGE_PATH, file_path)

        if os.path.isdir(complete_file_path):
            continue
        if file_path.startswith("."):
            continue

        base_filename = os.path.splitext(file_path)[0]
        spaced_filename = space_between_word(base_filename)

        document_found = stored_documents and any(
            doc.filename == spaced_filename for doc in stored_documents
        )
        if not document_found:
            create_document(
                spaced_filename, complete_file_path
            )

def create_admin_user():
    """Create an admin user if it doesn't exist"""
    found_users = get_all_users()
    admin_found = found_users and any(
        user.username == "admin" for user in found_users
    )
    if not admin_found:
        print("Creating admin user")
        create_user(
            username="admin",
            password="admin",
            is_superuser=True,
        )
