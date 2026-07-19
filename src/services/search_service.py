"""
Search service for asset discovery.

Provides search with relevance scoring and pagination.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.api.schemas import MetadataSchema, SearchResponseSchema, SearchResultSchema
from src.core.logging_config import get_logger
from src.repositories.asset_repository import AssetRepository
from src.utils.helpers import json_to_list

logger = get_logger(__name__)


class SearchService:
    """Service for searching assets."""

    def __init__(self, db: Session) -> None:
        """Initialize search service."""
        self.db = db
        self.repository = AssetRepository(db)

    def search(
        self, query: str, page: int = 1, per_page: int = 50
    ) -> SearchResponseSchema:
        """
        Search for assets.

        Args:
            query: Search query
            page: Page number (1-based)
            per_page: Results per page

        Returns:
            SearchResponseSchema with results
        """
        # Validate inputs
        if not query or not query.strip():
            return SearchResponseSchema(
                query=query,
                results=[],
                total=0,
                page=page,
                per_page=per_page,
            )

        query = query.strip()
        logger.info("Search query: '%s' (page=%d, per_page=%d)", query, page, per_page)

        # Calculate offset
        skip = (page - 1) * per_page

        # Search
        results, total = self.repository.search_assets(query, skip=skip, limit=per_page)
        logger.debug("Search '%s' returned %d / %d results", query, len(results), total)

        # Convert to SearchResultSchema
        search_results = []
        for result in results:
            metadata_schema = MetadataSchema(
                description=result["description"],
                tags=json_to_list(result["tags"]),
                keywords=json_to_list(result["keywords"]),
            )

            search_results.append(
                SearchResultSchema(
                    id=result["id"],
                    filename=result["filename"],
                    file_type=result["file_type"],
                    created_at=result["created_at"],
                    metadata=metadata_schema,
                    relevance_score=result["relevance_score"],
                )
            )

        return SearchResponseSchema(
            query=query,
            results=search_results,
            total=total,
            page=page,
            per_page=per_page,
        )
