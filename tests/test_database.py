import json

import pytest
from sqlalchemy.orm import Session

from src.models.asset import Asset, Metadata
from src.repositories.asset_repository import AssetRepository


class TestAssetRepository:
    """Test cases for AssetRepository."""

    def test_create_asset(
        self, test_db_session: Session, asset_repository: AssetRepository
    ) -> None:
        """Test creating an asset."""
        asset = asset_repository.create_asset(
            filename="test_doc.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="/tmp/test_doc.pdf",
            file_size=5000,
        )

        assert asset.id is not None
        assert asset.filename == "test_doc.pdf"
        assert asset.file_type == "text"

    def test_get_asset_by_id(
        self, test_db_session: Session, asset_repository: AssetRepository, test_asset: Asset
    ) -> None:
        """Test retrieving an asset by ID."""
        retrieved = asset_repository.get_asset_by_id(test_asset.id)

        assert retrieved is not None
        assert retrieved.id == test_asset.id
        assert retrieved.filename == test_asset.filename

    def test_get_nonexistent_asset(
        self, asset_repository: AssetRepository
    ) -> None:
        """Test retrieving non-existent asset."""
        result = asset_repository.get_asset_by_id(99999)
        assert result is None

    def test_list_all_assets(
        self, test_db_session: Session, asset_repository: AssetRepository
    ) -> None:
        """Test listing all assets."""
        # Create multiple assets
        for i in range(3):
            asset_repository.create_asset(
                filename=f"file_{i}.txt",
                file_type="text",
                mime_type="text/plain",
                file_path=f"/tmp/file_{i}.txt",
                file_size=1000 * (i + 1),
            )

        assets, total = asset_repository.get_all_assets()
        assert total >= 3

    def test_delete_asset(
        self,
        test_db_session: Session,
        asset_repository: AssetRepository,
        test_asset: Asset,
    ) -> None:
        """Test deleting an asset."""
        asset_id = test_asset.id
        asset_repository.delete_asset(asset_id)

        result = asset_repository.get_asset_by_id(asset_id)
        assert result is None

    def test_create_metadata(
        self,
        test_db_session: Session,
        asset_repository: AssetRepository,
        test_asset: Asset,
    ) -> None:
        """Test creating metadata for an asset."""
        metadata = asset_repository.create_metadata(
            asset_id=test_asset.id,
            description="Test description",
            tags=json.dumps(["tag1", "tag2"]),
            keywords=json.dumps(["keyword1", "keyword2"]),
            extracted_text="Extracted text content",
        )

        assert metadata.asset_id == test_asset.id
        assert metadata.description == "Test description"

    def test_get_metadata_by_asset_id(
        self,
        test_db_session: Session,
        asset_repository: AssetRepository,
        test_metadata: Metadata,
    ) -> None:
        """Test retrieving metadata by asset ID."""
        metadata = asset_repository.get_metadata_by_asset_id(test_metadata.asset_id)

        assert metadata is not None
        assert metadata.id == test_metadata.id
        assert metadata.description == test_metadata.description

    def test_update_metadata(
        self,
        test_db_session: Session,
        asset_repository: AssetRepository,
        test_metadata: Metadata,
    ) -> None:
        """Test updating metadata."""
        new_description = "Updated description"
        asset_repository.update_metadata(
            asset_id=test_metadata.asset_id,
            description=new_description,
        )

        updated = asset_repository.get_metadata_by_asset_id(test_metadata.asset_id)
        assert updated.description == new_description

    def test_search_assets_by_filename(
        self, test_db_session: Session, asset_repository: AssetRepository
    ) -> None:
        """Test searching assets by filename."""
        # Create test assets
        asset1 = asset_repository.create_asset(
            filename="python_guide.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="/tmp/python_guide.pdf",
            file_size=5000,
        )
        asset2 = asset_repository.create_asset(
            filename="java_guide.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="/tmp/java_guide.pdf",
            file_size=4000,
        )

        # Search
        results, total = asset_repository.search_assets("python")
        filenames = [r["filename"] for r in results]

        assert "python_guide.pdf" in filenames
