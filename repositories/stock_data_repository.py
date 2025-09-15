"""
Repository for stock OHLCV data operations.
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import logging

from repositories.base import BaseRepository
from schemas import OHLCVData

logger = logging.getLogger(__name__)


class StockDataRepository(BaseRepository):
    """Repository for managing stock OHLCV data."""
    
    def __init__(self, ticker: str):
        super().__init__("stock_data", ticker)
        self.ticker = ticker
    
    def add_ohlcv_data(self, ohlcv: OHLCVData) -> bool:
        """Add OHLCV data for a specific date."""
        try:
            doc = ohlcv.dict()
            doc["date"] = ohlcv.date.isoformat() if isinstance(ohlcv.date, date) else ohlcv.date
            
            # Use upsert to prevent duplicates
            filter_dict = {"date": doc["date"], "ticker": self.ticker}
            result = self.upsert(filter_dict, doc)
            
            if result:
                logger.debug(f"Added OHLCV data for {self.ticker} on {doc['date']}")
            return result
        except Exception as e:
            logger.error(f"Failed to add OHLCV data for {self.ticker}: {e}")
            return False
    
    def add_multiple_ohlcv_data(self, ohlcv_list: List[OHLCVData]) -> int:
        """Add multiple OHLCV data records."""
        added_count = 0
        for ohlcv in ohlcv_list:
            if self.add_ohlcv_data(ohlcv):
                added_count += 1
        return added_count
    
    def get_by_date(self, target_date: date) -> Optional[OHLCVData]:
        """Get OHLCV data for specific date."""
        date_str = target_date.isoformat() if isinstance(target_date, date) else target_date
        doc = self.find_one({"date": date_str, "ticker": self.ticker})
        if doc:
            return OHLCVData(**doc)
        return None
    
    def get_date_range(self, start_date: date, end_date: date) -> List[OHLCVData]:
        """Get OHLCV data for date range."""
        start_str = start_date.isoformat() if isinstance(start_date, date) else start_date
        end_str = end_date.isoformat() if isinstance(end_date, date) else end_date
        
        filter_dict = {
            "ticker": self.ticker,
            "date": {"$gte": start_str, "$lte": end_str}
        }
        
        docs = self.find_many(filter_dict, sort=[("date", 1)])
        return [OHLCVData(**doc) for doc in docs]
    
    def get_recent_data(self, limit: int = 30) -> List[OHLCVData]:
        """Get most recent OHLCV data."""
        docs = self.find_many(
            {"ticker": self.ticker},
            sort=[("date", -1)],
            limit=limit
        )
        return [OHLCVData(**doc) for doc in docs]
    
    def get_last_trading_date(self) -> Optional[date]:
        """Get the last trading date with data."""
        docs = self.find_many(
            {"ticker": self.ticker},
            sort=[("date", -1)],
            limit=1
        )
        if docs:
            date_str = docs[0]["date"]
            if isinstance(date_str, str):
                return date.fromisoformat(date_str)
            return date_str
        return None
    
    def get_data_count(self, start_date: Optional[date] = None) -> int:
        """Get count of data records."""
        filter_dict = {"ticker": self.ticker}
        if start_date:
            start_str = start_date.isoformat() if isinstance(start_date, date) else start_date
            filter_dict["date"] = {"$gte": start_str}
        
        return self.count_documents(filter_dict)
    
    def get_missing_dates(self, start_date: date, end_date: date, 
                         trading_dates: List[date]) -> List[date]:
        """Find missing trading dates in the data."""
        existing_docs = self.get_date_range(start_date, end_date)
        existing_dates = {
            date.fromisoformat(doc.date) if isinstance(doc.date, str) else doc.date 
            for doc in existing_docs
        }
        
        trading_dates_set = set(trading_dates)
        missing_dates = trading_dates_set - existing_dates
        
        return sorted(list(missing_dates))
    
    def get_price_statistics(self, days_back: int = 30) -> Dict[str, float]:
        """Get price statistics for recent period."""
        recent_data = self.get_recent_data(limit=days_back)
        
        if not recent_data:
            return {}
        
        prices = [data.close for data in recent_data]
        volumes = [data.volume for data in recent_data]
        
        return {
            "current_price": prices[0],  # Most recent is first due to desc sort
            "avg_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "price_volatility": self._calculate_volatility(prices),
            "avg_volume": sum(volumes) / len(volumes),
            "total_volume": sum(volumes)
        }
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility (standard deviation)."""
        if len(prices) < 2:
            return 0.0
        
        mean_price = sum(prices) / len(prices)
        variance = sum((price - mean_price) ** 2 for price in prices) / len(prices)
        return variance ** 0.5
    
    def delete_data_before_date(self, cutoff_date: date) -> int:
        """Delete data before specified date."""
        cutoff_str = cutoff_date.isoformat() if isinstance(cutoff_date, date) else cutoff_date
        
        try:
            deleted_count = self.delete_many({
                "ticker": self.ticker,
                "date": {"$lt": cutoff_str}
            })
            logger.info(f"Deleted {deleted_count} old records for {self.ticker}")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old data for {self.ticker}: {e}")
            return 0
    
    def backup_to_dict(self) -> List[Dict[str, Any]]:
        """Export all data as list of dictionaries."""
        docs = self.find_many({"ticker": self.ticker}, sort=[("date", 1)])
        return docs
    
    def restore_from_dict(self, data_list: List[Dict[str, Any]]) -> int:
        """Restore data from list of dictionaries."""
        try:
            # Add ticker and created_at if missing
            for doc in data_list:
                if "ticker" not in doc:
                    doc["ticker"] = self.ticker
                if "created_at" not in doc:
                    doc["created_at"] = datetime.utcnow()
            
            self.insert_many(data_list)
            logger.info(f"Restored {len(data_list)} records for {self.ticker}")
            return len(data_list)
        except Exception as e:
            logger.error(f"Failed to restore data for {self.ticker}: {e}")
            return 0