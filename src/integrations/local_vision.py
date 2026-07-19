"""Local vision processing using BLIP model (no API calls needed)."""

import json
import logging
from pathlib import Path

from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

logger = logging.getLogger(__name__)


class LocalVisionClient:
    """BLIP-based image analysis for metadata generation."""

    def __init__(self):
        """Initialize BLIP model and processor."""
        logger.info("Loading BLIP vision model...")
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        logger.info("BLIP model loaded successfully")

    def generate_metadata_for_image(self, image_path: str) -> tuple[str, str, str]:
        """
        Generate metadata for an image using BLIP.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (description, tags_json, keywords_json)
            - description: 1-2 sentence image description
            - tags_json: JSON string with 5 tags
            - keywords_json: JSON string with 8 keywords
        """
        try:
            image = Image.open(image_path).convert("RGB")
            logger.debug(f"Opened image: {image_path} ({image.size})")

            # Generate caption
            inputs = self.processor(image, return_tensors="pt")
            caption_ids = self.model.generate(**inputs, max_length=50, min_length=10)
            caption = self.processor.decode(caption_ids[0], skip_special_tokens=True)
            logger.debug(f"Generated caption: {caption}")

            # Extract visual features for keywords
            description = caption.strip()

            # Create tags based on caption
            words = caption.lower().split()
            tags = []
            for word in words:
                # Filter short words and common stop words
                if len(word) > 3 and word not in {"that", "this", "with", "from", "have"}:
                    tags.append(word.strip(".,!?"))
                if len(tags) >= 5:
                    break
            # Pad if needed
            while len(tags) < 5:
                tags.append("image")

            tags_json = json.dumps(tags[:5])

            # Create keywords (similar to tags but longer)
            keywords = tags + (["visual", "content", "photo"] * 2)[:8 - len(tags)]
            keywords_json = json.dumps(keywords[:8])

            logger.info(f"Generated metadata for {Path(image_path).name}: {len(tags)} tags, {len(json.loads(keywords_json))} keywords")
            return description, tags_json, keywords_json

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}", exc_info=True)
            raise


# Singleton instance
_client = None


def get_local_vision_client() -> LocalVisionClient:
    """Get or create singleton vision client."""
    global _client
    if _client is None:
        _client = LocalVisionClient()
    return _client
