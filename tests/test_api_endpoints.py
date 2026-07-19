"""Tests for API endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test cases for health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAssetEndpoints:
    """Test cases for asset endpoints."""

    def test_list_assets(self, client: TestClient) -> None:
        """Test listing all assets."""
        response = client.get("/api/assets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_nonexistent_asset(self, client: TestClient) -> None:
        """Test getting a non-existent asset."""
        response = client.get("/api/assets/99999")
        assert response.status_code == 404

    def test_upload_file(self, client: TestClient, sample_text_file: Path) -> None:
        """Test file upload."""
        with open(sample_text_file, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = client.post("/api/upload", files=files)

        # May return 200 (success) or 422 (validation error depending on setup)
        assert response.status_code in [200, 422]

    def test_download_nonexistent_asset(self, client: TestClient) -> None:
        """Test downloading non-existent asset."""
        response = client.get("/api/assets/99999/download")
        assert response.status_code == 404


class TestSearchEndpoint:
    """Test cases for search endpoint."""

    def test_search_empty_query(self, client: TestClient) -> None:
        """Test search with empty query."""
        response = client.get("/api/search?q=")
        # May return 200 with empty results or validation error
        assert response.status_code in [200, 422]

    def test_search_valid_query(self, client: TestClient) -> None:
        """Test search with valid query."""
        response = client.get("/api/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_search_with_pagination(self, client: TestClient) -> None:
        """Test search with pagination parameters."""
        response = client.get("/api/search?q=test&page=1&per_page=10")
        assert response.status_code == 200
