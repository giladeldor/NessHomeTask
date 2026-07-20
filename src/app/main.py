from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.core.database import init_db
from src.core.exceptions import KMSException
from src.core.logging_config import get_logger, setup_logging
from src.services.asset_service import backfill_extracted_text, backfill_image_metadata

# Configure logging once at import time (avoids multiprocessing conflicts with --reload)
setup_logging()
logger = get_logger(__name__)


from fastapi.openapi.docs import get_swagger_ui_html

"""
Main FastAPI application.

Initializes the Knowledge Management System API with:
- Route registration
- Middleware configuration
- Error handling
- Database initialization
"""

def get_custom_swagger_ui_html() -> str:
    """Generate custom Swagger UI with better styling"""
    return get_swagger_ui_html(
        title="Knowledge Management System - API Docs",
        openapi_url="/openapi.json",
        swagger_ui_parameters={
            "deepLinking": True,
            "defaultModelsExpandDepth": -1,
            "defaultModelExpandDepth": -1,
            "docExpansion": "list",
            "supportedSubmitMethods": [],  # Disable all execute buttons
        },
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
    )

# Initialize FastAPI app
def custom_docs(request: Request):
    """Serve custom styled Swagger UI."""
    return get_custom_swagger_ui_html()


app = FastAPI(
    title="Knowledge Management System",
    description="A system for uploading, organizing, and searching documents with AI-generated metadata",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)

# Mount custom docs at /api/docs
app.add_route("/api/docs", custom_docs, methods=["GET"])

# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Error Handling Middleware
# ============================================================================


@app.exception_handler(KMSException)
async def kms_exception_handler(request: Request, exc: KMSException) -> JSONResponse:
    """Handle custom KMS exceptions."""
    logger.warning("KMS exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": str(exc),
            "status_code": 400,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method, request.url.path, exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
        },
    )


# ============================================================================
# Startup & Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database on startup."""
    try:
        init_db()
        logger.info("Database initialized successfully")
        print("✅ Database initialized successfully")
    except Exception as e:
        logger.critical("Failed to initialize database: %s", e, exc_info=True)
        print(f"❌ Failed to initialize database: {str(e)}")
        raise

    # Backfill extracted_text for any existing assets that predate this feature
    import threading
    threading.Thread(target=backfill_extracted_text, daemon=True).start()
    threading.Thread(target=backfill_image_metadata, daemon=True).start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    logger.info("Application shutting down")
    print("🛑 Application shutting down...")


# ============================================================================
# Router Registration
# ============================================================================

app.include_router(router)

# ============================================================================
# Static Files & Frontend Routes
# ============================================================================

static_dir = Path(__file__).parent / "static"

# Mount static files directory
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend() -> FileResponse:
    """Serve the main frontend application."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")
    return {"error": "Frontend not available"}


@app.get("/docs-ui", include_in_schema=False)
async def serve_custom_docs() -> FileResponse:
    """Serve custom API documentation UI."""
    docs_file = static_dir / "docs.html"
    if docs_file.exists():
        return FileResponse(docs_file, media_type="text/html")
    return {"error": "Documentation not available"}

# ============================================================================
# Root API Endpoint
# ============================================================================


@app.get("/api", tags=["root"], summary="API Information")
def api_info() -> dict[str, str]:
    """API root endpoint with basic information."""
    return {
        "name": "Knowledge Management System",
        "version": "0.1.0",
        "docs": "/api/docs",
        "custom_docs": "/docs-ui",
        "health": "/api/health",
        "frontend": "/",
    }
