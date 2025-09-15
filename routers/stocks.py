"""
Stock data API routers.
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
from datetime import date, datetime
import logging

from database import db_manager
from repositories import TargetTickerRepository
from schemas import (
    StockListResponse, StockDetailResponse, TargetTicker, AnalyzedStockData
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=StockListResponse)
async def get_stocks(
    active_only: bool = Query(True, description="Return only active stocks"),
    min_market_cap: Optional[int] = Query(None, description="Minimum market cap filter"),
    limit: int = Query(100, description="Maximum number of stocks to return", ge=1, le=500)
):
    """Get list of tracked stocks."""
    try:
        target_ticker_repo = TargetTickerRepository()
        
        if min_market_cap:
            tickers = target_ticker_repo.get_by_market_cap_range(min_market_cap)
        elif active_only:
            tickers = target_ticker_repo.get_all_active()
        else:
            tickers = target_ticker_repo.get_all_tickers()
        
        # Apply limit
        limited_tickers = tickers[:limit]
        
        # Get counts
        total_count = len(tickers)
        active_count = len([t for t in limited_tickers if t.is_active])
        
        return StockListResponse(
            tickers=limited_tickers,
            total_count=total_count,
            active_count=active_count
        )
        
    except Exception as e:
        logger.error(f"Failed to get stocks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{ticker}", response_model=StockDetailResponse)
async def get_stock_detail(
    ticker: str = Path(..., description="Stock ticker code", min_length=6, max_length=6),
    days: int = Query(30, description="Number of recent days to return", ge=1, le=365)
):
    """Get detailed information for a specific stock."""
    try:
        # Get ticker information
        target_ticker_repo = TargetTickerRepository()
        ticker_info = target_ticker_repo.get_by_ticker(ticker)
        
        if not ticker_info:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
        
        # Get recent analyzed data
        analyzed_collection = db_manager.get_collection("stock_analyzed", ticker)
        
        # Find recent documents, sorted by date descending
        cursor = analyzed_collection.find().sort("date", -1).limit(days)
        documents = list(cursor)
        
        recent_data = []
        last_update = None
        
        for doc in documents:
            try:
                # Parse dates
                if isinstance(doc["date"], str):
                    doc["date"] = date.fromisoformat(doc["date"])
                if isinstance(doc["analysis_timestamp"], str):
                    doc["analysis_timestamp"] = datetime.fromisoformat(doc["analysis_timestamp"])
                
                # Convert to AnalyzedStockData
                analyzed_data = AnalyzedStockData(**doc)
                recent_data.append(analyzed_data)
                
                # Track most recent update
                if last_update is None or analyzed_data.analysis_timestamp > last_update:
                    last_update = analyzed_data.analysis_timestamp
                    
            except Exception as e:
                logger.warning(f"Failed to parse analyzed data for {ticker}: {e}")
                continue
        
        # Sort by date descending (most recent first)
        recent_data.sort(key=lambda x: x.date, reverse=True)
        
        return StockDetailResponse(
            ticker_info=ticker_info,
            recent_data=recent_data,
            last_update=last_update
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stock detail for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{ticker}/raw", response_model=dict)
async def get_stock_raw_data(
    ticker: str = Path(..., description="Stock ticker code", min_length=6, max_length=6),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(30, description="Maximum number of records", ge=1, le=365)
):
    """Get raw OHLCV data for a specific stock."""
    try:
        # Check if ticker exists
        target_ticker_repo = TargetTickerRepository()
        ticker_info = target_ticker_repo.get_by_ticker(ticker)
        
        if not ticker_info:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
        
        # Get raw stock data
        stock_collection = db_manager.get_collection("stock_data", ticker)
        
        # Build query
        query = {"ticker": ticker}
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date.isoformat()
            if end_date:
                date_filter["$lte"] = end_date.isoformat()
            query["date"] = date_filter
        
        # Execute query
        cursor = stock_collection.find(query).sort("date", -1).limit(limit)
        documents = list(cursor)
        
        # Convert ObjectId to string and format dates
        for doc in documents:
            doc["_id"] = str(doc["_id"])
            if "created_at" in doc and isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].isoformat()
        
        return {
            "ticker": ticker,
            "data_count": len(documents),
            "data": documents
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get raw data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{ticker}/statistics", response_model=dict)
async def get_stock_statistics(
    ticker: str = Path(..., description="Stock ticker code", min_length=6, max_length=6)
):
    """Get statistics for a specific stock."""
    try:
        # Check if ticker exists
        target_ticker_repo = TargetTickerRepository()
        ticker_info = target_ticker_repo.get_by_ticker(ticker)
        
        if not ticker_info:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
        
        # Get basic statistics
        stock_collection = db_manager.get_collection("stock_data", ticker)
        analyzed_collection = db_manager.get_collection("stock_analyzed", ticker)
        
        # Raw data statistics
        raw_count = stock_collection.count_documents({"ticker": ticker})
        analyzed_count = analyzed_collection.count_documents({})
        
        # Get date range
        first_doc = stock_collection.find({"ticker": ticker}).sort("date", 1).limit(1)
        last_doc = stock_collection.find({"ticker": ticker}).sort("date", -1).limit(1)
        
        first_doc = list(first_doc)
        last_doc = list(last_doc)
        
        date_range = None
        if first_doc and last_doc:
            date_range = {
                "start_date": first_doc[0]["date"],
                "end_date": last_doc[0]["date"]
            }
        
        # Get recent price data for volatility calculation
        recent_docs = list(stock_collection.find({"ticker": ticker}).sort("date", -1).limit(30))
        
        price_stats = {}
        if recent_docs:
            prices = [doc["close"] for doc in recent_docs]
            volumes = [doc["volume"] for doc in recent_docs]
            
            price_stats = {
                "current_price": prices[0],  # Most recent
                "avg_price_30d": sum(prices) / len(prices),
                "min_price_30d": min(prices),
                "max_price_30d": max(prices),
                "avg_volume_30d": sum(volumes) / len(volumes),
                "price_volatility_30d": _calculate_volatility(prices)
            }
        
        return {
            "ticker": ticker,
            "ticker_info": ticker_info.dict(),
            "data_statistics": {
                "raw_data_count": raw_count,
                "analyzed_data_count": analyzed_count,
                "date_range": date_range,
                "completion_rate": (analyzed_count / raw_count * 100) if raw_count > 0 else 0
            },
            "price_statistics": price_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{ticker}/refresh")
async def refresh_stock_analysis(
    ticker: str = Path(..., description="Stock ticker code", min_length=6, max_length=6)
):
    """Trigger refresh of technical analysis for a specific stock."""
    try:
        # Check if ticker exists and is active
        target_ticker_repo = TargetTickerRepository()
        ticker_info = target_ticker_repo.get_by_ticker(ticker)
        
        if not ticker_info:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
        
        if not ticker_info.is_active:
            raise HTTPException(status_code=400, detail=f"Ticker {ticker} is not active")
        
        # Reset last_analyzed_date to force re-analysis
        success = target_ticker_repo.update_last_analyzed_date(ticker, date(2020, 1, 1))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to trigger refresh")
        
        return {
            "message": f"Analysis refresh triggered for {ticker}",
            "ticker": ticker,
            "status": "queued_for_analysis"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _calculate_volatility(prices: List[float]) -> float:
    """Calculate price volatility (standard deviation)."""
    if len(prices) < 2:
        return 0.0
    
    mean_price = sum(prices) / len(prices)
    variance = sum((price - mean_price) ** 2 for price in prices) / len(prices)
    return variance ** 0.5