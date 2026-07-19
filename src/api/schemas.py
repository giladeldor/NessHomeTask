"""
Pydantic schemas for API request/response validation.

These schemas define the contract for all API endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MetadataSchema(BaseModel):
    """AI-generated metadata for an asset."""

    description: Optional[str] = Field(None, description="Description of the asset content")
    tags: list[str] = Field(default_factory=list, description="Tags extracted from content")
    keywords: list[str] = Field(default_factory=list, description="Keywords extracted from content")


class AssetSchema(BaseModel):
    """Basic asset information."""

    id: int
    filename: str
    file_type: str  # 'image' or 'text'
    mime_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class AssetDetailSchema(AssetSchema):
    """Asset with metadata."""

    metadata: Optional[MetadataSchema] = None


class UploadResponseSchema(BaseModel):
    """Response for file upload."""

    success: bool
    asset: AssetSchema
    metadata: Optional[MetadataSchema] = None
    message: Optional[str] = None


class ErrorResponseSchema(BaseModel):
    """Standard error response."""

    error: str
    status_code: int = 400


class ListAssetsResponseSchema(BaseModel):
    """Response for listing assets."""

    assets: list[AssetSchema]
    total: int
    page: int
    per_page: int


class SearchResultSchema(BaseModel):
    """Individual search result with relevance score."""

    id: int
    filename: str
    file_type: str
    file_size: int
    created_at: datetime
    metadata: MetadataSchema
    relevance_score: int


class SearchResponseSchema(BaseModel):
    """Response for search query."""

    query: str
    results: list[SearchResultSchema]
    total: int
    page: int
    per_page: int


class HealthResponseSchema(BaseModel):
    """Health check response."""

    status: str = "healthy"
