import os
from multiprocessing import Pool, cpu_count
from passlib.context import CryptContext

from app.config import settings
from app.database.documents import get_all_documents, create_chunks_embedding_index
from app.database.users import get_all_users, create_user
from app.utils.document_transformer import preprocess_document

DOCUMENT_STORAGE_PATH = settings.DOCUMENT_STORAGE_PATH
if not DOCUMENT_STORAGE_PATH:
    raise ValueError("DOCUMENT_STORAGE_PATH must be set in environment variables.")
os.makedirs(DOCUMENT_STORAGE_PATH, exist_ok=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def add_existing_documents():
    stored_documents = get_all_documents()
    dir_list = os.listdir(DOCUMENT_STORAGE_PATH)
    if not dir_list or len(dir_list)-1 <= len(stored_documents): # -1 for previews folder
        print("No new documents to add")
        return

    print("Adding existing documents, this may take a while...")

    tasks = []
    for file_path in dir_list:
        complete_file_path = os.path.join(DOCUMENT_STORAGE_PATH, file_path)

        if os.path.isdir(complete_file_path):
            continue
        if file_path.startswith("."):
            continue

        tasks.append((complete_file_path, file_path, stored_documents))

    num_processes = min(cpu_count(), len(tasks))
    print(f"Processing {len(tasks)} documents using {num_processes} processes")

    with Pool(processes=num_processes) as pool:
        pool.map(_preprocess_wrapper, tasks)

    create_chunks_embedding_index()


def _preprocess_wrapper(args):
    complete_file_path, file_path, stored_documents = args
    preprocess_document(complete_file_path, file_path, stored_documents)


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
