"""Pytest configuration and fixtures for testing."""

import json
import tempfile
import uuid
from pathlib import Path
from typing import Generator

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.database import Base
from src.core.config import settings
from src.models.asset import Asset, Metadata
from src.repositories.asset_repository import AssetRepository


@pytest.fixture(scope="session")
def test_db_path() -> str:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield f"sqlite:///{db_path}"


@pytest.fixture(scope="function")
def test_db_session(test_db_path: str) -> Generator[Session, None, None]:
    """Create a test database session."""
    engine = create_engine(test_db_path, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def asset_repository(test_db_session: Session) -> AssetRepository:
    """Create asset repository with test database."""
    return AssetRepository(test_db_session)


@pytest.fixture
def sample_image_path() -> Generator[Path, None, None]:
    """Create a temporary test image."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (100, 100), color="red")
        img.save(f.name)
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def sample_text_file() -> Generator[Path, None, None]:
    """Create a temporary test text file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document about machine learning and AI.")
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def sample_pdf_file() -> Generator[Path, None, None]:
    """Create a temporary test PDF file (placeholder - requires reportlab in real tests)."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        # In real tests, use reportlab or pypdf to create actual PDFs
        f.write(b"%PDF-1.4\n%Sample PDF placeholder")
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def test_asset(test_db_session: Session, asset_repository: AssetRepository) -> Asset:
    """Create a test asset."""
    # Generate unique file path to avoid UNIQUE constraint violations
    unique_id = str(uuid.uuid4())[:8]
    asset = Asset(
        filename="test_file.txt",
        file_type="text",
        mime_type="text/plain",
        file_path=f"/tmp/test_file_{unique_id}.txt",
        file_size=1024,
    )
    test_db_session.add(asset)
    test_db_session.commit()
    return asset


@pytest.fixture
def test_metadata(test_db_session: Session, test_asset: Asset) -> Metadata:
    """Create test metadata."""
    metadata = Metadata(
        asset_id=test_asset.id,
        description="Test document about Python programming",
        tags=json.dumps(["python", "programming", "test"]),
        keywords=json.dumps(["python", "code", "development"]),
        extracted_text="This is test content about Python.",
    )
    test_db_session.add(metadata)
    test_db_session.commit()
    return metadata


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings to defaults before each test."""
    yield
    # Reset any modified settings
    settings.gemini_api_key = ""
