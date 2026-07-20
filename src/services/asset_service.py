import shutil
import threading
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.api.schemas import AssetDetailSchema, MetadataSchema
from src.core.config import settings
from src.core.database import SessionLocal
from src.core.exceptions import FileProcessingError
from src.core.logging_config import get_logger
from src.repositories.asset_repository import AssetRepository
from src.services.ai_service import AIService
from src.utils.file_validator import FileValidator
from src.utils.helpers import sanitize_filename

logger = get_logger(__name__)


def backfill_extracted_text() -> None:
    """
    Backfill extracted_text for all existing text assets that are missing it.
    Runs once in a background thread at startup.
    """
    logger.info("Starting backfill of extracted_text for existing assets...")
    db = SessionLocal()
    try:
        from src.models.asset import Asset, Metadata
        from src.utils.text_extractor import TextExtractor

        # Find all text assets
        text_assets = db.query(Asset).filter(Asset.file_type == "text").all()
        repo = AssetRepository(db)
        updated = 0

        for asset in text_assets:
            # Skip if already has extracted_text
            meta = repo.get_metadata_by_asset_id(asset.id)
            if meta and meta.extracted_text:
                continue

            file_path = Path(asset.file_path)
            if not file_path.exists():
                logger.warning("Backfill: file not found for asset_id=%d (%s)", asset.id, asset.file_path)
                continue

            try:
                text = TextExtractor.extract_text(file_path)
                if not text:
                    continue
                if meta:
                    repo.update_metadata(asset.id, extracted_text=text)
                else:
                    repo.create_metadata(asset.id, extracted_text=text)
                updated += 1
                logger.debug("Backfill: extracted %d chars for asset_id=%d (%s)", len(text), asset.id, asset.filename)
            except Exception as e:
                logger.warning("Backfill: failed for asset_id=%d: %s", asset.id, e)

        logger.info("Backfill complete: updated %d / %d text assets", updated, len(text_assets))
    except Exception as e:
        logger.error("Backfill failed: %s", e, exc_info=True)
    finally:
        db.close()


def _generate_and_store_metadata(asset_id: int, file_path: Path, file_type: str) -> None:
    """Run AI metadata generation in a background thread with its own DB session."""
    logger.debug("Background metadata generation started for asset_id=%d", asset_id)
    db = SessionLocal()
    try:
        repo = AssetRepository(db)

        # Always extract text (works without OpenAI)
        extracted_text = None
        if file_type == "text":
            try:
                from src.utils.text_extractor import TextExtractor
                extracted_text = TextExtractor.extract_text(file_path)
                logger.debug("Extracted %d chars of text from asset_id=%d", len(extracted_text or ""), asset_id)
            except Exception as e:
                logger.warning("Text extraction failed for asset_id=%d: %s", asset_id, e)

        # Attempt AI metadata (may fail if quota exceeded)
        ai_service = AIService()
        description, tags_json, keywords_json = ai_service.generate_metadata(file_path, file_type)

        if description or tags_json or keywords_json or extracted_text:
            repo.create_metadata(
                asset_id=asset_id,
                description=description,
                tags=tags_json,
                keywords=keywords_json,
                extracted_text=extracted_text,
            )
            logger.info(
                "Metadata stored for asset_id=%d (ai=%s, text_chars=%d)",
                asset_id, "yes" if description else "no", len(extracted_text or ""),
            )
        else:
            logger.debug("No metadata generated for asset_id=%d", asset_id)
    except Exception as e:
        logger.error("Background metadata generation failed for asset_id=%d: %s", asset_id, e)
    finally:
        db.close()


def backfill_image_metadata() -> None:
    """
    Backfill AI metadata for all existing image assets that have no description.
    Runs once in a background thread at startup using local vision model (no API needed).
    """
    logger.info("Starting image metadata backfill via local vision...")
    db = SessionLocal()
    try:
        from src.models.asset import Asset, Metadata
        from src.integrations.local_vision import get_local_vision_client
        from src.utils.helpers import list_to_json

        image_assets = db.query(Asset).filter(Asset.file_type == "image").all()
        repo = AssetRepository(db)
        updated = 0
        client = get_local_vision_client()

        for asset in image_assets:
            meta = repo.get_metadata_by_asset_id(asset.id)
            if meta and meta.description:
                continue  # Already has AI description

            file_path = Path(asset.file_path)
            if not file_path.exists():
                logger.warning("Image backfill: file not found for asset_id=%d", asset.id)
                continue

            try:
                description, tags_json, keywords_json = client.generate_metadata_for_image(str(file_path))

                if meta:
                    repo.update_metadata(asset.id, description=description, tags=tags_json, keywords=keywords_json)
                else:
                    repo.create_metadata(asset.id, description=description, tags=tags_json, keywords=keywords_json)
                updated += 1
                logger.info("Image backfill: processed asset_id=%d (%s): %s", asset.id, asset.filename, description)
            except Exception as e:
                logger.warning("Image backfill: failed for asset_id=%d: %s", asset.id, e)

        logger.info("Image metadata backfill complete: updated %d / %d image assets", updated, len(image_assets))
    except Exception as e:
        logger.error("Image backfill failed: %s", e, exc_info=True)
    finally:
        db.close()


class AssetService:
    """Service for managing assets."""

    def __init__(self, db: Session) -> None:
        """Initialize asset service."""
        self.db = db
        self.repository = AssetRepository(db)
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
        logger.info("Upload started: '%s' (%d bytes)", original_filename, source_path.stat().st_size)
        # Step 1: Validate file (pass original_filename so extension is recognized)
        file_type, mime_type = FileValidator.validate_file(source_path, original_filename)

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

            # Step 6: Kick off AI metadata generation in background (doesn't block upload)
            thread = threading.Thread(
                target=_generate_and_store_metadata,
                args=(asset.id, destination_path, file_type),
                daemon=True,
            )
            thread.start()
            logger.info("Upload complete: '%s' -> asset_id=%d (metadata generating in background)", original_filename, asset.id)

            # Step 7: Build response (metadata will be None until background thread finishes)
            metadata_schema = None
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
            logger.error("Upload failed for '%s': %s", original_filename, e, exc_info=True)
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
                logger.info("Deleted file from disk: %s", file_path.name)
            except Exception as e:
                logger.warning("Could not delete file from disk: %s — %s", file_path, e)

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
