"""
FastAPI routes for the Knowledge Management System.

Provides REST API endpoints for:
- File upload with validation and AI metadata generation
- Asset retrieval and management
- Search with pagination and relevance scoring
- Health checks
"""

import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.api.schemas import (
    AssetDetailSchema,
    ErrorResponseSchema,
    HealthResponseSchema,
    ListAssetsResponseSchema,
    SearchResponseSchema,
    UploadResponseSchema,
)
from src.core.database import get_db
from src.core.exceptions import (
    AssetNotFoundError,
    FileTypeError,
    FileSizeError,
    FileProcessingError,
    SearchError,
)
from src.repositories.asset_repository import AssetRepository
from src.services.asset_service import AssetService
from src.services.search_service import SearchService

# Create router for API routes
router = APIRouter(prefix="/api", tags=["api"])


# ============================================================================
# Health Check
# ============================================================================


@router.get(
    "/health",
    response_model=HealthResponseSchema,
    summary="Health check",
    description="Check if the API is running and database is accessible",
)
def health_check(db: Session = Depends(get_db)) -> HealthResponseSchema:
    """Health check endpoint."""
    try:
        # Try to execute a simple query to verify database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return HealthResponseSchema(status="healthy")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )


# ============================================================================
# Asset Upload
# ============================================================================


@router.post(
    "/upload",
    response_model=UploadResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
    description="Upload a file (image or document) and generate AI metadata",
    responses={
        400: {"model": ErrorResponseSchema, "description": "Invalid file"},
        413: {"model": ErrorResponseSchema, "description": "File too large"},
        500: {"model": ErrorResponseSchema, "description": "Processing error"},
    },
)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponseSchema:
    """
    Upload a file and automatically generate metadata.

    Supports:
    - Images: .jpg, .jpeg, .png, .gif, .webp
    - Documents: .txt, .pdf, .doc, .docx

    Returns asset information with generated metadata.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename",
        )

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        try:
            # Upload via service
            service = AssetService(db)
            asset_detail = service.upload_asset(temp_path, file.filename)

            return UploadResponseSchema(
                success=True,
                asset=asset_detail,
                metadata=asset_detail.metadata,
                message="File uploaded successfully",
            )

        finally:
            # Cleanup temporary file
            if temp_path.exists():
                temp_path.unlink()

    except FileSizeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
            detail=str(e),
        )
    except FileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


# ============================================================================
# Asset Retrieval
# ============================================================================


@router.get(
    "/assets",
    response_model=ListAssetsResponseSchema,
    summary="List all assets",
    description="Retrieve a paginated list of all uploaded assets",
    responses={
        200: {"description": "List of assets"},
    },
)
def list_assets(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
) -> ListAssetsResponseSchema:
    """
    Get paginated list of all assets.

    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 500)
    """
    try:
        repo = AssetRepository(db)
        skip = (page - 1) * per_page

        assets, total = repo.get_all_assets(skip=skip, limit=per_page)

        return ListAssetsResponseSchema(
            assets=assets,
            total=total,
            page=page,
            per_page=per_page,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assets: {str(e)}",
        )


@router.get(
    "/assets/{asset_id}",
    response_model=AssetDetailSchema,
    summary="Get asset details",
    description="Retrieve detailed information about a specific asset",
    responses={
        404: {"model": ErrorResponseSchema, "description": "Asset not found"},
    },
)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
) -> AssetDetailSchema:
    """Get detailed information about a specific asset including metadata."""
    try:
        service = AssetService(db)
        asset = service.get_asset(asset_id)

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found",
            )

        return asset
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve asset: {str(e)}",
        )


@router.get(
    "/assets/{asset_id}/download",
    summary="Download asset file",
    description="Download the original file for a specific asset",
    responses={
        404: {"description": "Asset not found"},
        200: {"description": "File content"},
    },
)
def download_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """Download the original file for an asset."""
    from fastapi.responses import FileResponse

    try:
        service = AssetService(db)
        file_path = service.get_asset_file_path(asset_id)

        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found or file is missing",
            )

        # Get asset info for filename
        asset = service.get_asset(asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found",
            )

        return FileResponse(
            path=file_path,
            filename=asset.filename,
            media_type=asset.mime_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download asset: {str(e)}",
        )


# ============================================================================
# Asset Deletion
# ============================================================================


@router.delete(
    "/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an asset",
    description="Delete an asset and its associated metadata and file",
    responses={
        404: {"model": ErrorResponseSchema, "description": "Asset not found"},
    },
)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete an asset and its associated file and metadata."""
    try:
        service = AssetService(db)
        deleted = service.delete_asset(asset_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete asset: {str(e)}",
        )


# ============================================================================
# Search
# ============================================================================


@router.get(
    "/search",
    response_model=SearchResponseSchema,
    summary="Search assets",
    description="Search for assets by query with relevance scoring and pagination",
    responses={
        200: {"description": "Search results"},
    },
)
def search_assets(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db),
) -> SearchResponseSchema:
    """
    Search for assets by query.

    Searches across:
    - Asset filenames
    - Descriptions
    - Tags
    - Keywords

    Results are ranked by relevance score.

    Query Parameters:
    - q: Search query (required, min 1 character)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 500)
    """
    try:
        service = SearchService(db)
        results = service.search(query=q, page=page, per_page=per_page)
        return results

    except SearchError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )
