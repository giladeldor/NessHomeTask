import json
import re
from typing import Any


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues.
    
    Removes special characters, keeps only alphanumerics, hyphens, underscores, and dots.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and special characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Remove multiple dots
    filename = re.sub(r'\.+', '.', filename)
    # Limit length
    filename = filename[:255]
    return filename or "file"


def parse_json_safely(json_str: str | None) -> dict[str, Any] | list[Any]:
    """
    Safely parse JSON string, returns empty dict on failure.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed JSON or empty dict on error
    """
    if not json_str:
        return {}
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return {}


def json_to_list(json_str: str | None) -> list[str]:
    """
    Convert JSON string to list of strings.
    
    Args:
        json_str: JSON array string
        
    Returns:
        List of strings, empty list if parsing fails
    """
    if not json_str:
        return []
    
    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    
    return []


def list_to_json(items: list[str]) -> str:
    """
    Convert list of strings to JSON array.
    
    Args:
        items: List of strings
        
    Returns:
        JSON array string
    """
    return json.dumps(items, ensure_ascii=False)


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to maximum length, respecting word boundaries.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    # Try to cut at last space
    last_space = truncated.rfind(' ')
    if last_space > max_length // 2:
        truncated = truncated[:last_space]
    
    return truncated.rstrip() + "..."
