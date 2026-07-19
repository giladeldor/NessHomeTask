"""
Google Gemini integration for image metadata generation.

Used as fallback when OpenAI is unavailable or quota-exceeded.
Free tier: 15 requests/minute, 1500 requests/day.
Get a key at: https://aistudio.google.com/apikey
"""

import json
import re
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Client for Google Gemini Vision API."""

    MODEL = "gemini-pro-vision"

    PROMPT = """Analyze this image and return ONLY valid JSON with no explanation:
{
  "description": "A one or two sentence description of what is in the image, including key visual features like hair color, clothing, objects, setting, people, animals, etc.",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"]
}
Be specific about visual features: colors, textures, subjects, actions, environment."""

    def __init__(self) -> None:
        from src.core.config import settings
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        self._genai = genai

    def generate_metadata_for_image(self, image_path: Path) -> dict:
        """
        Analyze an image and return metadata dict.

        Returns:
            dict with 'description', 'tags', 'keywords'

        Raises:
            Exception on API failure
        """
        from PIL import Image as PILImage

        logger.debug("Gemini: analyzing image %s", image_path.name)
        model = self._genai.GenerativeModel(self.MODEL)
        image = PILImage.open(image_path)
        response = model.generate_content([self.PROMPT, image])
        return self._parse_response(response.text)

    def _parse_response(self, text: str) -> dict:
        """Parse JSON from Gemini response."""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Extract from markdown code block
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        logger.warning("Gemini: could not parse response as JSON, using raw text as description")
        return {"description": text.strip(), "tags": [], "keywords": []}
