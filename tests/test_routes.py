"""
Integration tests for FastAPI routes.

Tests verify all REST API endpoints work correctly with:
- File upload
- Asset retrieval and listing
- Search functionality
- Error handling
"""

import json
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from src.app.main import app
from src.core.database import Base, SessionLocal, engine, get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    
    # Override get_db dependency
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_text_file() -> bytes:
    """Create sample text file content."""
    return b"This is a sample document for testing upload functionality."


@pytest.fixture
def sample_image_file() -> bytes:
    """Create sample image file content."""
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    return img_bytes.getvalue()


@pytest.fixture
def mock_ai_service(db_session: Session) -> MagicMock:
    """Mock AIService to prevent calling OpenAI API in all tests."""
    patcher = patch("src.services.asset_service.AIService")
    mock_ai = patcher.start()
    mock_instance = MagicMock()
    # Mock generate_metadata to return empty metadata
    mock_instance.generate_metadata.return_value = (None, None, None)
    mock_ai.return_value = mock_instance
    yield mock_instance
    patcher.stop()


# ============================================================================
# Health Check Tests
# ============================================================================


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check_success(self, db_session: Session) -> None:
        """Test health check returns healthy status."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


# ============================================================================
# Upload Tests
# ============================================================================


class TestUpload:
    """Tests for file upload endpoint."""

    def test_upload_text_file(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes) -> None:
        """Test uploading a text file."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", sample_text_file)},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["asset"]["filename"] == "test.txt"
        assert data["asset"]["file_type"] == "text"

    def test_upload_image_file(self, db_session: Session, mock_ai_service: MagicMock, sample_image_file: bytes) -> None:
        """Test uploading an image file."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.jpg", sample_image_file)},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["asset"]["filename"] == "test.jpg"
        assert data["asset"]["file_type"] == "image"

    def test_upload_no_filename(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes) -> None:
        """Test upload fails without filename."""
        # FastAPI returns 422 validation error for empty filename
        response = client.post(
            "/api/upload",
            files={"file": ("", sample_text_file)},
        )

        assert response.status_code in [400, 422]  # Either 400 or 422 validation error

    def test_upload_empty_file(self, db_session: Session, mock_ai_service: MagicMock) -> None:
        """Test upload fails with empty file."""
        response = client.post(
            "/api/upload",
            files={"file": ("empty.txt", b"")},
        )

        assert response.status_code == 400

    def test_upload_unsupported_type(self, db_session: Session, mock_ai_service: MagicMock) -> None:
        """Test upload fails with unsupported file type."""
        response = client.post(
            "/api/upload",
            files={"file": ("file.xyz", b"content")},
        )

        assert response.status_code == 400


# ============================================================================
# Asset Retrieval Tests
# ============================================================================


class TestAssetRetrieval:
    """Tests for asset retrieval endpoints."""

    def test_list_assets_empty(self, db_session: Session) -> None:
        """Test listing assets when none exist."""
        response = client.get("/api/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["assets"]) == 0

    def test_list_assets_with_pagination(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes) -> None:
        """Test listing assets with pagination."""
        # Upload multiple files
        for i in range(5):
            client.post(
                "/api/upload",
                files={"file": (f"file{i}.txt", sample_text_file)},
            )

        # Test page 1
        response = client.get("/api/assets?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["assets"]) == 2
        assert data["page"] == 1

    def test_get_asset_by_id(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes) -> None:
        """Test retrieving a specific asset."""
        # Upload a file
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.txt", sample_text_file)},
        )
        asset_id = upload_response.json()["asset"]["id"]

        # Retrieve it
        response = client.get(f"/api/assets/{asset_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == asset_id
        assert data["filename"] == "test.txt"

    def test_get_asset_not_found(self, db_session: Session, mock_ai_service: MagicMock) -> None:
        """Test retrieving non-existent asset."""
        response = client.get("/api/assets/9999")

        assert response.status_code == 404

    def test_download_asset(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes) -> None:
        """Test downloading an asset file."""
        # Upload a file
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.txt", sample_text_file)},
        )
        asset_id = upload_response.json()["asset"]["id"]

        # Download it
        response = client.get(f"/api/assets/{asset_id}/download")
        assert response.status_code == 200
        assert response.headers["content-disposition"]

    def test_download_asset_not_found(self, db_session: Session, mock_ai_service: MagicMock) -> None:
        """Test downloading non-existent asset."""
        response = client.get("/api/assets/9999/download")

        assert response.status_code == 404


# ============================================================================
# Delete Tests
# ============================================================================


class TestDelete:
    """Tests for asset deletion endpoint."""

    def test_delete_asset(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes) -> None:
        """Test deleting an asset."""
        # Upload a file
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.txt", sample_text_file)},
        )
        asset_id = upload_response.json()["asset"]["id"]

        # Delete it
        response = client.delete(f"/api/assets/{asset_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/assets/{asset_id}")
        assert get_response.status_code == 404

    def test_delete_asset_not_found(self, db_session: Session, mock_ai_service: MagicMock) -> None:
        """Test deleting non-existent asset."""
        response = client.delete("/api/assets/9999")

        assert response.status_code == 404


# ============================================================================
# Search Tests
# ============================================================================


class TestSearch:
    """Tests for search endpoint."""

    def test_search_no_results(self, db_session: Session) -> None:
        """Test search with no results."""
        response = client.get("/api/search?q=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["results"]) == 0

    def test_search_with_results(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes) -> None:
        """Test search returning results."""
        # Update mock to return metadata with searchable tags
        mock_ai_service.generate_metadata.return_value = (
            "A Python programming document",
            '["python", "programming", "tutorial"]',
            '["python", "code", "learning"]'
        )
        
        # Upload file
        client.post(
            "/api/upload",
            files={"file": ("python_document.txt", b"This is about programming")},
        )

        # Search by keyword in metadata
        response = client.get("/api/search?q=python")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["results"]) >= 1

    def test_search_pagination(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes) -> None:
        """Test search with pagination."""
        # Upload multiple files
        for i in range(5):
            client.post(
                "/api/upload",
                files={"file": (f"file{i}.txt", b"searchable content here")},
            )

        # Search page 1
        response = client.get("/api/search?q=searchable&page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2

    def test_search_missing_query(self, db_session: Session) -> None:
        """Test search fails without query."""
        response = client.get("/api/search")

        assert response.status_code == 422  # Validation error


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_workflow(self, db_session: Session, mock_ai_service: MagicMock, sample_text_file: bytes, sample_image_file: bytes) -> None:
        """Test complete workflow: upload, retrieve, search, delete."""
        # Upload text file
        text_response = client.post(
            "/api/upload",
            files={"file": ("document.txt", sample_text_file)},
        )
        assert text_response.status_code == 201
        text_asset_id = text_response.json()["asset"]["id"]

        # Upload image file
        image_response = client.post(
            "/api/upload",
            files={"file": ("image.jpg", sample_image_file)},
        )
        assert image_response.status_code == 201
        image_asset_id = image_response.json()["asset"]["id"]

        # List assets
        list_response = client.get("/api/assets")
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 2

        # Get specific asset
        get_response = client.get(f"/api/assets/{text_asset_id}")
        assert get_response.status_code == 200

        # Search for assets
        search_response = client.get("/api/search?q=document")
        assert search_response.status_code == 200
        # May or may not have results depending on AI metadata generation

        # Delete asset
        delete_response = client.delete(f"/api/assets/{text_asset_id}")
        assert delete_response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/assets/{text_asset_id}")
        assert get_response.status_code == 404

    def test_api_documentation(self, db_session: Session) -> None:
        """Test that API documentation is available."""
        # OpenAPI schema
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/upload" in schema["paths"]
        assert "/api/assets" in schema["paths"]
        assert "/api/search" in schema["paths"]

    def test_root_endpoint(self, db_session: Session) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Knowledge Management System"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
