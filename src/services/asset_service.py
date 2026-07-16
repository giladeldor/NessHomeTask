"""
Asset management service.

Handles asset upload, storage, and retrieval.
"""

import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.api.schemas import AssetDetailSchema, MetadataSchema
from src.core.config import settings
from src.core.exceptions import FileProcessingError
from src.repositories.asset_repository import AssetRepository
from src.services.ai_service import AIService
from src.utils.file_validator import FileValidator
from src.utils.helpers import sanitize_filename


class AssetService:
    """Service for managing assets."""

    def __init__(self, db: Session) -> None:
        """Initialize asset service."""
        self.db = db
        self.repository = AssetRepository(db)
        self.ai_service = AIService()
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def upload_asset(self, source_path: Path, original_filename: str) -> AssetDetailSchema:
        """
        Upload an asset and generate metadata.

        Flow:
        1. Validate file
        2. Save to upload directory
        3. Create asset record
        4. Generate AI metadata
        5. Store metadata (non-blocking)

        Args:
            source_path: Path to uploaded file
            original_filename: Original filename

        Returns:
            AssetDetailSchema with asset and metadata info

        Raises:
            FileValidationError: If file validation fails
            FileProcessingError: If save/processing fails
        """
        # Step 1: Validate file
        file_type, mime_type = FileValidator.validate_file(source_path)

        # Step 2: Generate destination path
        sanitized_name = sanitize_filename(original_filename)
        # We'll use database ID for unique naming, so just use original name for now
        # The ID will be appended after database insert
        destination_path = None  # Will be set after asset creation

        try:
            # Step 3: Create asset record (to get ID)
            asset = self.repository.create_asset(
                filename=original_filename,
                file_type=file_type,
                mime_type=mime_type,
                file_path="",  # Placeholder, will be updated
                file_size=int(source_path.stat().st_size),
            )

            # Now create the destination path with the asset ID
            destination_filename = f"{asset.id}_{sanitized_name}"
            destination_path = self.upload_dir / destination_filename

            # Step 4: Save file
            shutil.copy2(source_path, destination_path)

            # Step 5: Update asset file path (use absolute path)
            asset.file_path = str(destination_path.absolute())
            self.db.commit()
            self.db.refresh(asset)

            # Step 6: Generate AI metadata (non-blocking - errors don't fail upload)
            description, tags_json, keywords_json = self.ai_service.generate_metadata(
                destination_path, file_type
            )

            # Step 7: Store metadata
            metadata = None
            if description or tags_json or keywords_json:
                metadata = self.repository.create_metadata(
                    asset_id=asset.id,
                    description=description,
                    tags=tags_json,
                    keywords=keywords_json,
                )

            # Step 8: Build response
            metadata_schema = None
            if metadata:
                metadata_schema = MetadataSchema(
                    description=metadata.description,
                    tags=eval(metadata.tags) if metadata.tags else [],
                    keywords=eval(metadata.keywords) if metadata.keywords else [],
                )

            return AssetDetailSchema(
                id=asset.id,
                filename=asset.filename,
                file_type=asset.file_type,
                mime_type=asset.mime_type,
                file_size=asset.file_size,
                created_at=asset.created_at,
                metadata=metadata_schema,
            )

        except Exception as e:
            # Cleanup on error
            if destination_path and destination_path.exists():
                destination_path.unlink()
            raise FileProcessingError(f"Failed to process upload: {str(e)}")

    def get_asset(self, asset_id: int) -> Optional[AssetDetailSchema]:
        """
        Get asset with metadata.

        Args:
            asset_id: Asset ID

        Returns:
            AssetDetailSchema or None if not found
        """
        asset = self.repository.get_asset_by_id(asset_id)
        if not asset:
            return None

        # Get metadata
        metadata = None
        if asset.asset_metadata:
            metadata = MetadataSchema(
                description=asset.asset_metadata.description,
                tags=eval(asset.asset_metadata.tags) if asset.asset_metadata.tags else [],
                keywords=eval(asset.asset_metadata.keywords)
                if asset.asset_metadata.keywords
                else [],
            )

        return AssetDetailSchema(
            id=asset.id,
            filename=asset.filename,
            file_type=asset.file_type,
            mime_type=asset.mime_type,
            file_size=asset.file_size,
            created_at=asset.created_at,
            metadata=metadata,
        )

    def delete_asset(self, asset_id: int) -> bool:
        """
        Delete an asset and its file.

        Args:
            asset_id: Asset ID

        Returns:
            True if deleted, False if not found
        """
        asset = self.repository.get_asset_by_id(asset_id)
        if not asset:
            return False

        # Delete file from disk
        file_path = Path(asset.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                # Log error but continue with database deletion
                pass

        # Delete from database (cascades to metadata)
        return self.repository.delete_asset(asset_id)

    def get_asset_file_path(self, asset_id: int) -> Optional[Path]:
        """
        Get the file path for an asset.

        Args:
            asset_id: Asset ID

        Returns:
            Path to file or None if not found
        """
        asset = self.repository.get_asset_by_id(asset_id)
        if not asset:
            return None

        file_path = Path(asset.file_path)
        if file_path.exists():
            return file_path

        return None
