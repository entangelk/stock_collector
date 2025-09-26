"""
MongoDB database connection and management.
"""
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from contextlib import contextmanager

from config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """MongoDB database connection manager."""
    
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._databases: dict[str, Database] = {}
    
    def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self._client = MongoClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                maxPoolSize=50,
                minPoolSize=5
            )
            
            # Test connection
            self._client.admin.command('ping')
            
            # Initialize database references
            db_names = settings.get_database_names()
            for db_key, db_name in db_names.items():
                self._databases[db_key] = self._client[db_name]
            
            logger.info(f"Connected to MongoDB at {settings.mongodb_url}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._databases.clear()
            logger.info("Disconnected from MongoDB")
    
    def get_database(self, db_name: str) -> Database:
        """Get database by name."""
        if db_name not in self._databases:
            raise ValueError(f"Database {db_name} not found. Available: {list(self._databases.keys())}")
        return self._databases[db_name]
    
    def get_collection(self, db_name: str, collection_name: str) -> Collection:
        """Get collection from specified database."""
        database = self.get_database(db_name)
        return database[collection_name]
    
    @property
    def system_info_db(self) -> Database:
        """Get system_info database."""
        return self.get_database("system_info")
    
    @property
    def stock_data_db(self) -> Database:
        """Get stock_data database."""
        return self.get_database("stock_data")
    
    @property
    def stock_analyzed_db(self) -> Database:
        """Get stock_analyzed database."""
        return self.get_database("stock_analyzed")
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        if not self._client:
            return False
        try:
            self._client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def create_indexes(self) -> None:
        """Create necessary indexes for optimal performance."""
        try:
            # target_tickers collection indexes
            target_tickers = self.get_collection("system_info", "target_tickers")
            target_tickers.create_index("ticker", unique=True)
            target_tickers.create_index("market_cap")
            target_tickers.create_index("is_active")
            target_tickers.create_index("last_analyzed_date")
            
            # job_status collection indexes
            job_status = self.get_collection("system_info", "job_status")
            job_status.create_index("job_name")
            job_status.create_index("date_kst")
            job_status.create_index("status")
            job_status.create_index("start_time_utc")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()


@contextmanager
def get_database_session():
    """Context manager for database sessions."""
    try:
        if not db_manager.is_connected():
            db_manager.connect()
        yield db_manager
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
    finally:
        # Keep connection alive for reuse
        pass


# Convenience functions
def get_target_tickers_collection() -> Collection:
    """Get target_tickers collection."""
    return db_manager.get_collection("system_info", "target_tickers")


def get_job_status_collection() -> Collection:
    """Get job_status collection."""
    return db_manager.get_collection("system_info", "job_status")


def get_stock_data_collection(ticker: str) -> Collection:
    """Get stock data collection for specific ticker."""
    return db_manager.get_collection("stock_data", ticker)


def get_stock_analyzed_collection(ticker: str) -> Collection:
    """Get analyzed stock data collection for specific ticker."""
    return db_manager.get_collection("stock_analyzed", ticker)