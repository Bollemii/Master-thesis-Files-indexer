import os
import uuid
from unittest.mock import patch
import pytest
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session, SQLModel, create_engine, select
from app.main import app
from app.database import get_session
from app.models import Document, User
from app.utils.security import get_password_hash

pytest_plugins = ["anyio"]

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def override_get_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session

client = TestClient(app, base_url="http://test/api")


@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test"""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin"),
            is_superuser=True,
        )
        session.add(admin)
        session.commit()

    os.makedirs("./documents", exist_ok=True)
    yield

    for root, _, files in os.walk("./documents"):
        for file in files:
            if file.startswith("test_"):
                os.remove(os.path.join(root, file))

    for file in os.listdir("."):
        if file.startswith("test_") and (
            file.endswith(".txt") or file.endswith(".pdf")
        ):
            try:
                os.remove(file)
            except (FileNotFoundError, PermissionError):
                pass


@pytest.fixture(scope="session", autouse=True)
def final_cleanup():
    """Clean up after all tests are done"""
    yield
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except (FileNotFoundError, PermissionError):
            pass


@pytest.fixture
async def auth_headers():
    """Fixture to get authentication headers"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        response = await ac.post(
            "/token", data={"username": "admin", "password": "admin"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def create_pdf_file():
    """Create a temporary PDF file for testing"""
    unique_suffix = str(uuid.uuid4())[:8]
    pdf_path = f"test_document_{unique_suffix}.pdf"
    c = canvas.Canvas(pdf_path)
    c.drawString(100, 750, "Test PDF Document")
    c.save()
    yield pdf_path
    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except (FileNotFoundError, PermissionError):
            pass


@pytest.mark.anyio
async def test_upload_document(auth_headers):
    """Test uploading a document"""
    unique_suffix = str(uuid.uuid4())[:8]
    file_path = f"test_document_{unique_suffix}.txt"

    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        with open(file_path, "rb") as f:
            response = await ac.post(
                "/documents/", files={"file": f}, headers=auth_headers
            )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"].startswith("Test Document")


@pytest.mark.anyio
async def test_get_document(auth_headers):
    """Test retrieving a document"""
    unique_suffix = str(uuid.uuid4())[:8]
    file_path = f"test_document_{unique_suffix}.txt"

    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        with open(file_path, "rb") as f:
            upload_response = await ac.post(
                "/documents/", files={"file": f}, headers=auth_headers
            )

    assert upload_response.status_code == 201
    data = upload_response.json()
    document_id = data["id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        get_response = await ac.get(f"/documents/{document_id}", headers=auth_headers)

    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == document_id


@pytest.mark.anyio
async def test_list_documents(auth_headers):
    """Test listing documents"""
    unique_suffix = str(uuid.uuid4())[:8]
    file_path = f"test_document_{unique_suffix}.txt"

    with open(file_path, "w") as f:
        f.write("This is a test document.")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as client:
        with open(file_path, "rb") as f:
            await client.post("/documents/", files={"file": f}, headers=auth_headers)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as client:
        response = await client.get("/documents/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0


@pytest.mark.anyio
async def test_process_document(auth_headers):
    """Test document processing with mocked process manager"""
    with patch(
        "app.routers.documents.process_manager.is_running"
    ) as mock_is_running, patch(
        "app.routers.documents.process_manager.run_process"
    ) as mock_run_process:
        mock_is_running.return_value = False
        mock_run_process.return_value = None

        unique_suffix = str(uuid.uuid4())[:8]
        file_path = f"test_document_{unique_suffix}.txt"

        with open(file_path, "w") as f:
            f.write("This is a test document.")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test/api"
        ) as client:
            with open(file_path, "rb") as f:
                await client.post(
                    "/documents/", files={"file": f}, headers=auth_headers
                )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test/api"
        ) as ac:
            response = await ac.post("/documents/process", headers=auth_headers)

        if response.status_code == 500:
            print(f"Process error: {response.json()}")

        assert response.status_code == 202
        assert response.json()["message"] == "Processing started"

        mock_is_running.assert_called_once()
        mock_run_process.assert_called_once()


@pytest.mark.anyio
async def test_document_preview(auth_headers, create_pdf_file):
    """Test document preview generation"""
    file_path = create_pdf_file

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "/documents/", files={"file": f}, headers=auth_headers
            )

        document_id = response.json()["id"]

        preview_response = await client.get(
            f"/documents/{document_id}/preview", headers=auth_headers
        )

        assert preview_response.status_code in [200, 404]

        if preview_response.status_code == 200:
            content_type = preview_response.headers["content-type"]
            assert content_type in ["image/webp", "image/png", "image/jpeg"]


@pytest.mark.anyio
async def test_lifespan():
    """Test the lifespan context manager"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/docs")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_cors():
    """Test CORS middleware configuration"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        response = await ac.options(
            "/documents/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers


@pytest.mark.anyio
async def test_admin_user():
    """Test admin user creation and authentication"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        response = await ac.post(
            "/token", data={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


@pytest.mark.anyio
async def test_unauthorized_access():
    """Test unauthorized access to protected endpoints"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        response = await ac.post("/documents/process")
        assert response.status_code == 401


