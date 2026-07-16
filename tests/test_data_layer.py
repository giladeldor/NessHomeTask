"""
Integration tests for database models, repository, and schemas.

These tests verify that:
1. Models are correctly configured
2. Database relationships work
3. Repository operations function properly
4. Schemas validate correctly
"""

import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from src.api.schemas import (
    AssetDetailSchema,
    AssetSchema,
    MetadataSchema,
    UploadResponseSchema,
)
from src.core.database import Base, SessionLocal, engine
from src.models.asset import Asset, Metadata
from src.repositories.asset_repository import AssetRepository


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestAssetModel:
    """Tests for Asset model."""

    def test_asset_creation(self, db_session: Session) -> None:
        """Test creating an asset record."""
        asset = Asset(
            filename="test.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="uploads/1_test.pdf",
            file_size=1024,
        )
        db_session.add(asset)
        db_session.commit()
        
        assert asset.id is not None
        assert asset.filename == "test.pdf"
        assert asset.file_type == "text"

    def test_asset_timestamps(self, db_session: Session) -> None:
        """Test that timestamps are automatically set."""
        asset = Asset(
            filename="test.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_path="uploads/1_test.jpg",
            file_size=2048,
        )
        db_session.add(asset)
        db_session.commit()
        
        assert asset.created_at is not None
        assert isinstance(asset.created_at, datetime)
        assert asset.updated_at is not None

    def test_asset_with_metadata(self, db_session: Session) -> None:
        """Test asset with related metadata."""
        asset = Asset(
            filename="document.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="uploads/1_document.pdf",
            file_size=5000,
        )
        db_session.add(asset)
        db_session.flush()  # Get the ID without committing
        
        metadata = Metadata(
            asset_id=asset.id,
            description="A test document",
            tags=json.dumps(["test", "document"]),
            keywords=json.dumps(["key1", "key2"]),
        )
        db_session.add(metadata)
        db_session.commit()
        
        # Refresh and verify relationship
        db_session.refresh(asset)
        assert asset.asset_metadata is not None
        assert asset.asset_metadata.description == "A test document"


class TestMetadataModel:
    """Tests for Metadata model."""

    def test_metadata_creation(self, db_session: Session) -> None:
        """Test creating metadata."""
        asset = Asset(
            filename="test.txt",
            file_type="text",
            mime_type="text/plain",
            file_path="uploads/1_test.txt",
            file_size=500,
        )
        db_session.add(asset)
        db_session.flush()
        
        metadata = Metadata(
            asset_id=asset.id,
            description="Test metadata",
            tags=json.dumps(["tag1", "tag2"]),
            keywords=json.dumps(["kw1", "kw2"]),
        )
        db_session.add(metadata)
        db_session.commit()
        
        assert metadata.id is not None
        assert metadata.asset_id == asset.id

    def test_metadata_cascade_delete(self, db_session: Session) -> None:
        """Test that deleting an asset deletes its metadata."""
        asset = Asset(
            filename="delete_me.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="uploads/1_delete_me.pdf",
            file_size=1000,
        )
        db_session.add(asset)
        db_session.flush()
        
        metadata = Metadata(
            asset_id=asset.id,
            description="To be deleted",
        )
        db_session.add(metadata)
        db_session.commit()
        
        asset_id = asset.id
        
        # Delete asset
        db_session.delete(asset)
        db_session.commit()
        
        # Verify metadata was also deleted
        remaining_metadata = db_session.query(Metadata).filter(
            Metadata.asset_id == asset_id
        ).first()
        assert remaining_metadata is None


