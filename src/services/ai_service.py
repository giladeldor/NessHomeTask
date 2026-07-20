from pathlib import Path
from typing import Optional

from src.core.exceptions import AIServiceError
from src.core.logging_config import get_logger
from src.integrations.openai_client import OpenAIClient
from src.integrations.local_vision import get_local_vision_client
from src.utils.helpers import list_to_json
from src.utils.text_extractor import TextExtractor

logger = get_logger(__name__)


def _try_local_vision_image(file_path: Path) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Attempt image analysis via local BLIP model. Returns (description, tags_json, keywords_json) or (None,None,None)."""
    try:
        client = get_local_vision_client()
        description, tags_json, keywords_json = client.generate_metadata_for_image(str(file_path))
        logger.info("Local vision image analysis succeeded for %s", file_path.name)
        return description, tags_json, keywords_json
    except Exception as e:
        logger.warning("Local vision image analysis failed: %s", e)
        return None, None, None


class AIService:
    """Service for AI-powered metadata generation."""

    def __init__(self) -> None:
        """Initialize AI service."""
        self.client = OpenAIClient()

    def generate_metadata(
        self, file_path: Path, file_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Generate metadata for an uploaded file.

        Args:
            file_path: Path to uploaded file
            file_type: 'image' or 'text'

        Returns:
            Tuple of (description, tags_json, keywords_json)
            Returns (None, None, None) if generation fails

        Raises:
            AIServiceError: If unexpected error occurs
        """
        try:
            logger.debug("Generating metadata for %s file: %s", file_type, file_path.name)
            if file_type == "image":
                metadata = self.client.generate_metadata_for_image(file_path)
            elif file_type == "text":
                # Extract text first
                text = TextExtractor.extract_text(file_path)
                metadata = self.client.generate_metadata_for_text(text)
            else:
                raise AIServiceError(f"Unknown file type: {file_type}")

            # Extract components from metadata
            description = metadata.get("description", "")
            tags = metadata.get("tags", [])
            keywords = metadata.get("keywords", [])

            # Validate and convert to JSON
            if not isinstance(tags, list):
                tags = []
            if not isinstance(keywords, list):
                keywords = []

            tags_json = list_to_json(tags) if tags else None
            keywords_json = list_to_json(keywords) if keywords else None

            return description or None, tags_json, keywords_json

        except AIServiceError as e:
            logger.warning("OpenAI metadata generation failed (degrading gracefully): %s", e)
            # For images, try local vision as fallback
            if file_type == "image":
                logger.info("Trying local vision as fallback for image: %s", file_path.name)
                return _try_local_vision_image(file_path)
            return None, None, None
        except Exception as e:
            logger.error("Unexpected error in metadata generation: %s", e, exc_info=True)
            if file_type == "image":
                return _try_local_vision_image(file_path)
            return None, None, None
