"""
Base repository class for data access operations.
"""
from typing import Optional, List, Dict, Any, TypeVar, Generic
from abc import ABC, abstractmethod
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError
import logging
from datetime import datetime

from database import db_manager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """Base repository for common database operations."""
    
    def __init__(self, db_name: str, collection_name: str):
        self.db_name = db_name
        self.collection_name = collection_name
    
    @property
    def collection(self) -> Collection:
        """Get the MongoDB collection."""
        return db_manager.get_collection(self.db_name, self.collection_name)
    
    def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        try:
            return self.collection.find_one(filter_dict)
        except PyMongoError as e:
            logger.error(f"Error finding document: {e}")
            raise
    
    def find_many(self, filter_dict: Dict[str, Any], 
                  limit: Optional[int] = None, 
                  sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        try:
            cursor = self.collection.find(filter_dict)
            
            if sort:
                cursor = cursor.sort(sort)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except PyMongoError as e:
            logger.error(f"Error finding documents: {e}")
            raise
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert a single document."""
        try:
            result = self.collection.insert_one(document)
            logger.debug(f"Inserted document with id: {result.inserted_id}")
            return str(result.inserted_id)
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate key error: {e}")
            raise
        except PyMongoError as e:
            logger.error(f"Error inserting document: {e}")
            raise
    
    def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents."""
        try:
            result = self.collection.insert_many(documents)
            logger.debug(f"Inserted {len(result.inserted_ids)} documents")
            return [str(id) for id in result.inserted_ids]
        except PyMongoError as e:
            logger.error(f"Error inserting documents: {e}")
            raise
    
    def update_one(self, filter_dict: Dict[str, Any], 
                   update_dict: Dict[str, Any], 
                   upsert: bool = False) -> bool:
        """Update a single document."""
        try:
            result = self.collection.update_one(
                filter_dict, 
                {"$set": update_dict}, 
                upsert=upsert
            )
            logger.debug(f"Updated {result.modified_count} documents")
            return result.modified_count > 0 or (upsert and result.upserted_id is not None)
        except PyMongoError as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    def update_many(self, filter_dict: Dict[str, Any], 
                    update_dict: Dict[str, Any]) -> int:
        """Update multiple documents."""
        try:
            result = self.collection.update_many(
                filter_dict, 
                {"$set": update_dict}
            )
            logger.debug(f"Updated {result.modified_count} documents")
            return result.modified_count
        except PyMongoError as e:
            logger.error(f"Error updating documents: {e}")
            raise
    
    def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document."""
        try:
            result = self.collection.delete_one(filter_dict)
            logger.debug(f"Deleted {result.deleted_count} documents")
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting document: {e}")
            raise
    
    def delete_many(self, filter_dict: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        try:
            result = self.collection.delete_many(filter_dict)
            logger.debug(f"Deleted {result.deleted_count} documents")
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Error deleting documents: {e}")
            raise
    
    def count_documents(self, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents matching filter."""
        try:
            if filter_dict is None:
                filter_dict = {}
            return self.collection.count_documents(filter_dict)
        except PyMongoError as e:
            logger.error(f"Error counting documents: {e}")
            raise
    
    def upsert(self, filter_dict: Dict[str, Any], 
               document: Dict[str, Any]) -> bool:
        """Insert or update document."""
        document['updated_at'] = datetime.utcnow()
        return self.update_one(filter_dict, document, upsert=True)
    
    def create_index(self, index_spec: List[tuple], **kwargs) -> str:
        """Create index on collection."""
        try:
            return self.collection.create_index(index_spec, **kwargs)
        except PyMongoError as e:
            logger.error(f"Error creating index: {e}")
            raise
    
    def drop_collection(self) -> None:
        """Drop the entire collection."""
        try:
            self.collection.drop()
            logger.warning(f"Dropped collection: {self.collection_name}")
        except PyMongoError as e:
            logger.error(f"Error dropping collection: {e}")
            raise