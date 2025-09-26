"""
Repository for target ticker operations.
"""
from typing import List, Optional
from datetime import date, datetime
import logging

from repositories.base import BaseRepository
from schemas import TargetTicker

logger = logging.getLogger(__name__)


class TargetTickerRepository(BaseRepository):
    """Repository for managing target ticker data."""
    
    def __init__(self):
        super().__init__("system_info", "target_tickers")
    
    def get_by_ticker(self, ticker: str) -> Optional[TargetTicker]:
        """Get target ticker by ticker code."""
        doc = self.find_one({"ticker": ticker})
        if doc:
            return TargetTicker(**doc)
        return None
    
    def get_all_active(self) -> List[TargetTicker]:
        """Get all active target tickers."""
        docs = self.find_many({"is_active": True})
        return [TargetTicker(**doc) for doc in docs]
    
    def get_all_tickers(self) -> List[TargetTicker]:
        """Get all target tickers."""
        docs = self.find_many({})
        return [TargetTicker(**doc) for doc in docs]
    
    def get_by_market_cap_range(self, min_cap: int, max_cap: Optional[int] = None) -> List[TargetTicker]:
        """Get tickers by market cap range."""
        filter_dict = {"market_cap": {"$gte": min_cap}, "is_active": True}
        if max_cap:
            filter_dict["market_cap"]["$lte"] = max_cap
        
        docs = self.find_many(filter_dict, sort=[("market_cap", -1)])
        return [TargetTicker(**doc) for doc in docs]
    
    def get_pending_analysis(self, target_date: date) -> List[TargetTicker]:
        """Get tickers that need analysis for target date."""
        filter_dict = {
            "is_active": True,
            "$or": [
                {"last_analyzed_date": {"$lt": target_date}},
                {"last_analyzed_date": {"$exists": False}},
                {"last_analyzed_date": None}
            ]
        }
        
        docs = self.find_many(filter_dict, sort=[("market_cap", -1)])
        return [TargetTicker(**doc) for doc in docs]
    
    def add_ticker(self, ticker_data: TargetTicker) -> bool:
        """Add new target ticker."""
        try:
            doc = ticker_data.dict()
            doc["added_date"] = ticker_data.added_date.isoformat() if isinstance(ticker_data.added_date, date) else ticker_data.added_date
            if ticker_data.last_analyzed_date:
                doc["last_analyzed_date"] = ticker_data.last_analyzed_date.isoformat() if isinstance(ticker_data.last_analyzed_date, date) else ticker_data.last_analyzed_date
            
            self.insert_one(doc)
            logger.info(f"Added ticker: {ticker_data.ticker}")
            return True
        except Exception as e:
            logger.error(f"Failed to add ticker {ticker_data.ticker}: {e}")
            return False
    
    def add_multiple_tickers(self, tickers: List[TargetTicker]) -> int:
        """Add multiple target tickers."""
        added_count = 0
        for ticker in tickers:
            if self.add_ticker(ticker):
                added_count += 1
        return added_count
    
    def update_last_analyzed_date(self, ticker: str, analyzed_date: date) -> bool:
        """Update last analyzed date for ticker."""
        try:
            date_str = analyzed_date.isoformat() if isinstance(analyzed_date, date) else analyzed_date
            result = self.update_one(
                {"ticker": ticker},
                {"last_analyzed_date": date_str, "updated_at": datetime.utcnow()}
            )
            if result:
                logger.debug(f"Updated last_analyzed_date for {ticker} to {date_str}")
            return result
        except Exception as e:
            logger.error(f"Failed to update last_analyzed_date for {ticker}: {e}")
            return False
    
    def deactivate_ticker(self, ticker: str) -> bool:
        """Deactivate a ticker (set is_active to False)."""
        try:
            result = self.update_one(
                {"ticker": ticker},
                {"is_active": False, "updated_at": datetime.utcnow()}
            )
            if result:
                logger.info(f"Deactivated ticker: {ticker}")
            return result
        except Exception as e:
            logger.error(f"Failed to deactivate ticker {ticker}: {e}")
            return False
    
    def activate_ticker(self, ticker: str) -> bool:
        """Activate a ticker (set is_active to True)."""
        try:
            result = self.update_one(
                {"ticker": ticker},
                {"is_active": True, "updated_at": datetime.utcnow()}
            )
            if result:
                logger.info(f"Activated ticker: {ticker}")
            return result
        except Exception as e:
            logger.error(f"Failed to activate ticker {ticker}: {e}")
            return False
    
    def update_market_cap(self, ticker: str, market_cap: int) -> bool:
        """Update market cap for ticker."""
        try:
            result = self.update_one(
                {"ticker": ticker},
                {"market_cap": market_cap, "updated_at": datetime.utcnow()}
            )
            if result:
                logger.debug(f"Updated market_cap for {ticker} to {market_cap}")
            return result
        except Exception as e:
            logger.error(f"Failed to update market_cap for {ticker}: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """Get statistics about target tickers."""
        total_count = self.count_documents()
        active_count = self.count_documents({"is_active": True})
        
        # Get market cap statistics for active tickers
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": None,
                "avg_market_cap": {"$avg": "$market_cap"},
                "min_market_cap": {"$min": "$market_cap"},
                "max_market_cap": {"$max": "$market_cap"},
                "total_market_cap": {"$sum": "$market_cap"}
            }}
        ]
        
        stats = list(self.collection.aggregate(pipeline))
        market_cap_stats = stats[0] if stats else {}
        
        return {
            "total_tickers": total_count,
            "active_tickers": active_count,
            "inactive_tickers": total_count - active_count,
            "market_cap_stats": market_cap_stats
        }