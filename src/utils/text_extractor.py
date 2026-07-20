from pathlib import Path
from typing import Optional

import pdfplumber
from docx import Document

from src.core.exceptions import TextExtractionError


class TextExtractor:
    """Extracts text from uploaded files."""

    # Maximum tokens to extract (approximate: 4 chars per token)
    MAX_TOKENS = 8000
    MAX_CHARS = MAX_TOKENS * 4

    @classmethod
    def extract_text(cls, file_path: Path) -> str:
        """
        Extract text from file.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text (truncated to MAX_CHARS)

        Raises:
            TextExtractionError: If extraction fails
        """
        extension = file_path.suffix.lower()

        try:
            if extension == ".txt":
                return cls._extract_txt(file_path)
            elif extension == ".pdf":
                return cls._extract_pdf(file_path)
            elif extension in [".docx", ".doc"]:
                return cls._extract_docx(file_path)
            else:
                raise TextExtractionError(f"Unsupported file type: {extension}")
        except TextExtractionError:
            raise
        except Exception as e:
            raise TextExtractionError(f"Failed to extract text: {str(e)}")

    @staticmethod
    def _extract_txt(file_path: Path) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read(TextExtractor.MAX_CHARS)
            return text.strip()
        except Exception as e:
            raise TextExtractionError(f"Failed to read text file: {str(e)}")

    @classmethod
    def _extract_pdf(cls, file_path: Path) -> str:
        """Extract text from PDF file."""
        text_parts: list[str] = []
        total_chars = 0

        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract text from first few pages to stay under token limit
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                        total_chars += len(page_text)

                        if total_chars >= cls.MAX_CHARS:
                            break

            extracted_text = "\n".join(text_parts)
            # Truncate to max length
            return extracted_text[: cls.MAX_CHARS].strip()
        except Exception as e:
            raise TextExtractionError(f"Failed to extract text from PDF: {str(e)}")

    @classmethod
    def _extract_docx(cls, file_path: Path) -> str:
        """Extract text from DOCX/DOC file."""
        text_parts: list[str] = []

        try:
            doc = Document(file_path)

            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)

            extracted_text = "\n".join(text_parts)
            # Truncate to max length
            return extracted_text[: cls.MAX_CHARS].strip()
        except Exception as e:
            raise TextExtractionError(f"Failed to extract text from DOCX: {str(e)}")
