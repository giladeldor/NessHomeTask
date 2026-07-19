#!/usr/bin/env python
"""Database management utilities."""

import sys
from pathlib import Path

from src.core.database import SessionLocal, Base, engine
from src.core.logging_config import get_logger

logger = get_logger(__name__)


def init_database() -> None:
    """Initialize database schema."""
    logger.info("Initializing database...")
    try:
        Base.metadata.create_all(engine)
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


def reset_database() -> None:
    """Drop and recreate all tables."""
    logger.warning("⚠️  Resetting database - all data will be lost")
    response = input("Type 'yes' to confirm: ")
    
    if response.lower() != "yes":
        logger.info("Reset cancelled")
        return
    
    try:
        Base.metadata.drop_all(engine)
        logger.info("Dropped all tables")
        
        Base.metadata.create_all(engine)
        logger.info("✅ Database reset complete")
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        sys.exit(1)


def show_tables() -> None:
    """Display all tables in database."""
    try:
        inspector = __import__("sqlalchemy", fromlist=["inspect"]).inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            logger.info("No tables found in database")
            return
        
        logger.info(f"Tables in database ({len(tables)}):")
        for table in tables:
            columns = inspector.get_columns(table)
            logger.info(f"  • {table}")
            for col in columns:
                logger.info(f"      - {col['name']}: {col['type']}")
    except Exception as e:
        logger.error(f"Failed to show tables: {e}")
        sys.exit(1)


def count_records() -> None:
    """Count records in each table."""
    try:
        from src.models.asset import Asset, Metadata
        
        db = SessionLocal()
        asset_count = db.query(Asset).count()
        metadata_count = db.query(Metadata).count()
        db.close()
        
        logger.info("Record counts:")
        logger.info(f"  • Assets: {asset_count}")
        logger.info(f"  • Metadata: {metadata_count}")
    except Exception as e:
        logger.error(f"Failed to count records: {e}")
        sys.exit(1)


def cleanup_orphaned_metadata() -> None:
    """Remove metadata records with no corresponding asset."""
    try:
        from src.models.asset import Asset, Metadata
        
        db = SessionLocal()
        
        # Find orphaned metadata
        asset_ids = set(db.query(Asset.id).all())
        orphaned = db.query(Metadata).filter(~Metadata.asset_id.in_(asset_ids)).all()
        
        if not orphaned:
            logger.info("No orphaned metadata found")
            db.close()
            return
        
        logger.warning(f"Found {len(orphaned)} orphaned metadata records")
        response = input("Delete these records? (yes/no): ")
        
        if response.lower() == "yes":
            for meta in orphaned:
                db.delete(meta)
            db.commit()
            logger.info(f"✅ Deleted {len(orphaned)} orphaned records")
        else:
            logger.info("Deletion cancelled")
        
        db.close()
    except Exception as e:
        logger.error(f"Failed to cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management utilities")
    parser.add_argument(
        "command",
        choices=["init", "reset", "show-tables", "count", "cleanup"],
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_database()
    elif args.command == "reset":
        reset_database()
    elif args.command == "show-tables":
        show_tables()
    elif args.command == "count":
        count_records()
    elif args.command == "cleanup":
        cleanup_orphaned_metadata()
