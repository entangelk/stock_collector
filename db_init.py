"""
Database initialization script.
"""
import logging
from typing import List
from datetime import datetime

from database import db_manager
from repositories import TargetTickerRepository, JobStatusRepository
from config import settings

logger = logging.getLogger(__name__)


def initialize_database() -> bool:
    """Initialize database connections and create indexes."""
    try:
        # Connect to database
        db_manager.connect()
        logger.info("Database connection established")
        
        # Create indexes for optimal performance
        db_manager.create_indexes()
        logger.info("Database indexes created")
        
        # Verify collections are accessible
        _verify_collections()
        logger.info("Database collections verified")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def _verify_collections() -> None:
    """Verify that all required collections are accessible."""
    # Test system_info database collections
    target_ticker_repo = TargetTickerRepository()
    job_status_repo = JobStatusRepository()
    
    # Test basic operations
    target_ticker_repo.count_documents()
    job_status_repo.count_documents()
    
    logger.debug("All collections are accessible")


def create_sample_data() -> bool:
    """Create sample data for testing (optional)."""
    try:
        target_ticker_repo = TargetTickerRepository()
        
        # Check if we already have data
        if target_ticker_repo.count_documents() > 0:
            logger.info("Sample data already exists, skipping creation")
            return True
        
        # Create sample target tickers (major Korean stocks)
        from schemas import TargetTicker
        from datetime import date
        
        sample_tickers = [
            TargetTicker(
                ticker="005930",
                name="삼성전자",
                market_cap=600_000_000_000_000,  # 600조원
                added_date=date.today(),
                is_active=True
            ),
            TargetTicker(
                ticker="000660",
                name="SK하이닉스",
                market_cap=150_000_000_000_000,  # 150조원
                added_date=date.today(),
                is_active=True
            ),
            TargetTicker(
                ticker="035420",
                name="NAVER",
                market_cap=80_000_000_000_000,  # 80조원
                added_date=date.today(),
                is_active=True
            ),
            TargetTicker(
                ticker="051910",
                name="LG화학",
                market_cap=70_000_000_000_000,  # 70조원
                added_date=date.today(),
                is_active=True
            ),
            TargetTicker(
                ticker="006400",
                name="삼성SDI",
                market_cap=50_000_000_000_000,  # 50조원
                added_date=date.today(),
                is_active=True
            )
        ]
        
        added_count = target_ticker_repo.add_multiple_tickers(sample_tickers)
        logger.info(f"Created {added_count} sample target tickers")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        return False


def health_check() -> dict:
    """Perform database health check."""
    result = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database_connection": False,
        "collections_accessible": False,
        "indexes_created": False,
        "sample_data_count": 0
    }
    
    try:
        # Test connection
        if db_manager.is_connected():
            result["database_connection"] = True
            
            # Test collections
            target_ticker_repo = TargetTickerRepository()
            job_status_repo = JobStatusRepository()
            
            ticker_count = target_ticker_repo.count_documents()
            job_count = job_status_repo.count_documents()
            
            result["collections_accessible"] = True
            result["sample_data_count"] = ticker_count
            
            # Check if basic indexes exist
            collections_info = [
                db_manager.system_info_db.target_tickers.index_information(),
                db_manager.system_info_db.job_status.index_information()
            ]
            
            result["indexes_created"] = all(
                len(info) > 1 for info in collections_info  # More than just _id index
            )
            
            logger.info(f"Health check passed: {ticker_count} tickers, {job_count} jobs")
            
        else:
            result["status"] = "unhealthy"
            result["error"] = "Database connection failed"
            
    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)
        logger.error(f"Health check failed: {e}")
    
    return result


def reset_database(confirm: bool = False) -> bool:
    """Reset database (drop all collections). Use with caution!"""
    if not confirm:
        logger.warning("Database reset requires confirmation")
        return False
    
    try:
        logger.warning("Resetting database - all data will be lost!")
        
        # Drop collections
        db_manager.system_info_db.target_tickers.drop()
        db_manager.system_info_db.job_status.drop()
        
        logger.warning("Database reset completed")
        
        # Reinitialize
        return initialize_database()
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            success = initialize_database()
            if success:
                print("Database initialization completed successfully")
            else:
                print("Database initialization failed")
                sys.exit(1)
                
        elif command == "sample":
            initialize_database()
            success = create_sample_data()
            if success:
                print("Sample data created successfully")
            else:
                print("Sample data creation failed")
                sys.exit(1)
                
        elif command == "health":
            result = health_check()
            print(f"Health check result: {result}")
            if result["status"] != "healthy":
                sys.exit(1)
                
        elif command == "reset":
            confirm = len(sys.argv) > 2 and sys.argv[2] == "confirm"
            success = reset_database(confirm)
            if success:
                print("Database reset completed")
            else:
                print("Database reset failed")
                sys.exit(1)
        else:
            print("Usage: python db_init.py [init|sample|health|reset]")
            sys.exit(1)
    else:
        # Default: initialize database
        success = initialize_database()
        if success:
            print("Database initialization completed")
        else:
            print("Database initialization failed")
            sys.exit(1)