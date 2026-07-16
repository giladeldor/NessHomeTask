"""
Main FastAPI application.

Initializes the Knowledge Management System API with:
- Route registration
- Middleware configuration
- Error handling
- Database initialization
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.api.schemas import ErrorResponseSchema
from src.core.database import init_db
from src.core.exceptions import KMSException

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Management System",
    description="A system for uploading, organizing, and searching documents with AI-generated metadata",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

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
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    print("🛑 Application shutting down...")


# ============================================================================
# Router Registration
# ============================================================================

app.include_router(router)

# ============================================================================
# Static Files (Optional - for serving frontend)
# ============================================================================

# Uncomment if you want to serve static files (CSS, JS, images)
# from pathlib import Path
# static_dir = Path(__file__).parent.parent.parent / "static"
# if static_dir.exists():
#     app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/", tags=["root"], summary="API Root")
def root() -> dict[str, str]:
    """Root endpoint with basic information."""
    return {
        "name": "Knowledge Management System",
        "version": "0.1.0",
        "docs": "/api/docs",
        "health": "/api/health",
    }
