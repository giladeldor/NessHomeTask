import json
from pathlib import Path

import pytest
from PIL import Image

from src.integrations.local_vision import LocalVisionClient


class TestLocalVisionClient:
    """Test cases for LocalVisionClient."""

    def test_initialization(self) -> None:
        """Test that LocalVisionClient initializes correctly."""
        client = LocalVisionClient()
        assert client.processor is not None
        assert client.model is not None

    def test_generate_metadata_for_valid_image(self, sample_image_path: Path) -> None:
        """Test metadata generation for a valid image."""
        client = LocalVisionClient()
        description, tags_json, keywords_json = client.generate_metadata_for_image(
            str(sample_image_path)
        )

        assert description is not None
        assert isinstance(description, str)
        assert len(description) > 0

        assert tags_json is not None
        tags = json.loads(tags_json)
        assert isinstance(tags, list)
        assert len(tags) > 0

        assert keywords_json is not None
        keywords = json.loads(keywords_json)
        assert isinstance(keywords, list)
        assert len(keywords) > 0

    def test_generate_metadata_missing_file(self) -> None:
        """Test error handling for missing image file."""
        client = LocalVisionClient()
        with pytest.raises(Exception):
            client.generate_metadata_for_image("/nonexistent/path/image.jpg")

    def test_get_local_vision_client_singleton(self) -> None:
        """Test that get_local_vision_client returns singleton."""
        from src.integrations.local_vision import get_local_vision_client

        client1 = get_local_vision_client()
        client2 = get_local_vision_client()
        assert client1 is client2
