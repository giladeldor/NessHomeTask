"""
Repository layer for data access.

Repositories provide a clean interface for database operations.
This layer abstracts SQLAlchemy from the service layer.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.models.asset import Asset, Metadata


class AssetRepository:
    """Repository for Asset model operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def create_asset(
        self,
        filename: str,
        file_type: str,
        mime_type: str,
        file_path: str,
        file_size: int,
    ) -> Asset:
        """
        Create a new asset record.

        Args:
            filename: Original filename
            file_type: 'image' or 'text'
            mime_type: MIME type (e.g., 'image/jpeg')
            file_path: Relative path to uploaded file
            file_size: File size in bytes

        Returns:
            Created Asset instance
        """
        asset = Asset(
            filename=filename,
            file_type=file_type,
            mime_type=mime_type,
            file_path=file_path,
            file_size=file_size,
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get_asset_by_id(self, asset_id: int) -> Optional[Asset]:
        """Get asset by ID."""
        return self.db.query(Asset).filter(Asset.id == asset_id).first()

    def get_all_assets(self, skip: int = 0, limit: int = 50) -> tuple[list[Asset], int]:
        """
        Get all assets with pagination.

        Returns:
            Tuple of (assets list, total count)
        """
        total = self.db.query(Asset).count()
        assets = self.db.query(Asset).order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()
        return assets, total

    def delete_asset(self, asset_id: int) -> bool:
        """
        Delete an asset by ID.

        Returns:
            True if deleted, False if not found
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if asset:
            self.db.delete(asset)
            self.db.commit()
            return True
        return False

    def create_metadata(
        self,
        asset_id: int,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        keywords: Optional[str] = None,
        extracted_text: Optional[str] = None,
    ) -> Metadata:
        """
        Create metadata for an asset.

        Args:
            asset_id: ID of the asset
            description: Metadata description (JSON string)
            tags: JSON array string of tags
            keywords: JSON array string of keywords
            extracted_text: Raw text extracted from the file

        Returns:
            Created Metadata instance
        """
        metadata = Metadata(
            asset_id=asset_id,
            description=description,
            tags=tags,
            keywords=keywords,
            extracted_text=extracted_text,
        )
        self.db.add(metadata)
        self.db.commit()
        self.db.refresh(metadata)
        return metadata

    def get_metadata_by_asset_id(self, asset_id: int) -> Optional[Metadata]:
        """Get metadata for an asset."""
        return self.db.query(Metadata).filter(Metadata.asset_id == asset_id).first()

    def update_metadata(
        self,
        asset_id: int,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        keywords: Optional[str] = None,
        extracted_text: Optional[str] = None,
    ) -> Optional[Metadata]:
        """
        Update metadata for an asset.

        Returns:
            Updated Metadata instance or None if not found
        """
        metadata = self.db.query(Metadata).filter(Metadata.asset_id == asset_id).first()
        if metadata:
            if description is not None:
                metadata.description = description
            if tags is not None:
                metadata.tags = tags
            if keywords is not None:
                metadata.keywords = keywords
            if extracted_text is not None:
                metadata.extracted_text = extracted_text
            self.db.commit()
            self.db.refresh(metadata)
        return metadata

    def search_assets(
        self, query: str, skip: int = 0, limit: int = 50
    ) -> tuple[list[dict], int]:
        """
        Search across assets using LIKE queries.

        Searches in:
        - Asset.filename
        - metadata.description
        - metadata.tags
        - metadata.keywords

        Returns:
            Tuple of (results list with relevance scores, total count)
        """
        search_term = f"%{query.lower()}%"

        # Build query with relevance scoring
        results = (
            self.db.query(
                Asset.id,
                Asset.filename,
                Asset.file_type,
                Asset.created_at,
                Metadata.description,
                Metadata.tags,
                Metadata.keywords,
            )
            .outerjoin(Metadata, Asset.id == Metadata.asset_id)
            .filter(
                (Asset.filename.ilike(search_term))
                | (Metadata.description.ilike(search_term))
                | (Metadata.tags.ilike(search_term))
                | (Metadata.keywords.ilike(search_term))
                | (Metadata.extracted_text.ilike(search_term))
            )
            .order_by(Asset.created_at.desc())
            .all()
        )

        # Calculate total before pagination
        total = len(results)

        # Apply pagination
        paginated_results = results[skip : skip + limit]

        # Convert to dictionaries and calculate relevance scores
        result_dicts = []
        for row in paginated_results:
            score = self._calculate_relevance_score(query.lower(), row)
            result_dicts.append(
                {
                    "id": row.id,
                    "filename": row.filename,
                    "file_type": row.file_type,
                    "created_at": row.created_at,
                    "description": row.description,
                    "tags": row.tags,
                    "keywords": row.keywords,
                    "relevance_score": score,
                }
            )

        # Sort by relevance score
        result_dicts.sort(key=lambda x: x["relevance_score"], reverse=True)

        return result_dicts, total

    @staticmethod
    def _calculate_relevance_score(query: str, row) -> int:
        """
        Calculate relevance score for a search result.

        Scoring:
        - Exact tag match: +100
        - Keyword match: +50
        - Description match: +30
        """
        score = 0
        query_lower = query.lower()

        # Check tags (highest score)
        if row.tags:
            if query_lower in row.tags.lower():
                score += 100

        # Check keywords
        if row.keywords:
            if query_lower in row.keywords.lower():
                score += 50

        # Check description
        if row.description:
            if query_lower in row.description.lower():
                score += 30

        return score if score > 0 else 10  # Minimum score for matches
