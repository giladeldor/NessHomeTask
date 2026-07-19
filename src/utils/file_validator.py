"""
File validation utilities.

Validates file type, size, and integrity.
"""

from pathlib import Path
from typing import Optional

from PIL import Image

from src.core.config import settings
from src.core.exceptions import FileSizeError, FileTypeError
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FileValidator:
    """Validates uploaded files."""

    ALLOWED_TEXT_TYPES = settings.allowed_text_extensions
    ALLOWED_IMAGE_TYPES = settings.allowed_image_extensions
    MAX_FILE_SIZE = settings.max_file_size

    # MIME type mapping
    MIME_TYPES = {
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    @classmethod
    def validate_file(cls, file_path: Path, filename: Optional[str] = None) -> tuple[str, str]:
        """
        Validate a file and return (file_type, mime_type).

        Args:
            file_path: Path to the file
            filename: Optional original filename (used for extension validation)

        Returns:
            Tuple of (file_type, mime_type) where file_type is 'image' or 'text'

        Raises:
            FileTypeError: If file type is not allowed
            FileSizeError: If file size exceeds limit
        """
        if not file_path.exists():
            raise FileTypeError("File does not exist")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > cls.MAX_FILE_SIZE:
            logger.warning(
                "File rejected — too large: %d bytes (max %d)", file_size, cls.MAX_FILE_SIZE
            )
            raise FileSizeError(
                f"File size {file_size} bytes exceeds maximum {cls.MAX_FILE_SIZE} bytes"
            )

        if file_size == 0:
            logger.warning("File rejected — empty file")
            raise FileTypeError("File is empty")

        # Get extension - use provided filename if available (e.g., for temp files)
        # otherwise use file_path.suffix
        if filename:
            extension = Path(filename).suffix.lower()
        else:
            extension = file_path.suffix.lower()
            
        if not extension:
            raise FileTypeError("File has no extension")

        # Determine file type
        if extension in cls.ALLOWED_TEXT_TYPES:
            file_type = "text"
        elif extension in cls.ALLOWED_IMAGE_TYPES:
            file_type = "image"
        else:
            logger.warning("File rejected — unsupported extension: '%s'", extension)
            raise FileTypeError(
                f"File type '{extension}' not allowed. "
                f"Allowed text: {', '.join(cls.ALLOWED_TEXT_TYPES)}, "
                f"Allowed images: {', '.join(cls.ALLOWED_IMAGE_TYPES)}"
            )

        # Get MIME type
        mime_type = cls.MIME_TYPES.get(extension, "application/octet-stream")

        # Additional validation based on type
        if file_type == "image":
            cls._validate_image(file_path)
        elif file_type == "text" and extension == ".txt":
            # Only validate plain text files for UTF-8 encoding
            # PDF and DOCX are binary formats, so skip validation
            cls._validate_text_file(file_path)

        return file_type, mime_type

    @staticmethod
    def _validate_image(file_path: Path) -> None:
        """Validate image file integrity."""
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            raise FileTypeError(f"Image file is corrupted or invalid: {str(e)}")

    @staticmethod
    def _validate_text_file(file_path: Path) -> None:
        """Validate text file readability."""
        try:
            # Try to read first 1KB to verify it's readable
            with open(file_path, "rb") as f:
                content = f.read(1024)
                # Try to decode as UTF-8
                content.decode("utf-8")
        except UnicodeDecodeError:
            raise FileTypeError("Text file is not valid UTF-8")
        except Exception as e:
            raise FileTypeError(f"Cannot read text file: {str(e)}")
