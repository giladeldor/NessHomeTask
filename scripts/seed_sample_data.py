#!/usr/bin/env python
"""Seed database with sample data for testing and demo purposes."""

import json
from pathlib import Path

from src.core.database import SessionLocal
from src.models.asset import Asset, Metadata
from src.core.logging_config import get_logger

logger = get_logger(__name__)


def seed_sample_data() -> None:
    """Create sample assets and metadata."""
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_count = db.query(Asset).count()
        if existing_count > 0:
            logger.info(f"Database already contains {existing_count} assets. Skipping seed.")
            return

        logger.info("Creating sample data...")

        # Sample Asset 1: Python Guide
        asset1 = Asset(
            filename="python_programming_guide.pdf",
            file_type="text",
            file_path="/uploads/sample_python_guide.pdf",
            file_size=250000,
        )
        db.add(asset1)
        db.flush()

        metadata1 = Metadata(
            asset_id=asset1.id,
            description="Comprehensive guide to Python programming covering basics, OOP, and advanced features.",
            tags=json.dumps(["python", "programming", "guide", "tutorial", "education"]),
            keywords=json.dumps(
                ["python", "code", "programming", "development", "tutorial", "learning", "guide",
                 "advanced"]
            ),
            extracted_text="""
            This guide covers Python programming fundamentals including:
            - Variables and data types
            - Control flow and loops
            - Functions and modules
            - Object-oriented programming
            - Exception handling
            - File I/O operations
            - Working with libraries like NumPy and Pandas
            """,
        )
        db.add(metadata1)

        # Sample Asset 2: Machine Learning Paper
        asset2 = Asset(
            filename="deep_learning_research.pdf",
            file_type="text",
            file_path="/uploads/sample_ml_paper.pdf",
            file_size=1500000,
        )
        db.add(asset2)
        db.flush()

        metadata2 = Metadata(
            asset_id=asset2.id,
            description="Research paper on deep learning architectures and their applications in computer vision.",
            tags=json.dumps(["machine learning", "deep learning", "neural networks", "research", "AI"]),
            keywords=json.dumps(
                ["deep learning", "neural networks", "CNN", "RNN", "transformer", "computer vision",
                 "AI", "research"]
            ),
            extracted_text="""
            Recent advances in deep learning have revolutionized:
            - Computer vision applications
            - Natural language processing
            - Reinforcement learning
            - Generative models
            - Transfer learning techniques
            """,
        )
        db.add(metadata2)

        # Sample Asset 3: Business Document
        asset3 = Asset(
            filename="Q3_2024_financial_report.pdf",
            file_type="text",
            file_path="/uploads/sample_financial_report.pdf",
            file_size=500000,
        )
        db.add(asset3)
        db.flush()

        metadata3 = Metadata(
            asset_id=asset3.id,
            description="Third quarter 2024 financial report with revenue analysis and future projections.",
            tags=json.dumps(["financial", "report", "Q3", "2024", "business"]),
            keywords=json.dumps(
                ["revenue", "profit", "financial", "quarterly", "report", "growth", "analysis",
                 "forecast"]
            ),
            extracted_text="""
            Financial Summary Q3 2024:
            - Total Revenue: $2.5M (↑15% YoY)
            - Operating Costs: $1.2M
            - Net Income: $800K
            - Customer Growth: 25%
            - Market Expansion: 3 new regions
            """,
        )
        db.add(metadata3)

        db.commit()
        logger.info(f"✅ Successfully created {db.query(Asset).count()} sample assets")

    except Exception as e:
        logger.error(f"Error seeding data: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_sample_data()
