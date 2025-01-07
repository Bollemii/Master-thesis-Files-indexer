import os
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session, SQLModel, create_engine
from .main import app, get_session, Document

# FILE: app/test_main.py


# Create a test database
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Override the get_session dependency to use the test database
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# Create the test client
client = TestClient(app)

# Create the database and tables
SQLModel.metadata.create_all(engine)

@pytest.fixture(scope="module",autouse=True)
def run_around_tests():
    # Setup: create tables
    SQLModel.metadata.create_all(engine)
    yield
    # Teardown: drop tables
    SQLModel.metadata.drop_all(engine)
    if os.path.exists("test.db"):
        os.remove("test.db")

@pytest.mark.anyio
async def test_upload_document():
    file_path = "test_document.txt"
    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(file_path, "rb") as f:
            response = await client.post("/documents/", files={"file": f})

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_document.txt"
    assert "id" in data

    os.remove(file_path)

@pytest.mark.anyio
async def test_get_document():
    # First, upload a document
    file_path = "test_document.txt"
    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(file_path, "rb") as f:
            response = await client.post("/documents/", files={"file": f})

    assert response.status_code == 200
    data = response.json()
    document_id = data["id"]

    # Now, retrieve the document by ID
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        get_response = await client.get(f"/documents/{document_id}")

    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["document"]["id"]== document_id
    assert get_data["document"]["filename"] == "test_document.txt"

    os.remove(file_path)

@pytest.mark.anyio
async def test_list_documents():
    # First, upload a document
    file_path = "test_document.txt"
    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(file_path, "rb") as f:
            await client.post("/documents/", files={"file": f})

    # Now, list all documents
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/documents/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    os.remove(file_path)

@pytest.mark.anyio
async def test_process_document():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/documents/process")
    
    assert response.status_code == 200
    # Add more assertions when the process_document function is implemented