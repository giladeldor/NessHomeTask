"""
AI metadata generation service.

Orchestrates AI metadata generation for uploaded assets.
"""

import json
from pathlib import Path
from typing import Optional

from src.core.exceptions import AIServiceError
from src.integrations.openai_client import OpenAIClient
from src.utils.helpers import list_to_json
from src.utils.text_extractor import TextExtractor


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
            # Log and return None for graceful degradation
            print(f"DEBUG: AIServiceError in metadata generation: {str(e)}")
            return None, None, None
        except Exception as e:
            # Unexpected error - log but don't raise
            print(f"DEBUG: Unexpected error in metadata generation: {type(e).__name__}: {str(e)}")
            return None, None, None
