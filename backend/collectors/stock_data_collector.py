"""
Stock data collector using pykrx library.
"""
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
import logging
from time import sleep
import pykrx.stock.stock as krx_stock

from schemas import OHLCVData, TargetTicker
from utils import get_kst_today, is_business_day, get_business_days_between
from config import settings

logger = logging.getLogger(__name__)


class StockDataCollector:
    """Collector for Korean stock market data using pykrx."""
    
    def __init__(self):
        self.request_delay = 0.1  # 100ms delay between requests to avoid rate limiting
    
    def get_market_tickers(self, market: str = "ALL", 
                          date: Optional[date] = None) -> List[str]:
        """Get all tickers for specified market."""
        if date is None:
            date = get_kst_today()
            # If today is not a business day, use previous business day
            while not is_business_day(date):
                date -= timedelta(days=1)
        
        date_str = date.strftime("%Y%m%d")
        
        try:
            if market.upper() == "ALL":
                kospi_tickers = krx_stock.get_market_ticker_list(date_str, market="KOSPI")
                kosdaq_tickers = krx_stock.get_market_ticker_list(date_str, market="KOSDAQ")
                return kospi_tickers + kosdaq_tickers
            else:
                return krx_stock.get_market_ticker_list(date_str, market=market.upper())
        except Exception as e:
            logger.error(f"Failed to get market tickers for {market}: {e}")
            return []
    
    def get_ticker_info(self, ticker: str, 
                       date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """Get basic information about a ticker."""
        if date is None:
            date = get_kst_today()
            while not is_business_day(date):
                date -= timedelta(days=1)
        
        date_str = date.strftime("%Y%m%d")
        
        try:
            # Get ticker name
            ticker_name = krx_stock.get_market_ticker_name(ticker)
            
            # Get market cap
            market_cap_df = krx_stock.get_market_cap_by_ticker(date_str, ticker)
            
            if market_cap_df.empty:
                logger.warning(f"No market cap data found for {ticker} on {date_str}")
                return None
            
            # Market cap is in units of 100 million won, convert to won
            market_cap = market_cap_df.iloc[0]['시가총액'] * 100_000_000
            
            return {
                "ticker": ticker,
                "name": ticker_name,
                "market_cap": market_cap,
                "date": date
            }
            
        except Exception as e:
            logger.error(f"Failed to get ticker info for {ticker}: {e}")
            return None
    
    def get_ohlcv_data(self, ticker: str, start_date: date, 
                      end_date: date) -> List[OHLCVData]:
        """Get OHLCV data for a ticker within date range."""
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        try:
            df = krx_stock.get_market_ohlcv_by_ticker(start_str, end_str, ticker)
            
            if df.empty:
                logger.warning(f"No OHLCV data found for {ticker} from {start_date} to {end_date}")
                return []
            
            ohlcv_data = []
            for date_idx, row in df.iterrows():
                ohlcv = OHLCVData(
                    date=date_idx.date(),
                    open=float(row['시가']),
                    high=float(row['고가']), 
                    low=float(row['저가']),
                    close=float(row['종가']),
                    volume=int(row['거래량']),
                    ticker=ticker
                )
                ohlcv_data.append(ohlcv)
            
            logger.debug(f"Collected {len(ohlcv_data)} OHLCV records for {ticker}")
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Failed to get OHLCV data for {ticker}: {e}")
            return []
    
    def get_single_day_ohlcv(self, ticker: str, target_date: date) -> Optional[OHLCVData]:
        """Get OHLCV data for a single day."""
        data = self.get_ohlcv_data(ticker, target_date, target_date)
        return data[0] if data else None
    
    def collect_large_cap_tickers(self, min_market_cap: int = None,
                                 target_date: Optional[date] = None) -> List[TargetTicker]:
        """Collect tickers with market cap above threshold."""
        if min_market_cap is None:
            min_market_cap = settings.min_market_cap
        
        if target_date is None:
            target_date = get_kst_today()
            while not is_business_day(target_date):
                target_date -= timedelta(days=1)
        
        logger.info(f"Collecting large cap tickers with min market cap: {min_market_cap:,}")
        
        # Get all tickers
        all_tickers = self.get_market_tickers("ALL", target_date)
        large_cap_tickers = []
        
        for i, ticker in enumerate(all_tickers):
            try:
                ticker_info = self.get_ticker_info(ticker, target_date)
                
                if ticker_info and ticker_info["market_cap"] >= min_market_cap:
                    target_ticker = TargetTicker(
                        ticker=ticker,
                        name=ticker_info["name"],
                        market_cap=ticker_info["market_cap"],
                        added_date=target_date,
                        is_active=True
                    )
                    large_cap_tickers.append(target_ticker)
                    logger.info(f"Added {ticker} ({ticker_info['name']}) - "
                              f"Market Cap: {ticker_info['market_cap']:,}")
                
                # Rate limiting
                sleep(self.request_delay)
                
                # Progress logging
                if (i + 1) % 50 == 0:
                    logger.info(f"Processed {i + 1}/{len(all_tickers)} tickers, "
                              f"found {len(large_cap_tickers)} large cap stocks")
                
            except Exception as e:
                logger.warning(f"Skipping ticker {ticker} due to error: {e}")
                continue
        
        logger.info(f"Collected {len(large_cap_tickers)} large cap tickers")
        return large_cap_tickers
    
    def collect_historical_data(self, ticker: str, days_back: int = 300) -> List[OHLCVData]:
        """Collect historical data for a ticker."""
        end_date = get_kst_today()
        
        # Find the last business day
        while not is_business_day(end_date):
            end_date -= timedelta(days=1)
        
        # Calculate start date (approximately, will be filtered by business days)
        start_date = end_date - timedelta(days=days_back * 2)  # Buffer for weekends/holidays
        
        # Get business days in range
        business_days = get_business_days_between(start_date, end_date)
        
        if len(business_days) > days_back:
            actual_start_date = business_days[-days_back]  # Last N business days
        else:
            actual_start_date = business_days[0] if business_days else start_date
        
        logger.info(f"Collecting historical data for {ticker} from {actual_start_date} to {end_date}")
        
        return self.get_ohlcv_data(ticker, actual_start_date, end_date)
    
    def collect_missing_data(self, ticker: str, missing_dates: List[date]) -> List[OHLCVData]:
        """Collect data for specific missing dates."""
        if not missing_dates:
            return []
        
        # Group consecutive dates to minimize API calls
        date_ranges = self._group_consecutive_dates(missing_dates)
        all_data = []
        
        for start_date, end_date in date_ranges:
            data = self.get_ohlcv_data(ticker, start_date, end_date)
            all_data.extend(data)
            sleep(self.request_delay)  # Rate limiting
        
        logger.info(f"Collected {len(all_data)} missing records for {ticker}")
        return all_data
    
    def _group_consecutive_dates(self, dates: List[date]) -> List[tuple[date, date]]:
        """Group consecutive dates into ranges."""
        if not dates:
            return []
        
        sorted_dates = sorted(dates)
        ranges = []
        start = sorted_dates[0]
        end = sorted_dates[0]
        
        for i in range(1, len(sorted_dates)):
            current_date = sorted_dates[i]
            if (current_date - end).days <= 3:  # Allow small gaps for weekends
                end = current_date
            else:
                ranges.append((start, end))
                start = current_date
                end = current_date
        
        ranges.append((start, end))
        return ranges
    
    def validate_data_integrity(self, ticker: str, data: List[OHLCVData]) -> Dict[str, Any]:
        """Validate collected data for basic integrity."""
        if not data:
            return {"valid": False, "error": "No data provided"}
        
        issues = []
        
        # Check for missing dates
        dates = [d.date for d in data]
        date_gaps = []
        
        for i in range(1, len(dates)):
            current_date = dates[i]
            prev_date = dates[i-1]
            
            expected_business_days = get_business_days_between(
                prev_date + timedelta(days=1), current_date - timedelta(days=1)
            )
            
            if expected_business_days:
                date_gaps.extend(expected_business_days)
        
        if date_gaps:
            issues.append(f"Missing data for {len(date_gaps)} business days")
        
        # Check for invalid prices
        invalid_prices = []
        for d in data:
            if d.open <= 0 or d.high <= 0 or d.low <= 0 or d.close <= 0:
                invalid_prices.append(d.date)
            if d.high < d.low:
                invalid_prices.append(d.date)
        
        if invalid_prices:
            issues.append(f"Invalid prices on {len(invalid_prices)} dates")
        
        # Check for extreme volume
        volumes = [d.volume for d in data]
        if volumes:
            avg_volume = sum(volumes) / len(volumes)
            extreme_volumes = [
                d.date for d in data 
                if d.volume > avg_volume * 10 or d.volume < avg_volume * 0.1
            ]
            
            if extreme_volumes:
                issues.append(f"Extreme volumes on {len(extreme_volumes)} dates")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_records": len(data),
            "date_range": f"{min(dates)} to {max(dates)}" if dates else "N/A",
            "missing_dates": date_gaps[:10],  # First 10 missing dates
            "avg_volume": sum(volumes) / len(volumes) if volumes else 0
        }