"""
OpenAI integration for metadata generation.

Wraps the OpenAI API with proper error handling and response parsing.
"""

import base64
import json
import re
from pathlib import Path
from typing import Optional

from openai import OpenAI, APIError, Timeout

from src.core.config import settings
from src.core.exceptions import AIServiceError, AITimeoutError, AIParsingError


class OpenAIClient:
    """Client for OpenAI API."""

    def __init__(self) -> None:
        """Initialize OpenAI client."""
        if not settings.openai_api_key:
            raise AIServiceError("OPENAI_API_KEY not configured")

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-3.5-turbo"
        self.timeout = settings.ai_timeout

    def generate_metadata_for_text(self, text: str) -> dict[str, list[str]]:
        """
        Generate metadata for text content.

        Args:
            text: Text content to analyze

        Returns:
            Dictionary with 'description', 'tags', 'keywords'

        Raises:
            AIServiceError: If API call fails
        """
        prompt = """You are a content metadata extractor. Analyze this text and return JSON.

Return ONLY valid JSON, no explanation:
{
  "description": "A brief summary of the text (1-2 sentences)",
  "tags": ["tag1", "tag2", "tag3"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}"""

        return self._call_api_and_parse(
            prompt=prompt,
            content=text,
            is_image=False,
        )

    def generate_metadata_for_image(self, image_path: Path) -> dict[str, list[str]]:
        """
        Generate metadata for image using vision.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with 'description', 'tags', 'keywords'

        Raises:
            AIServiceError: If API call fails
        """
        # Convert image to base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Determine MIME type from extension
        extension = image_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(extension, "image/jpeg")

        image_url = f"data:{mime_type};base64,{image_data}"

        prompt = """You are a content metadata extractor. Analyze this image and return JSON.

Return ONLY valid JSON, no explanation:
{
  "description": "A brief description of what is in the image",
  "tags": ["tag1", "tag2", "tag3"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}"""

        return self._call_api_and_parse(
            prompt=prompt,
            content=image_url,
            is_image=True,
        )

    def _call_api_and_parse(
        self, prompt: str, content: str, is_image: bool
    ) -> dict[str, list[str]]:
        """
        Call OpenAI API and parse response.

        Args:
            prompt: System prompt
            content: Text or image URL to analyze
            is_image: Whether content is an image URL

        Returns:
            Parsed metadata dictionary

        Raises:
            AIServiceError: If API fails
            AITimeoutError: If request times out
            AIParsingError: If response parsing fails
        """
        try:
            if is_image:
                # Vision API call with image
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": content}},
                            ],
                        }
                    ],
                    temperature=0.7,
                    max_tokens=500,
                    timeout=self.timeout,
                )
            else:
                # Regular text API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": f"{prompt}\n\nContent to analyze:\n{content}"}
                    ],
                    temperature=0.7,
                    max_tokens=500,
                    timeout=self.timeout,
                )

            # Extract response text
            response_text = response.choices[0].message.content

            if not response_text:
                raise AIParsingError("Empty response from OpenAI")

            # Parse JSON from response
            return self._parse_json_response(response_text)

        except Timeout as e:
            raise AITimeoutError(f"OpenAI request timed out after {self.timeout}s: {str(e)}")
        except APIError as e:
            raise AIServiceError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            if isinstance(e, (AIServiceError, AITimeoutError, AIParsingError)):
                raise
            raise AIServiceError(f"Unexpected error calling OpenAI: {str(e)}")

    @staticmethod
    def _parse_json_response(response_text: str) -> dict[str, list[str]]:
        """
        Parse JSON from OpenAI response.

        Tries multiple strategies:
        1. Direct JSON parsing
        2. Extract JSON from markdown code block
        3. Regex extraction

        Args:
            response_text: Response text from OpenAI

        Returns:
            Parsed dictionary

        Raises:
            AIParsingError: If parsing fails
        """
        # Strategy 1: Direct parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code block
        markdown_pattern = r"```(?:json)?\s*(.*?)\s*```"
        match = re.search(markdown_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 3: Regex extraction for JSON object
        json_pattern = r"\{.*\}"
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise AIParsingError(f"Could not parse JSON from response: {response_text[:200]}")