@pytest.mark.anyio
async def test_invalid_document_id(auth_headers):
    """Test handling of invalid document ID"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        response = await ac.get(
            "/documents/00000000-0000-0000-0000-000000000000", headers=auth_headers
        )
        assert response.status_code == 404


@pytest.mark.anyio
async def test_invalid_file_upload(auth_headers):
    """Test handling of invalid file upload"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        response = await ac.post("/documents/", files={}, headers=auth_headers)
        assert response.status_code == 422


@pytest.mark.anyio
async def test_delete_document(auth_headers):
    """Test deleting a document"""
    unique_suffix = str(uuid.uuid4())[:8]
    file_path = f"test_document_{unique_suffix}.txt"

    with open(file_path, "w") as f:
        f.write("This is a test document for deletion.")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as client:
        with open(file_path, "rb") as f:
            upload_response = await client.post(
                "/documents/", files={"file": f}, headers=auth_headers
            )

        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]

        delete_response = await client.delete(
            f"/documents/{document_id}", headers=auth_headers
        )

        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Document deleted"

        get_response = await client.get(
            f"/documents/{document_id}", headers=auth_headers
        )
        assert get_response.status_code == 404


@pytest.mark.anyio
async def test_update_document_filename(auth_headers):
    """Test updating a document's filename"""
    unique_suffix = str(uuid.uuid4())[:8]
    file_path = f"test_document_{unique_suffix}.txt"

    with open(file_path, "w") as f:
        f.write("This is a test document for updating.")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as client:
        with open(file_path, "rb") as f:
            upload_response = await client.post(
                "/documents/", files={"file": f}, headers=auth_headers
            )

        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]

        new_filename = f"Updated Document {unique_suffix}"
        update_response = await client.put(
            f"/documents/{document_id}/name",
            data={"name": new_filename},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["filename"] == new_filename

        get_response = await client.get(
            f"/documents/{document_id}", headers=auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["filename"] == new_filename


@pytest.mark.anyio
async def test_update_document_content(auth_headers):
    """Test updating a document's content"""
    unique_suffix = str(uuid.uuid4())[:8]
    file_path = f"test_document_{unique_suffix}.txt"
    new_file_path = f"updated_document_{unique_suffix}.txt"

    with open(file_path, "w") as f:
        f.write("This is a test document for content updating.")

    with open(new_file_path, "w") as f:
        f.write("This is the updated content for testing.")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as client:
        with open(file_path, "rb") as f:
            upload_response = await client.post(
                "/documents/", files={"file": f}, headers=auth_headers
            )

        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]

        # Check if document is processed
        get_response = await client.get(
            f"/documents/{document_id}", headers=auth_headers
        )
        assert get_response.json()["processed"] is False

        # Update the document content
        with open(new_file_path, "rb") as f:
            files = {"file": (new_file_path, f, "text/plain")}
            update_response = await client.put(
                f"/documents/{document_id}",
                files=files,
                headers=auth_headers,
            )

        assert update_response.status_code == 200

        # Verify the processed flag has been reset
        get_response_after = await client.get(
            f"/documents/{document_id}", headers=auth_headers
        )
        assert get_response_after.status_code == 200
        assert get_response_after.json()["processed"] is False

        os.remove(new_file_path)


@pytest.mark.anyio
async def test_update_nonexistent_document(auth_headers):
    """Test updating a document that doesn't exist"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as client:
        # Try to update a non-existent document
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        update_response = await client.put(
            f"/documents/{nonexistent_id}/name",
            data={"name": "This Should Fail"},
            headers=auth_headers,
        )
        print(update_response.json())
        assert update_response.status_code == 404


class TestMainIntegration:
    """Integration tests for main application"""

    @pytest.mark.anyio
    async def test_full_document_workflow(self):
        """Test complete document workflow: upload, process, retrieve"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test/api"
        ) as ac:
            auth_response = await ac.post(
                "/token", data={"username": "admin", "password": "admin"}
            )
            token = auth_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            unique_suffix = str(uuid.uuid4())[:8]
            file_path = f"test_document_{unique_suffix}.txt"
            with open(file_path, "w") as f:
                f.write("Test document content")

            with open(file_path, "rb") as f:
                upload_response = await ac.post(
                    "/documents/", files={"file": f}, headers=headers
                )
            assert upload_response.status_code == 201
            doc_id = uuid.UUID(upload_response.json()["id"])

            with patch(
                "app.routers.documents.process_manager.is_running"
            ) as mock_is_running, patch(
                "app.routers.documents.process_manager.run_process"
            ) as mock_run_process:
                mock_is_running.return_value = False
                mock_run_process.return_value = None

                process_response = await ac.post("/documents/process", headers=headers)
                assert process_response.status_code == 202
                mock_is_running.assert_called_once()
                mock_run_process.assert_called_once()

                with Session(engine) as session:
                    doc = session.exec(
                        select(Document).where(Document.id == doc_id)
                    ).first()
                    if doc:
                        doc.processed = True
                        session.add(doc)
                        session.commit()

            get_response = await ac.get(f"/documents/{doc_id}", headers=headers)
            assert get_response.status_code == 200
