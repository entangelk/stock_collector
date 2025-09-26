"""
Hourly technical analysis script with state-based recovery.

This script runs every hour from 19:10 KST to 08:10 KST (next day) on business days.
It performs technical analysis on stocks and updates the analyzed database.

Cron schedule: 
- 10 19-23 * * 1-5 (Mon-Fri 19:10-23:10)
- 10 0-8 * * 1-5 (Mon-Fri 00:10-08:10)
"""
import logging
import sys
from datetime import date, datetime, timedelta
from typing import List, Optional
import time

from database import db_manager
from repositories import (
    TargetTickerRepository, JobStatusRepository, 
    StockDataRepository
)
from collectors import TechnicalAnalyzer
from schemas import AnalyzedStockData
from utils import get_kst_today, get_kst_now
from config import settings


def setup_logging():
    """Setup logging for hourly analysis process."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("logs/hourly_analysis.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def initialize_components():
    """Initialize database and components."""
    logger = logging.getLogger(__name__)
    
    try:
        # Connect to database
        db_manager.connect()
        
        # Initialize repositories and analyzer
        target_ticker_repo = TargetTickerRepository()
        job_status_repo = JobStatusRepository()
        analyzer = TechnicalAnalyzer()
        
        logger.info("Components initialized successfully")
        return target_ticker_repo, job_status_repo, analyzer
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


def check_prerequisites(job_status_repo: JobStatusRepository, 
                       target_date: date) -> bool:
    """Check if daily_update completed for the target date."""
    logger = logging.getLogger(__name__)
    
    # Check if daily_update completed for target date
    daily_job_status = job_status_repo.get_job_status("daily_update", target_date)
    
    if daily_job_status is None:
        logger.warning(f"No daily_update job found for {target_date}")
        return False
    
    if daily_job_status.status.value != "completed":
        logger.warning(f"Daily_update for {target_date} not completed yet (status: {daily_job_status.status.value})")
        return False
    
    logger.info(f"Daily_update for {target_date} completed successfully")
    return True


def get_pending_analysis_tickers(target_ticker_repo: TargetTickerRepository,
                                target_date: date,
                                max_count: int = None) -> List:
    """Get tickers that need analysis for target date."""
    logger = logging.getLogger(__name__)
    
    if max_count is None:
        max_count = settings.max_analysis_per_hour
    
    # Get tickers that haven't been analyzed for target date
    pending_tickers = target_ticker_repo.get_pending_analysis(target_date)
    
    if not pending_tickers:
        logger.info(f"No tickers need analysis for {target_date}")
        return []
    
    # Sort by market cap (descending) for priority processing
    pending_tickers.sort(key=lambda x: x.market_cap, reverse=True)
    
    # Limit to max_count
    limited_tickers = pending_tickers[:max_count]
    
    logger.info(f"Found {len(pending_tickers)} pending tickers, processing {len(limited_tickers)} this hour")
    return limited_tickers


def analyze_ticker(ticker: str, target_date: date, 
                  analyzer: TechnicalAnalyzer) -> Optional[List[AnalyzedStockData]]:
    """Analyze a single ticker for target date."""
    logger = logging.getLogger(__name__)
    
    try:
        # Get stock data repository for this ticker
        stock_repo = StockDataRepository(ticker)
        
        # Get historical data (we need enough data for technical indicators)
        # Get last 100 business days to ensure we have enough for 60-day SMA
        end_date = target_date
        start_date = target_date - timedelta(days=200)  # Buffer for weekends/holidays
        
        historical_data = stock_repo.get_date_range(start_date, end_date)
        
        if len(historical_data) < 60:  # Minimum data for technical analysis
            logger.warning(f"  Insufficient data for {ticker}: {len(historical_data)} records")
            return None
        
        # Perform technical analysis
        analyzed_data = analyzer.analyze_ohlcv_data(historical_data)
        
        if not analyzed_data:
            logger.warning(f"  No analysis results for {ticker}")
            return None
        
        # Filter to only return data for target_date and recent dates
        recent_data = [
            data for data in analyzed_data 
            if data.date >= target_date - timedelta(days=30)
        ]
        
        logger.debug(f"  Analyzed {ticker}: {len(analyzed_data)} total, {len(recent_data)} recent")
        return recent_data
        
    except Exception as e:
        logger.error(f"  Failed to analyze {ticker}: {e}")
        return None


def store_analyzed_data(ticker: str, analyzed_data: List[AnalyzedStockData]) -> bool:
    """Store analyzed data in the database."""
    logger = logging.getLogger(__name__)
    
    try:
        # Get analyzed stock collection for this ticker
        analyzed_collection = db_manager.get_collection("stock_analyzed", ticker)
        
        # Convert to documents for storage
        documents = []
        for data in analyzed_data:
            doc = data.dict()
            doc["date"] = data.date.isoformat()
            doc["analysis_timestamp"] = data.analysis_timestamp.isoformat()
            documents.append(doc)
        
        if not documents:
            return True
        
        # Clear existing data and insert new data (overwrite approach)
        analyzed_collection.delete_many({})
        result = analyzed_collection.insert_many(documents)
        
        logger.debug(f"  Stored {len(result.inserted_ids)} analyzed records for {ticker}")
        return True
        
    except Exception as e:
        logger.error(f"  Failed to store analyzed data for {ticker}: {e}")
        return False


def run_hourly_analysis(max_runtime_minutes: int = None):
    """Main hourly analysis process with state-based recovery."""
    logger = logging.getLogger(__name__)
    
    if max_runtime_minutes is None:
        max_runtime_minutes = settings.analysis_time_limit_minutes
    
    start_time = datetime.now()
    target_date = get_kst_today()
    
    # Use yesterday's date if it's early morning (before 09:00)
    current_time = get_kst_now()
    if current_time.hour < 9:
        target_date = target_date - timedelta(days=1)
    
    logger.info(f"Starting hourly analysis for date: {target_date}")
    logger.info(f"Maximum runtime: {max_runtime_minutes} minutes")
    
    try:
        # Initialize components
        target_ticker_repo, job_status_repo, analyzer = initialize_components()
        
        # Check prerequisites (daily_update must be completed)
        if not check_prerequisites(job_status_repo, target_date):
            logger.error("Prerequisites not met. Exiting.")
            return False
        
        # Get tickers that need analysis
        pending_tickers = get_pending_analysis_tickers(
            target_ticker_repo, target_date
        )
        
        if not pending_tickers:
            logger.info("No tickers need analysis")
            return True
        
        # Process tickers with time limit
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for ticker_info in pending_tickers:
            ticker = ticker_info.ticker
            
            # Check time limit
            elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
            if elapsed_minutes >= max_runtime_minutes:
                logger.info(f"Time limit reached ({max_runtime_minutes} minutes). Stopping.")
                break
            
            logger.info(f"Analyzing {ticker} ({ticker_info.name}) - {processed_count + 1}/{len(pending_tickers)}")
            
            try:
                # Analyze ticker
                analyzed_data = analyze_ticker(ticker, target_date, analyzer)
                
                if analyzed_data is None:
                    error_count += 1
                    processed_count += 1
                    continue
                
                # Store analyzed data
                if store_analyzed_data(ticker, analyzed_data):
                    # Update last_analyzed_date
                    target_ticker_repo.update_last_analyzed_date(ticker, target_date)
                    success_count += 1
                    logger.info(f"  Successfully analyzed {ticker}")
                else:
                    error_count += 1
                    logger.warning(f"  Failed to store analysis for {ticker}")
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"  Error processing {ticker}: {e}")
                error_count += 1
                processed_count += 1
                continue
        
        # Log summary
        total_time = (datetime.now() - start_time).total_seconds() / 60
        
        logger.info("=" * 60)
        logger.info(f"Hourly analysis completed!")
        logger.info(f"Target date: {target_date}")
        logger.info(f"Processed: {processed_count}/{len(pending_tickers)} tickers")
        logger.info(f"Success: {success_count}, Errors: {error_count}")
        logger.info(f"Runtime: {total_time:.1f} minutes")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Hourly analysis failed: {e}")
        return False


def get_analysis_status(target_date: Optional[date] = None) -> dict:
    """Get current analysis status for monitoring."""
    logger = logging.getLogger(__name__)
    
    if target_date is None:
        target_date = get_kst_today()
        current_time = get_kst_now()
        if current_time.hour < 9:
            target_date = target_date - timedelta(days=1)
    
    try:
        db_manager.connect()
        target_ticker_repo = TargetTickerRepository()
        job_status_repo = JobStatusRepository()
        
        # Get total active tickers
        all_active = target_ticker_repo.get_all_active()
        total_active = len(all_active)
        
        # Get pending analysis tickers
        pending_tickers = target_ticker_repo.get_pending_analysis(target_date)
        pending_count = len(pending_tickers)
        
        analyzed_count = total_active - pending_count
        
        # Check daily_update status
        daily_job = job_status_repo.get_job_status("daily_update", target_date)
        daily_status = daily_job.status.value if daily_job else "not_found"
        
        status = {
            "target_date": target_date.isoformat(),
            "total_active_tickers": total_active,
            "analyzed_tickers": analyzed_count,
            "pending_tickers": pending_count,
            "completion_percentage": (analyzed_count / total_active * 100) if total_active > 0 else 0,
            "daily_update_status": daily_status,
            "is_analysis_complete": pending_count == 0,
            "can_run_analysis": daily_status == "completed"
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get analysis status: {e}")
        return {"error": str(e)}


def main():
    """Main entry point."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting hourly technical analysis...")
    logger.info(f"Current KST time: {get_kst_now()}")
    logger.info("=" * 60)
    
    try:
        success = run_hourly_analysis()
        
        if success:
            logger.info("Hourly analysis completed successfully")
            sys.exit(0)
        else:
            logger.error("Hourly analysis failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Hourly analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Hourly analysis failed with unexpected error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if db_manager._client:
            db_manager.disconnect()


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Hourly Technical Analysis Script")
            print("")
            print("This script performs technical analysis on stocks with state-based recovery.")
            print("It processes tickers that haven't been analyzed for the current date.")
            print("")
            print("Usage:")
            print("  python hourly_analysis.py [--status] [--max-time MINUTES]")
            print("")
            print("Options:")
            print("  --status          Show current analysis status")
            print("  --max-time MIN    Maximum runtime in minutes (default: from config)")
            print("  --help, -h        Show this help message")
            print("")
            print("Cron schedule:")
            print("  10 19-23 * * 1-5 (Mon-Fri 19:10-23:10)")
            print("  10 0-8 * * 1-5 (Mon-Fri 00:10-08:10)")
            sys.exit(0)
        
        elif sys.argv[1] == "--status":
            # Show analysis status
            logger = setup_logging()
            status = get_analysis_status()
            
            print("\n" + "="*50)
            print("HOURLY ANALYSIS STATUS")
            print("="*50)
            
            if "error" in status:
                print(f"Error: {status['error']}")
            else:
                print(f"Target Date: {status['target_date']}")
                print(f"Daily Update Status: {status['daily_update_status']}")
                print(f"Total Active Tickers: {status['total_active_tickers']}")
                print(f"Analyzed Tickers: {status['analyzed_tickers']}")
                print(f"Pending Tickers: {status['pending_tickers']}")
                print(f"Completion: {status['completion_percentage']:.1f}%")
                print(f"Analysis Complete: {status['is_analysis_complete']}")
                print(f"Can Run Analysis: {status['can_run_analysis']}")
            
            print("="*50)
            sys.exit(0)
        
        elif sys.argv[1] == "--max-time" and len(sys.argv) > 2:
            try:
                max_time = int(sys.argv[2])
                settings.analysis_time_limit_minutes = max_time
                print(f"Using maximum runtime: {max_time} minutes")
            except ValueError:
                print("Invalid time value. Using default from config.")
    
    # Normal execution
    main()