class TestAssetRepository:
    """Tests for AssetRepository data access layer."""

    def test_create_asset(self, db_session: Session) -> None:
        """Test creating an asset via repository."""
        repo = AssetRepository(db_session)
        
        asset = repo.create_asset(
            filename="report.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="uploads/1_report.pdf",
            file_size=3000,
        )
        
        assert asset.id is not None
        assert asset.filename == "report.pdf"

    def test_get_asset_by_id(self, db_session: Session) -> None:
        """Test retrieving an asset by ID."""
        repo = AssetRepository(db_session)
        
        asset = repo.create_asset(
            filename="test.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_path="uploads/1_test.jpg",
            file_size=2000,
        )
        
        retrieved = repo.get_asset_by_id(asset.id)
        assert retrieved is not None
        assert retrieved.filename == "test.jpg"

    def test_get_all_assets_pagination(self, db_session: Session) -> None:
        """Test retrieving all assets with pagination."""
        repo = AssetRepository(db_session)
        
        # Create multiple assets
        for i in range(5):
            repo.create_asset(
                filename=f"file{i}.txt",
                file_type="text",
                mime_type="text/plain",
                file_path=f"uploads/{i}_file{i}.txt",
                file_size=100 * (i + 1),
            )
        
        # Test pagination
        assets, total = repo.get_all_assets(skip=0, limit=3)
        assert len(assets) == 3
        assert total == 5

    def test_delete_asset(self, db_session: Session) -> None:
        """Test deleting an asset."""
        repo = AssetRepository(db_session)
        
        asset = repo.create_asset(
            filename="delete.txt",
            file_type="text",
            mime_type="text/plain",
            file_path="uploads/1_delete.txt",
            file_size=100,
        )
        
        deleted = repo.delete_asset(asset.id)
        assert deleted is True
        
        retrieved = repo.get_asset_by_id(asset.id)
        assert retrieved is None

    def test_create_metadata(self, db_session: Session) -> None:
        """Test creating metadata via repository."""
        repo = AssetRepository(db_session)
        
        asset = repo.create_asset(
            filename="doc.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="uploads/1_doc.pdf",
            file_size=2000,
        )
        
        metadata = repo.create_metadata(
            asset_id=asset.id,
            description="A PDF document",
            tags=json.dumps(["pdf", "document"]),
            keywords=json.dumps(["format", "text"]),
        )
        
        assert metadata.id is not None
        assert metadata.asset_id == asset.id

    def test_get_metadata_by_asset_id(self, db_session: Session) -> None:
        """Test retrieving metadata by asset ID."""
        repo = AssetRepository(db_session)
        
        asset = repo.create_asset(
            filename="image.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_path="uploads/1_image.jpg",
            file_size=5000,
        )
        
        repo.create_metadata(
            asset_id=asset.id,
            description="A photo",
            tags=json.dumps(["photo", "image"]),
        )
        
        metadata = repo.get_metadata_by_asset_id(asset.id)
        assert metadata is not None
        assert metadata.description == "A photo"

    def test_search_assets(self, db_session: Session) -> None:
        """Test searching assets."""
        repo = AssetRepository(db_session)
        
        # Create assets with metadata
        asset1 = repo.create_asset(
            filename="photo.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_path="uploads/1_photo.jpg",
            file_size=2000,
        )
        
        repo.create_metadata(
            asset_id=asset1.id,
            description="A person with black hair",
            tags=json.dumps(["black hair", "portrait"]),
            keywords=json.dumps(["hair", "person"]),
        )
        
        asset2 = repo.create_asset(
            filename="document.txt",
            file_type="text",
            mime_type="text/plain",
            file_path="uploads/2_document.txt",
            file_size=1000,
        )
        
        repo.create_metadata(
            asset_id=asset2.id,
            description="A document about hair care",
            tags=json.dumps(["hair", "care"]),
            keywords=json.dumps(["document", "guide"]),
        )
        
        # Search for "black hair"
        results, total = repo.search_assets("black hair", skip=0, limit=50)
        assert total == 1
        assert len(results) == 1
        assert results[0]["filename"] == "photo.jpg"

    def test_search_relevance_scoring(self, db_session: Session) -> None:
        """Test that search results are scored by relevance."""
        repo = AssetRepository(db_session)
        
        # Create asset with exact tag match
        asset1 = repo.create_asset(
            filename="photo.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_path="uploads/1_photo.jpg",
            file_size=2000,
        )
        
        repo.create_metadata(
            asset_id=asset1.id,
            tags=json.dumps(["black hair"]),  # Exact match in tags
        )
        
        # Create asset with keyword match
        asset2 = repo.create_asset(
            filename="doc.txt",
            file_type="text",
            mime_type="text/plain",
            file_path="uploads/2_doc.txt",
            file_size=1000,
        )
        
        repo.create_metadata(
            asset_id=asset2.id,
            description="Information about black hair",
            keywords=json.dumps(["black hair", "hair care"]),  # Match in keywords
        )
        
        results, _ = repo.search_assets("black hair")
        
        # Should have at least 2 results
        assert len(results) >= 2
        # First result should be the one with tag match (higher score)
        assert results[0]["filename"] == "photo.jpg"
        assert results[0]["relevance_score"] > results[1]["relevance_score"]


