import os
import json
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session, SQLModel, create_engine
from .main import app
from app.database import get_session

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

@pytest.fixture
async def auth_headers():
    """Fixture to get authentication headers"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/token",
            data={
                "username": "admin",
                "password": "admin"
            }
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.anyio
async def test_upload_document(auth_headers):
    file_path = "test_document.txt"
    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "/documents/",
                files={"file": f},
                headers=auth_headers
            )

    assert response.status_code == 201  # Changed to 201 as per your API spec
    data = response.json()
    assert data["filename"] == "This Is A Test Document"
    assert "id" in data

    os.remove(file_path)

@pytest.mark.anyio
async def test_get_document(auth_headers):
    file_path = "test_document.txt"
    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "/documents/",
                files={"file": f},
                headers=auth_headers
            )

    assert response.status_code == 201
    data = response.json()
    document_id = data["id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        get_response = await client.get(
            f"/documents/{document_id}",
            headers=auth_headers
        )

    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == document_id
    assert get_data["filename"] == "This Is A Test Document"

    os.remove(file_path)

@pytest.mark.anyio
async def test_list_documents(auth_headers):
    file_path = "test_document.txt"
    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(file_path, "rb") as f:
            await client.post(
                "/documents/",
                files={"file": f},
                headers=auth_headers
            )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/documents/",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0

    os.remove(file_path)

@pytest.mark.anyio
async def test_process_document(auth_headers):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/documents/process",
            headers=auth_headers
        )
    
    assert response.status_code == 202
    assert response.json()["message"] == "Processing started"

@pytest.mark.anyio
async def test_document_preview(auth_headers):
    # First upload a PDF document
    file_path = "test_document.pdf"
    # Create a sample PDF file here
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "/documents/",
                files={"file": f},
                headers=auth_headers
            )
        
        document_id = response.json()["id"]
        
        # Test preview endpoint
        preview_response = await client.get(
            f"/documents/{document_id}/preview",
            headers=auth_headers
        )
        
        assert preview_response.status_code in [200, 404]  # 404 if preview not available
        
        if preview_response.status_code == 200:
            assert preview_response.headers["content-type"] == "image/png"

    # Cleanup
    os.remove(file_path)

@pytest.mark.anyio
async def test_lifespan():
    """Test the lifespan context manager"""
    # Test database initialization and OpenAPI file creation
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/docs")
        assert response.status_code == 200
        
    # Verify OpenAPI file was created
    assert os.path.exists("./openapi.json")
    with open("./openapi.json") as f:
        openapi_spec = json.load(f)
        assert openapi_spec["info"]["title"] == "Document Processing API"

@pytest.mark.anyio
async def test_cors():
    """Test CORS middleware configuration"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.options("/documents/", 
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "Content-Type" in response.headers["access-control-allow-headers"]

@pytest.mark.anyio
async def test_admin_user():
    """Test admin user creation and authentication"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test login with admin credentials
        response = await ac.post("/token", 
            data={
                "username": "admin",
                "password": "admin"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.anyio
async def test_unauthorized_access():
    """Test unauthorized access to protected endpoints"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/documents/process")
        assert response.status_code == 401

@pytest.mark.anyio
async def test_invalid_document_id():
    """Test handling of invalid document ID"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/documents/999999")
        assert response.status_code == 404

@pytest.mark.anyio
async def test_invalid_file_upload():
    """Test handling of invalid file upload"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/documents/", files={})
        assert response.status_code == 422

@pytest.mark.anyio
async def test_database_connection():
    """Test database connection handling"""
    # Save original engine
    original_engine = app.dependency_overrides.get(get_session, get_session)
    
    # Override with invalid database URL
    def bad_session():
        engine = create_engine("sqlite:///nonexistent/path/db.sqlite")
        with Session(engine) as session:
            yield session
    
    app.dependency_overrides[get_session] = bad_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/documents/")
        assert response.status_code == 500
    
    # Restore original engine
    app.dependency_overrides[get_session] = original_engine

@pytest.fixture
def cleanup_files():
    """Fixture to clean up test files"""
    yield
    if os.path.exists("./openapi.json"):
        os.remove("./openapi.json")
    if os.path.exists("./test_document.txt"):
        os.remove("./test_document.txt")

@pytest.mark.usefixtures("cleanup_files")
class TestMainIntegration:
    """Integration tests for main application"""
    
    @pytest.mark.anyio
    async def test_full_document_workflow(self):
        """Test complete document workflow: upload, process, retrieve"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Login as admin
            auth_response = await ac.post("/users/token", 
                data={
                    "username": "admin",
                    "password": "admin"
                }
            )
            token = auth_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create test document
            with open("test_document.txt", "w") as f:
                f.write("Test document content")
            
            # Upload document
            with open("test_document.txt", "rb") as f:
                upload_response = await ac.post("/documents/", 
                    files={"file": f},
                    headers=headers
                )
            assert upload_response.status_code == 200
            doc_id = upload_response.json()["id"]
            
            # Process document
            process_response = await ac.post(f"/documents/{doc_id}/process",
                headers=headers
            )
            assert process_response.status_code == 200
            
            # Retrieve processed document
            get_response = await ac.get(f"/documents/{doc_id}",
                headers=headers
            )
            assert get_response.status_code == 200
            assert get_response.json()["document"]["processed"] == True