"""
Stock screener API routers.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import time
import logging
from datetime import date, timedelta

from database import db_manager
from repositories import TargetTickerRepository
from strategies import strategy_manager
from schemas import ScreenerRequest, ScreenerResponse, AnalyzedStockData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/strategies")
async def list_strategies():
    """List all available screening strategies."""
    try:
        strategies = strategy_manager.list_strategies()
        return {
            "strategies": strategies,
            "total_count": len(strategies)
        }
    except Exception as e:
        logger.error(f"Failed to list strategies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/strategies/{strategy_name}")
async def get_strategy_info(strategy_name: str):
    """Get detailed information about a specific strategy."""
    try:
        strategy = strategy_manager.get_strategy(strategy_name)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found")
        
        return {
            "name": strategy_name,
            "description": strategy.get_description(),
            "parameters": strategy.get_parameters(),
            "parameter_descriptions": _get_parameter_descriptions(strategy_name)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy info for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ScreenerResponse)
async def screen_stocks(request: ScreenerRequest):
    """Screen stocks using the specified strategy."""
    start_time = time.time()
    
    try:
        # Validate strategy exists
        strategy = strategy_manager.get_strategy(request.strategy_name)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy '{request.strategy_name}' not found")
        
        # Get analyzed stock data
        analyzed_data = await _get_analyzed_stock_data(request.limit * 2)  # Get extra data for filtering
        
        if not analyzed_data:
            return ScreenerResponse(
                strategy_name=request.strategy_name,
                matched_tickers=[],
                total_matches=0,
                execution_time_ms=0.0
            )
        
        # Screen stocks using strategy
        screening_results = strategy_manager.screen_stocks(
            request.strategy_name,
            analyzed_data,
            request.parameters
        )
        
        # Limit results
        limited_results = screening_results[:request.limit]
        matched_tickers = [result["ticker"] for result in limited_results]
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return ScreenerResponse(
            strategy_name=request.strategy_name,
            matched_tickers=matched_tickers,
            total_matches=len(screening_results),
            execution_time_ms=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to screen stocks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/")
async def screen_stocks_get(
    strategy_name: str = Query(..., description="Strategy name to use"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=100),
    min_signal_strength: float = Query(0.0, description="Minimum signal strength", ge=0.0, le=1.0),
    **parameters
):
    """Screen stocks using GET method with query parameters."""
    try:
        # Convert query parameters to ScreenerRequest
        # Filter out FastAPI internal parameters
        strategy_params = {
            k: v for k, v in parameters.items() 
            if k not in ["strategy_name", "limit", "min_signal_strength"]
        }
        
        request = ScreenerRequest(
            strategy_name=strategy_name,
            parameters=strategy_params if strategy_params else None,
            limit=limit
        )
        
        # Use the POST endpoint logic
        response = await screen_stocks(request)
        
        # Add additional filtering by signal strength
        if min_signal_strength > 0.0:
            analyzed_data = await _get_analyzed_stock_data_by_tickers(response.matched_tickers)
            screening_results = strategy_manager.screen_stocks(
                strategy_name,
                analyzed_data,
                strategy_params
            )
            
            # Filter by signal strength
            filtered_results = [
                result for result in screening_results 
                if result["signal_strength"] >= min_signal_strength
            ]
            
            response.matched_tickers = [result["ticker"] for result in filtered_results[:limit]]
            response.total_matches = len(filtered_results)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to screen stocks (GET): {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{strategy_name}/detailed")
async def screen_stocks_detailed(
    strategy_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    limit: int = Query(20, description="Maximum number of results", ge=1, le=50)
):
    """Screen stocks with detailed analysis results."""
    start_time = time.time()
    
    try:
        # Validate strategy exists
        strategy = strategy_manager.get_strategy(strategy_name)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found")
        
        # Get analyzed stock data
        analyzed_data = await _get_analyzed_stock_data(limit * 3)
        
        if not analyzed_data:
            return {
                "strategy_name": strategy_name,
                "results": [],
                "total_matches": 0,
                "execution_time_ms": 0.0
            }
        
        # Screen stocks using strategy
        screening_results = strategy_manager.screen_stocks(
            strategy_name,
            analyzed_data,
            parameters
        )
        
        # Limit and return detailed results
        detailed_results = screening_results[:limit]
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "strategy_name": strategy_name,
            "results": detailed_results,
            "total_matches": len(screening_results),
            "execution_time_ms": execution_time,
            "parameters_used": parameters or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get detailed screening results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _get_analyzed_stock_data(limit: int = 200) -> List[AnalyzedStockData]:
    """Get analyzed stock data for screening."""
    try:
        # Get active tickers
        target_ticker_repo = TargetTickerRepository()
        active_tickers = target_ticker_repo.get_all_active()
        
        if not active_tickers:
            return []
        
        # Limit the number of tickers to process
        limited_tickers = active_tickers[:limit]
        
        analyzed_data = []
        target_date = date.today() - timedelta(days=1)  # Use yesterday's data
        
        for ticker_info in limited_tickers:
            try:
                ticker = ticker_info.ticker
                
                # Get most recent analyzed data for this ticker
                analyzed_collection = db_manager.get_collection("stock_analyzed", ticker)
                
                # Find the most recent document
                cursor = analyzed_collection.find().sort("date", -1).limit(1)
                documents = list(cursor)
                
                if not documents:
                    continue
                
                doc = documents[0]
                
                # Parse dates if they are strings
                if isinstance(doc["date"], str):
                    doc["date"] = date.fromisoformat(doc["date"])
                if isinstance(doc["analysis_timestamp"], str):
                    doc["analysis_timestamp"] = date.fromisoformat(doc["analysis_timestamp"])
                
                # Convert to AnalyzedStockData
                analyzed_stock_data = AnalyzedStockData(**doc)
                analyzed_data.append(analyzed_stock_data)
                
            except Exception as e:
                logger.warning(f"Failed to load analyzed data for {ticker_info.ticker}: {e}")
                continue
        
        return analyzed_data
        
    except Exception as e:
        logger.error(f"Failed to get analyzed stock data: {e}")
        return []


async def _get_analyzed_stock_data_by_tickers(tickers: List[str]) -> List[AnalyzedStockData]:
    """Get analyzed stock data for specific tickers."""
    analyzed_data = []
    
    for ticker in tickers:
        try:
            # Get most recent analyzed data for this ticker
            analyzed_collection = db_manager.get_collection("stock_analyzed", ticker)
            
            # Find the most recent document
            cursor = analyzed_collection.find().sort("date", -1).limit(1)
            documents = list(cursor)
            
            if not documents:
                continue
            
            doc = documents[0]
            
            # Parse dates if they are strings
            if isinstance(doc["date"], str):
                doc["date"] = date.fromisoformat(doc["date"])
            if isinstance(doc["analysis_timestamp"], str):
                doc["analysis_timestamp"] = date.fromisoformat(doc["analysis_timestamp"])
            
            # Convert to AnalyzedStockData
            analyzed_stock_data = AnalyzedStockData(**doc)
            analyzed_data.append(analyzed_stock_data)
            
        except Exception as e:
            logger.warning(f"Failed to load analyzed data for {ticker}: {e}")
            continue
    
    return analyzed_data


def _get_parameter_descriptions(strategy_name: str) -> Dict[str, str]:
    """Get parameter descriptions for a strategy."""
    descriptions = {
        "macdgoldencrossstrategy": {
            "min_histogram": "Minimum MACD histogram value for signal confirmation",
            "min_volume_ratio": "Minimum volume ratio compared to average volume",
            "max_rsi": "Maximum RSI value to avoid overbought conditions"
        },
        "rsioversoldstrategy": {
            "max_rsi": "Maximum RSI value for oversold condition",
            "min_rsi": "Minimum RSI value to avoid extreme oversold",
            "require_uptrend": "Whether to require overall uptrend (price > SMA60)",
            "min_volume_ratio": "Minimum volume ratio for confirmation"
        },
        "bollingersqueezestrategy": {
            "max_band_width": "Maximum Bollinger Band width as percentage of middle band",
            "min_volume_ratio": "Minimum volume ratio during squeeze",
            "breakout_threshold": "Price movement percentage to confirm breakout",
            "require_consolidation": "Whether to require price consolidation near middle band"
        },
        "movingaveragecrossoverstrategy": {
            "signal_type": "Type of signal: 'golden_cross', 'death_cross', or 'both'",
            "min_separation": "Minimum separation between moving averages",
            "volume_confirmation": "Whether to require volume confirmation",
            "trend_confirmation": "Whether to require overall trend confirmation"
        }
    }
    
    return descriptions.get(strategy_name.lower(), {})