class TestPydanticSchemas:
    """Tests for Pydantic schema validation."""

    def test_metadata_schema(self) -> None:
        """Test MetadataSchema validation."""
        data = {
            "description": "Test description",
            "tags": ["tag1", "tag2"],
            "keywords": ["kw1", "kw2"],
        }
        schema = MetadataSchema(**data)
        
        assert schema.description == "Test description"
        assert len(schema.tags) == 2

    def test_asset_schema(self) -> None:
        """Test AssetSchema validation."""
        data = {
            "id": 1,
            "filename": "test.pdf",
            "file_type": "text",
            "mime_type": "application/pdf",
            "file_size": 1000,
            "created_at": datetime.now(),
        }
        schema = AssetSchema(**data)
        
        assert schema.id == 1
        assert schema.filename == "test.pdf"

    def test_asset_detail_schema(self) -> None:
        """Test AssetDetailSchema with metadata."""
        asset_data = {
            "id": 1,
            "filename": "test.jpg",
            "file_type": "image",
            "mime_type": "image/jpeg",
            "file_size": 2000,
            "created_at": datetime.now(),
        }
        metadata_data = {
            "description": "A test image",
            "tags": ["test"],
            "keywords": ["image"],
        }
        
        schema = AssetDetailSchema(
            **asset_data,
            metadata=MetadataSchema(**metadata_data),
        )
        
        assert schema.metadata is not None
        assert schema.metadata.description == "A test image"

    def test_upload_response_schema(self) -> None:
        """Test UploadResponseSchema."""
        asset_data = {
            "id": 1,
            "filename": "upload.pdf",
            "file_type": "text",
            "mime_type": "application/pdf",
            "file_size": 3000,
            "created_at": datetime.now(),
        }
        
        schema = UploadResponseSchema(
            success=True,
            asset=AssetSchema(**asset_data),
        )
        
        assert schema.success is True
        assert schema.asset.filename == "upload.pdf"


class TestDatabaseIntegration:
    """End-to-end integration tests."""

    def test_full_upload_workflow(self, db_session: Session) -> None:
        """Test complete upload workflow."""
        repo = AssetRepository(db_session)
        
        # Step 1: Create asset
        asset = repo.create_asset(
            filename="workflow.pdf",
            file_type="text",
            mime_type="application/pdf",
            file_path="uploads/1_workflow.pdf",
            file_size=4000,
        )
        
        # Step 2: Create metadata
        metadata = repo.create_metadata(
            asset_id=asset.id,
            description="A workflow document",
            tags=json.dumps(["workflow", "process"]),
            keywords=json.dumps(["steps", "guide"]),
        )
        
        # Step 3: Retrieve and verify
        retrieved_asset = repo.get_asset_by_id(asset.id)
        retrieved_metadata = repo.get_metadata_by_asset_id(asset.id)
        
        assert retrieved_asset.filename == "workflow.pdf"
        assert retrieved_metadata.description == "A workflow document"
        
        # Step 4: Search
        results, total = repo.search_assets("workflow")
        assert total >= 1
        assert any(r["id"] == asset.id for r in results)

    def test_multiple_assets_search(self, db_session: Session) -> None:
        """Test searching across multiple assets."""
        repo = AssetRepository(db_session)
        
        # Create multiple assets
        test_data = [
            ("photo1.jpg", "image", "A person with black hair", ["portrait"]),
            ("photo2.jpg", "image", "Another person with black hair", ["portrait"]),
            ("doc.txt", "text", "Document about black hair care", ["guide"]),
        ]
        
        for filename, file_type, description, tags in test_data:
            asset = repo.create_asset(
                filename=filename,
                file_type=file_type,
                mime_type="image/jpeg" if file_type == "image" else "text/plain",
                file_path=f"uploads/{filename}",
                file_size=1000,
            )
            repo.create_metadata(
                asset_id=asset.id,
                description=description,
                tags=json.dumps(tags + ["black hair"]),
            )
        
        # Search
        results, total = repo.search_assets("black hair")
        assert total == 3
        assert len(results) <= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
