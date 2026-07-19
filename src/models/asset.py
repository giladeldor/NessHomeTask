"""
SQLAlchemy models for the Knowledge Management System.

These models represent the database schema:
- Asset: Uploaded files (images, text)
- Metadata: AI-generated searchable metadata
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Asset(Base):
    """Represents an uploaded file (image or text)."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'image' or 'text'
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'image/jpeg'
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)  # relative path
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship
    asset_metadata: Mapped[Optional["Metadata"]] = relationship(
        "Metadata", back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, filename='{self.filename}', file_type='{self.file_type}')>"


class Metadata(Base):
    """AI-generated searchable metadata for an asset."""

    __tablename__ = "metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, unique=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string: '["tag1", "tag2"]'
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string: '["kw1", "kw2"]'
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Raw text from file

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship
    asset: Mapped["Asset"] = relationship("Asset", back_populates="asset_metadata")

    def __repr__(self) -> str:
        return f"<Metadata(id={self.id}, asset_id={self.asset_id})>"
