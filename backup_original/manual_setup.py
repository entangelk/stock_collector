"""
Manual setup script for initial data loading and target ticker initialization.

This script should be run once manually to:
1. Initialize the system_info.target_tickers collection 
2. Load historical data (last 300 days) for selected tickers
"""
import logging
import sys
from datetime import date, timedelta
from typing import List

from database import db_manager
from repositories import TargetTickerRepository, StockDataRepository
from collectors import StockDataCollector
from schemas import TargetTicker
from utils import get_kst_today, is_business_day, get_recent_business_days
from config import settings


def setup_logging():
    """Setup logging for the manual setup process."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("logs/manual_setup.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def initialize_database():
    """Initialize database connection."""
    logger = logging.getLogger(__name__)
    try:
        db_manager.connect()
        db_manager.create_indexes()
        logger.info("Database initialization completed")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def collect_and_store_target_tickers(min_market_cap: int = None) -> List[TargetTicker]:
    """Collect large cap tickers and store them in the database."""
    logger = logging.getLogger(__name__)
    
    if min_market_cap is None:
        min_market_cap = settings.min_market_cap
    
    logger.info(f"Collecting target tickers with minimum market cap: {min_market_cap:,} KRW")
    
    # Initialize components
    collector = StockDataCollector()
    target_ticker_repo = TargetTickerRepository()
    
    # Check if we already have target tickers
    existing_count = target_ticker_repo.count_documents()
    if existing_count > 0:
        logger.warning(f"Found {existing_count} existing target tickers")
        response = input("Do you want to replace them? (y/N): ").lower().strip()
        if response != 'y':
            logger.info("Using existing target tickers")
            return target_ticker_repo.get_all_active()
        else:
            logger.info("Clearing existing target tickers...")
            target_ticker_repo.delete_many({})
    
    # Collect large cap tickers
    try:
        large_cap_tickers = collector.collect_large_cap_tickers(min_market_cap)
        
        if not large_cap_tickers:
            logger.error("No large cap tickers found")
            return []
        
        # Store in database
        added_count = target_ticker_repo.add_multiple_tickers(large_cap_tickers)
        logger.info(f"Successfully added {added_count} target tickers to database")
        
        # Display summary
        logger.info("Target tickers summary:")
        for ticker in large_cap_tickers[:10]:  # Show first 10
            logger.info(f"  {ticker.ticker}: {ticker.name} (Market Cap: {ticker.market_cap:,})")
        
        if len(large_cap_tickers) > 10:
            logger.info(f"  ... and {len(large_cap_tickers) - 10} more tickers")
        
        return large_cap_tickers
        
    except Exception as e:
        logger.error(f"Failed to collect target tickers: {e}")
        return []


def load_historical_data(target_tickers: List[TargetTicker], days_back: int = 300):
    """Load historical data for target tickers."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Loading historical data ({days_back} days) for {len(target_tickers)} tickers")
    
    collector = StockDataCollector()
    success_count = 0
    error_count = 0
    
    for i, target_ticker in enumerate(target_tickers):
        ticker = target_ticker.ticker
        logger.info(f"Processing {ticker} ({target_ticker.name}) - {i+1}/{len(target_tickers)}")
        
        try:
            # Initialize stock data repository for this ticker
            stock_repo = StockDataRepository(ticker)
            
            # Check if we already have data
            existing_count = stock_repo.count_documents()
            if existing_count > 0:
                logger.info(f"  Found {existing_count} existing records for {ticker}")
                response = input(f"  Replace existing data for {ticker}? (y/N/a for all): ").lower().strip()
                if response == 'a':
                    # Replace all without asking again
                    logger.info("  Replacing data for all remaining tickers...")
                    stock_repo.delete_many({})
                elif response == 'y':
                    stock_repo.delete_many({})
                elif response == 'n' or response == '':
                    logger.info(f"  Skipping {ticker}")
                    continue
                else:
                    logger.info(f"  Skipping {ticker}")
                    continue
            
            # Collect historical data
            historical_data = collector.collect_historical_data(ticker, days_back)
            
            if not historical_data:
                logger.warning(f"  No historical data found for {ticker}")
                error_count += 1
                continue
            
            # Store data in database
            added_count = stock_repo.add_multiple_ohlcv_data(historical_data)
            logger.info(f"  Added {added_count} records for {ticker}")
            
            # Validate data integrity
            validation_result = collector.validate_data_integrity(ticker, historical_data)
            if not validation_result["valid"]:
                logger.warning(f"  Data integrity issues for {ticker}: {validation_result['issues']}")
            
            success_count += 1
            
        except Exception as e:
            logger.error(f"  Failed to load data for {ticker}: {e}")
            error_count += 1
            continue
    
    logger.info(f"Historical data loading completed: {success_count} success, {error_count} errors")


