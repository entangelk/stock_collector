"""
Pydantic models for data validation and serialization.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status enumeration."""
    RUNNING = "running"
    COMPLETED = "completed" 
    FAILED = "failed"


class TargetTicker(BaseModel):
    """Model for target ticker information."""
    ticker: str = Field(..., description="Stock ticker code", min_length=6, max_length=6)
    name: str = Field(..., description="Company name")
    market_cap: int = Field(..., description="Market capitalization in KRW", gt=0)
    added_date: date = Field(..., description="Date when ticker was added to tracking")
    is_active: bool = Field(default=True, description="Whether ticker is actively being tracked")
    last_analyzed_date: Optional[date] = Field(None, description="Last successful analysis date in KST")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        if not v.isdigit():
            raise ValueError('Ticker must be numeric')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "ticker": "005930",
                "name": "삼성전자",
                "market_cap": 60000000000000,
                "added_date": "2025-09-15",
                "is_active": True,
                "last_analyzed_date": "2025-09-14"
            }
        }


class JobStatusRecord(BaseModel):
    """Model for job execution status record."""
    id: str = Field(..., alias="_id", description="Unique job ID (format: YYYY-MM-DD_job_name)")
    job_name: str = Field(..., description="Name of the job")
    date_kst: date = Field(..., description="Job execution date in KST")
    status: JobStatus = Field(..., description="Job execution status")
    start_time_utc: datetime = Field(..., description="Job start time in UTC")
    end_time_utc: Optional[datetime] = Field(None, description="Job end time in UTC")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    records_processed: Optional[int] = Field(None, description="Number of records processed")
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "_id": "2025-09-15_daily_update",
                "job_name": "daily_update",
                "date_kst": "2025-09-15",
                "status": "completed",
                "start_time_utc": "2025-09-15T10:00:00Z",
                "end_time_utc": "2025-09-15T10:05:12Z",
                "records_processed": 100
            }
        }


class OHLCVData(BaseModel):
    """Model for OHLCV stock data."""
    date: date = Field(..., description="Trading date in KST")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price") 
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume", ge=0)
    ticker: str = Field(..., description="Stock ticker code")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation time in UTC")
    
    @validator('open', 'high', 'low', 'close')
    def validate_prices(cls, v):
        if v <= 0:
            raise ValueError('Prices must be positive')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "date": "2025-09-15",
                "open": 75000,
                "high": 76000,
                "low": 74500,
                "close": 75500,
                "volume": 1234567,
                "ticker": "005930"
            }
        }


class TechnicalIndicators(BaseModel):
    """Model for technical analysis indicators."""
    sma_5: Optional[float] = Field(None, description="5-day Simple Moving Average")
    sma_20: Optional[float] = Field(None, description="20-day Simple Moving Average")
    sma_60: Optional[float] = Field(None, description="60-day Simple Moving Average")
    ema_12: Optional[float] = Field(None, description="12-day Exponential Moving Average")
    ema_26: Optional[float] = Field(None, description="26-day Exponential Moving Average")
    macd: Optional[float] = Field(None, description="MACD line")
    macd_signal: Optional[float] = Field(None, description="MACD Signal line")
    macd_histogram: Optional[float] = Field(None, description="MACD Histogram")
    rsi_14: Optional[float] = Field(None, description="14-day RSI", ge=0, le=100)
    bollinger_upper: Optional[float] = Field(None, description="Bollinger Band Upper")
    bollinger_middle: Optional[float] = Field(None, description="Bollinger Band Middle")
    bollinger_lower: Optional[float] = Field(None, description="Bollinger Band Lower")
    stoch_k: Optional[float] = Field(None, description="Stochastic %K", ge=0, le=100)
    stoch_d: Optional[float] = Field(None, description="Stochastic %D", ge=0, le=100)


class AnalyzedStockData(BaseModel):
    """Model for analyzed stock data with technical indicators."""
    date: date = Field(..., description="Trading date in KST")
    ticker: str = Field(..., description="Stock ticker code")
    ohlcv: OHLCVData = Field(..., description="OHLCV data")
    technical_indicators: TechnicalIndicators = Field(..., description="Technical analysis indicators")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp in UTC")
    
    class Config:
        schema_extra = {
            "example": {
                "date": "2025-09-15",
                "ticker": "005930",
                "ohlcv": {
                    "date": "2025-09-15",
                    "open": 75000,
                    "high": 76000,
                    "low": 74500,
                    "close": 75500,
                    "volume": 1234567,
                    "ticker": "005930"
                },
                "technical_indicators": {
                    "sma_20": 74800,
                    "rsi_14": 65.5,
                    "macd": 123.45
                }
            }
        }


# API Response Models
class StockListResponse(BaseModel):
    """Response model for stock list API."""
    tickers: List[TargetTicker] = Field(..., description="List of tracked stocks")
    total_count: int = Field(..., description="Total number of stocks")
    active_count: int = Field(..., description="Number of active stocks")


class StockDetailResponse(BaseModel):
    """Response model for stock detail API."""
    ticker_info: TargetTicker = Field(..., description="Ticker information")
    recent_data: List[AnalyzedStockData] = Field(..., description="Recent analyzed data", max_items=30)
    last_update: Optional[datetime] = Field(None, description="Last update timestamp")


class ScreenerRequest(BaseModel):
    """Request model for screener API."""
    strategy_name: str = Field(..., description="Strategy name to apply")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")
    limit: int = Field(default=50, description="Maximum number of results", ge=1, le=100)


class ScreenerResponse(BaseModel):
    """Response model for screener API."""
    strategy_name: str = Field(..., description="Applied strategy name") 
    matched_tickers: List[str] = Field(..., description="Tickers matching the strategy")
    total_matches: int = Field(..., description="Total number of matches")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class AIAnalysisRequest(BaseModel):
    """Request model for AI analysis API."""
    tickers: List[str] = Field(..., description="List of tickers to analyze", min_items=1, max_items=10)
    prompt_type: str = Field(..., description="Type of analysis prompt")
    custom_prompt: Optional[str] = Field(None, description="Custom analysis prompt")


class AIAnalysisResponse(BaseModel):
    """Response model for AI analysis API."""
    analysis_result: str = Field(..., description="AI-generated analysis")
    analyzed_tickers: List[str] = Field(..., description="List of analyzed tickers")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    model_used: str = Field(default="gemini", description="AI model used for analysis")