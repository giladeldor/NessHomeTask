"""Tests for search service module."""

import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from src.models.asset import Asset, Metadata
from src.repositories.asset_repository import AssetRepository
from src.services.search_service import SearchService


class TestSearchService:
    """Test cases for SearchService."""

    @pytest.fixture
    def search_service(self, test_db_session: Session) -> SearchService:
        """Create SearchService instance."""
        return SearchService()

    @pytest.fixture
    def populated_database(
        self, test_db_session: Session
    ) -> tuple[Asset, Asset, Asset]:
        """Populate database with test assets."""
        # Asset 1: Text document
        asset1 = Asset(
            filename="python_guide.txt",
            file_type="text",
            file_path="/tmp/python_guide.txt",
            file_size=5000,
        )
        metadata1 = Metadata(
            asset_id=asset1.id if asset1.id else 1,
            description="Guide to Python programming",
            tags=json.dumps(["python", "programming", "guide"]),
            keywords=json.dumps(["python", "code", "tutorial"]),
            extracted_text="This guide covers Python basics, advanced features, and best practices.",
        )
        test_db_session.add(asset1)
        test_db_session.flush()
        metadata1.asset_id = asset1.id
        test_db_session.add(metadata1)

        # Asset 2: Image
        asset2 = Asset(
            filename="nature_photo.jpg",
            file_type="image",
            file_path="/tmp/nature_photo.jpg",
            file_size=250000,
        )
        metadata2 = Metadata(
            asset_id=asset2.id if asset2.id else 2,
            description="Beautiful mountain landscape with green trees",
            tags=json.dumps(["nature", "mountain", "landscape"]),
            keywords=json.dumps(["mountain", "tree", "scenic", "landscape"]),
            extracted_text=None,
        )
        test_db_session.add(asset2)
        test_db_session.flush()
        metadata2.asset_id = asset2.id
        test_db_session.add(metadata2)

        # Asset 3: PDF document
        asset3 = Asset(
            filename="research_paper.pdf",
            file_type="text",
            file_path="/tmp/research_paper.pdf",
            file_size=1000000,
        )
        metadata3 = Metadata(
            asset_id=asset3.id if asset3.id else 3,
            description="Research paper on machine learning algorithms",
            tags=json.dumps(["research", "ml", "ai"]),
            keywords=json.dumps(["machine learning", "algorithm", "neural network"]),
            extracted_text="Recent advances in deep learning have revolutionized AI applications.",
        )
        test_db_session.add(asset3)
        test_db_session.flush()
        metadata3.asset_id = asset3.id
        test_db_session.add(metadata3)

        test_db_session.commit()
        return asset1, asset2, asset3

    def test_search_by_filename(
        self, search_service: SearchService, test_db_session: Session, populated_database
    ) -> None:
        """Test searching by filename."""
        results = search_service.search("python_guide", test_db_session)
        assert len(results) > 0
        assert results[0].filename == "python_guide.txt"

    def test_search_by_description(
        self, search_service: SearchService, test_db_session: Session, populated_database
    ) -> None:
        """Test searching by description."""
        results = search_service.search("mountain", test_db_session)
        assert len(results) > 0
        assert "mountain" in results[0].metadata.description.lower()

    def test_search_by_extracted_text(
        self, search_service: SearchService, test_db_session: Session, populated_database
    ) -> None:
        """Test searching by extracted text content."""
        results = search_service.search("deep learning", test_db_session)
        assert len(results) > 0

    def test_search_case_insensitive(
        self, search_service: SearchService, test_db_session: Session, populated_database
    ) -> None:
        """Test that search is case-insensitive."""
        results_lower = search_service.search("python", test_db_session)
        results_upper = search_service.search("PYTHON", test_db_session)
        assert len(results_lower) == len(results_upper)

    def test_search_no_results(
        self, search_service: SearchService, test_db_session: Session, populated_database
    ) -> None:
        """Test search with no matching results."""
        results = search_service.search("nonexistent_query_xyz", test_db_session)
        assert len(results) == 0

    def test_search_pagination(
        self, search_service: SearchService, test_db_session: Session, populated_database
    ) -> None:
        """Test search pagination."""
        # Note: populate_database only has 3 items, but pagination should still work
        results_page1 = search_service.search(
            "guide", test_db_session, page=1, per_page=1
        )
        results_page2 = search_service.search(
            "guide", test_db_session, page=2, per_page=1
        )
        # Should have different results or empty second page
        assert isinstance(results_page1, list)
        assert isinstance(results_page2, list)
