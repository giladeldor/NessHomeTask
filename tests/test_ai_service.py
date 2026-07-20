from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.ai_service import AIService


class TestAIService:
    """Test cases for AIService."""

    @pytest.fixture
    def ai_service(self) -> AIService:
        """Create AIService instance."""
        return AIService()

    def test_initialization(self, ai_service: AIService) -> None:
        """Test that AIService initializes correctly."""
        assert ai_service.client is not None

    def test_generate_metadata_for_text_file(
        self, ai_service: AIService, sample_text_file: Path
    ) -> None:
        """Test metadata generation for text files."""
        # Mock OpenAI client to avoid API calls
        with patch.object(ai_service.client, "generate_metadata_for_text") as mock_gen:
            mock_gen.return_value = {
                "description": "Test document",
                "tags": ["test", "document"],
                "keywords": ["test", "sample"],
            }

            description, tags_json, keywords_json = ai_service.generate_metadata(
                sample_text_file, "text"
            )

            assert description is not None
            assert tags_json is not None
            assert keywords_json is not None

    def test_generate_metadata_for_image_file(
        self, ai_service: AIService, sample_image_path: Path
    ) -> None:
        """Test metadata generation for image files."""
        with patch.object(ai_service.client, "generate_metadata_for_image") as mock_gen:
            mock_gen.return_value = {
                "description": "Red square image",
                "tags": ["red", "square"],
                "keywords": ["color", "shape"],
            }

            description, tags_json, keywords_json = ai_service.generate_metadata(
                sample_image_path, "image"
            )

            assert description is not None
            assert tags_json is not None
            assert keywords_json is not None

    def test_generate_metadata_openai_failure_fallback_to_local_vision(
        self, ai_service: AIService, sample_image_path: Path
    ) -> None:
        """Test fallback to local vision when OpenAI fails."""
        with patch.object(ai_service.client, "generate_metadata_for_image") as mock_openai:
            # Simulate OpenAI failure
            from src.core.exceptions import AIServiceError

            mock_openai.side_effect = AIServiceError("Quota exceeded")

            with patch("src.services.ai_service.get_local_vision_client") as mock_local:
                mock_client = MagicMock()
                mock_client.generate_metadata_for_image.return_value = (
                    "fallback description",
                    '["tag1"]',
                    '["keyword1"]',
                )
                mock_local.return_value = mock_client

                description, tags_json, keywords_json = ai_service.generate_metadata(
                    sample_image_path, "image"
                )

                assert description == "fallback description"
                assert tags_json == '["tag1"]'
                assert keywords_json == '["keyword1"]'
                mock_client.generate_metadata_for_image.assert_called_once()
