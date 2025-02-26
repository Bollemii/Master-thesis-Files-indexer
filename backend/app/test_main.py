import os
import json
from unittest.mock import MagicMock, patch
import pytest
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.exc import OperationalError
from app.main import app
from app.database import get_session
from app.models import User

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
client = TestClient(app, base_url="http://test")

@pytest.fixture(scope="module",autouse=True)
def run_around_tests():
    # Setup: create tables and admin
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        from app.utils.security import get_password_hash
        admin = session.exec(select(User).where(User.username == "admin")).first()
        if not admin:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin"),
                is_superuser=True
            )
            session.add(admin)
            session.commit()

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

@pytest.fixture
def create_pdf_file():
    """Create a temporary PDF file for testing"""
    pdf_path = "test_document.pdf"
    c = canvas.Canvas(pdf_path)
    c.drawString(100, 750, "Test PDF Document")
    c.save()
    yield pdf_path
    # Cleanup
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

@pytest.fixture
def cleanup_files():
    """Fixture to clean up test files"""
    yield
    files_to_clean = [
        "./openapi.json",
        "./documents/test_document.txt",
        "./documents/test_document.pdf"
    ]
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            os.remove(file_path)

@pytest.mark.anyio
async def test_upload_document(auth_headers):
    file_path = "test_document.txt"
    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(file_path, "rb") as f:
            response = await ac.post(
                "/documents/",
                files={"file": f},
                headers=auth_headers
            )

    print(response.json())
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "Test Document"
    assert "id" in data

    os.remove(file_path)

@pytest.mark.anyio
async def test_get_document(auth_headers):
    file_path = "test_document.txt"
    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with open(file_path, "rb") as f:
            response = await ac.post(
                "/documents/",
                files={"file": f},
                headers=auth_headers
            )

    assert response.status_code == 201
    data = response.json()
    document_id = data["id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        get_response = await ac.get(
            f"/documents/{document_id}",
            headers=auth_headers
        )

    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == document_id
    assert get_data["filename"] == "Test Document"

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
    with patch("app.routers.documents.process_manager.is_running") as mock_is_running, \
         patch("app.routers.documents.process_manager.run_process") as mock_run_process:
        mock_run_process.return_value = None
        mock_is_running.return_value = False
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/documents/process",
                headers=auth_headers
            )
    
        assert response.status_code == 202
        assert response.json()["message"] == "Processing started"

        mock_run_process.assert_called_once()

@pytest.mark.anyio
async def test_document_preview(auth_headers, create_pdf_file):
    # Use fixture to create PDF file
    file_path = create_pdf_file
    
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
            assert preview_response.headers["content-type"] == "image/webp"

@pytest.mark.anyio
async def test_lifespan():
    """Test the lifespan context manager"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/docs")
        assert response.status_code == 200
        
    # Verify OpenAPI file was created
    # assert os.path.exists("./openapi.json")
    # with open("./openapi.json") as f:
    #     openapi_spec = json.load(f)
    #     assert openapi_spec["info"]["title"] == "Document Processing API"

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
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

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
        print(response.json())
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.anyio
async def test_unauthorized_access():
    """Test unauthorized access to protected endpoints"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/documents/process")
        assert response.status_code == 401

@pytest.mark.anyio
async def test_invalid_document_id(auth_headers):
    """Test handling of invalid document ID"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/documents/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        print(response.json())
        assert response.status_code == 404

@pytest.mark.anyio
async def test_invalid_file_upload(auth_headers):
    """Test handling of invalid file upload"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/documents/", files={}, headers=auth_headers)
        assert response.status_code == 422

@pytest.mark.anyio
async def test_database_connection(auth_headers):
    """Test database connection handling"""
    # Save original engine
    original_engine = app.dependency_overrides[get_session]
    
    def mock_bad_db_session():
        mock_session = MagicMock()
        for method_name in ['exec', 'query', 'get', 'add', 'commit']:
            getattr(mock_session, method_name).side_effect = Exception("Mock DB Error")
        return mock_session
    
    app.dependency_overrides[get_session] = lambda: mock_bad_db_session()
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/documents/", headers=auth_headers)
            assert response.status_code in [500, 503, 422, 404]
    finally:    
        app.dependency_overrides[get_session] = original_engine

@pytest.mark.usefixtures("cleanup_files")
class TestMainIntegration:
    """Integration tests for main application"""
    
    @pytest.mark.anyio
    async def test_full_document_workflow(self):
        """Test complete document workflow: upload, process, retrieve"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Login as admin
            auth_response = await ac.post("/token", 
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
            assert upload_response.status_code == 201
            doc_id = upload_response.json()["id"]
            
            # Process document
            with patch("app.routers.documents.process_manager.is_running") as mock_is_running, \
                 patch("app.routers.documents.process_manager.run_process") as mock_run_process:
                mock_is_running.return_value = False  # This prevents the 409 Conflict
                mock_run_process.return_value = None
                
                process_response = await ac.post("/documents/process",
                    headers=headers
                )
                assert process_response.status_code == 202

                mock_is_running.assert_called_once()
                mock_run_process.assert_called_once()
            
            # Retrieve processed document
            get_response = await ac.get(f"/documents/{doc_id}",
                headers=headers
            )
            assert get_response.status_code == 200
            
            # Clean up
            os.remove("test_document.txt")