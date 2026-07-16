"""
Custom exception types for the application.

These exceptions provide clear error handling throughout the application.
"""


class KMSException(Exception):
    """Base exception for the Knowledge Management System."""

    pass


class FileValidationError(KMSException):
    """Raised when file validation fails."""

    pass


class FileSizeError(FileValidationError):
    """Raised when file exceeds size limit."""

    pass


class FileTypeError(FileValidationError):
    """Raised when file type is not allowed."""

    pass


class FileProcessingError(KMSException):
    """Raised when file processing fails."""

    pass


class AIServiceError(KMSException):
    """Raised when AI service fails."""

    pass


class AITimeoutError(AIServiceError):
    """Raised when AI request times out."""

    pass


class AIParsingError(AIServiceError):
    """Raised when AI response parsing fails."""

    pass


class TextExtractionError(FileProcessingError):
    """Raised when text extraction fails."""

    pass


class AssetNotFoundError(KMSException):
    """Raised when asset is not found in database."""

    pass


class SearchError(KMSException):
    """Raised when search operation fails."""

    pass


class DatabaseError(KMSException):
    """Raised when database operation fails."""

    pass
