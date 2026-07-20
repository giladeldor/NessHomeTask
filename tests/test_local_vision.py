import json
from pathlib import Path

import pytest
from PIL import Image

import src.integrations.local_vision as local_vision
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

    def test_missing_torch_falls_back_gracefully(self, monkeypatch) -> None:
        """Missing optional dependencies should not crash the vision client."""

        class FailingProcessor:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                raise ImportError("PyTorch was not found")

        class FailingModel:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                raise ImportError("PyTorch was not found")

        monkeypatch.setattr(local_vision, "BlipProcessor", FailingProcessor)
        monkeypatch.setattr(local_vision, "BlipForConditionalGeneration", FailingModel)
        local_vision._client = None

        client = local_vision.get_local_vision_client()
        assert client is not None
        assert client.available is False

        description, tags_json, keywords_json = client.generate_metadata_for_image("/tmp/example.jpg")
        assert description == "image upload"
        assert tags_json == '["image", "upload"]'
        assert keywords_json == '["image", "upload", "visual", "content"]'
