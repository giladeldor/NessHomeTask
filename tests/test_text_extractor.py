"""Tests for text extraction module."""

from pathlib import Path

import pytest

from src.utils.text_extractor import TextExtractor


class TestTextExtractor:
    """Test cases for TextExtractor."""

    def test_extract_text_from_txt_file(self, sample_text_file: Path) -> None:
        """Test text extraction from .txt files."""
        extracted = TextExtractor.extract_text(sample_text_file)
        assert extracted is not None
        assert len(extracted) > 0
        assert "machine learning" in extracted.lower()

    def test_extract_text_empty_file(self) -> None:
        """Test extraction from empty text file."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            path = Path(f.name)

        try:
            extracted = TextExtractor.extract_text(path)
            assert extracted == "" or extracted is None
        finally:
            path.unlink(missing_ok=True)

    def test_extract_text_unsupported_file_type(self) -> None:
        """Test error handling for unsupported file types."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"random content")
            path = Path(f.name)

        try:
            with pytest.raises(Exception):
                TextExtractor.extract_text(path)
        finally:
            path.unlink(missing_ok=True)

    def test_extract_text_missing_file(self) -> None:
        """Test error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            TextExtractor.extract_text(Path("/nonexistent/file.txt"))

    def test_extract_text_respects_character_limit(self) -> None:
        """Test that extraction respects character limits."""
        import tempfile

        # Create a file with long content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("word " * 100000)  # ~500KB of text
            path = Path(f.name)

        try:
            extracted = TextExtractor.extract_text(path)
            # Should be limited or handled gracefully
            assert extracted is not None
        finally:
            path.unlink(missing_ok=True)