def verify_setup():
    """Verify that setup completed successfully."""
    logger = logging.getLogger(__name__)
    
    logger.info("Verifying setup...")
    
    # Check target tickers
    target_ticker_repo = TargetTickerRepository()
    ticker_count = target_ticker_repo.count_documents()
    active_count = target_ticker_repo.count_documents({"is_active": True})
    
    logger.info(f"Target tickers: {ticker_count} total, {active_count} active")
    
    if ticker_count == 0:
        logger.error("No target tickers found!")
        return False
    
    # Check stock data for a few tickers
    active_tickers = target_ticker_repo.get_all_active()
    data_summary = []
    
    for ticker_info in active_tickers[:5]:  # Check first 5 tickers
        stock_repo = StockDataRepository(ticker_info.ticker)
        data_count = stock_repo.count_documents()
        
        if data_count > 0:
            recent_data = stock_repo.get_recent_data(1)
            last_date = recent_data[0].date if recent_data else None
            data_summary.append(f"{ticker_info.ticker}: {data_count} records, last: {last_date}")
        else:
            data_summary.append(f"{ticker_info.ticker}: No data")
    
    logger.info("Stock data summary:")
    for summary in data_summary:
        logger.info(f"  {summary}")
    
    # Get overall statistics
    stats = target_ticker_repo.get_statistics()
    logger.info(f"Setup verification completed: {stats}")
    
    return True


def main():
    """Main setup process."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting manual setup process...")
    logger.info("=" * 60)
    
    try:
        # Step 1: Initialize database
        logger.info("Step 1: Initializing database...")
        if not initialize_database():
            logger.error("Database initialization failed. Exiting.")
            sys.exit(1)
        
        # Step 2: Collect target tickers
        logger.info("Step 2: Collecting target tickers...")
        target_tickers = collect_and_store_target_tickers()
        
        if not target_tickers:
            logger.error("No target tickers collected. Exiting.")
            sys.exit(1)
        
        # Step 3: Load historical data
        logger.info("Step 3: Loading historical data...")
        load_historical_data(target_tickers)
        
        # Step 4: Verify setup
        logger.info("Step 4: Verifying setup...")
        if verify_setup():
            logger.info("=" * 60)
            logger.info("Manual setup completed successfully!")
            logger.info("You can now run the daily_update.py script via cron.")
            logger.info("=" * 60)
        else:
            logger.error("Setup verification failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed with error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if db_manager._client:
            db_manager.disconnect()


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Manual Setup Script for Stock Collector")
            print("")
            print("This script initializes the database with target tickers")
            print("and loads historical data for analysis.")
            print("")
            print("Usage:")
            print("  python manual_setup.py [--min-cap AMOUNT]")
            print("")
            print("Options:")
            print("  --min-cap AMOUNT  Minimum market cap in KRW (default: from config)")
            print("  --help, -h        Show this help message")
            sys.exit(0)
        
        elif sys.argv[1] == "--min-cap" and len(sys.argv) > 2:
            try:
                min_cap = int(sys.argv[2])
                settings.min_market_cap = min_cap
                print(f"Using minimum market cap: {min_cap:,} KRW")
            except ValueError:
                print("Invalid market cap value. Using default from config.")
    
    main()