"""
Daily stock data update script with self-healing capability.

This script runs via cron every business day at 19:00 KST.
It automatically detects missing data and backfills from the last successful date.

Cron schedule: 0 19 * * 1-5 (Mon-Fri 19:00 KST)
"""
import logging
import sys
from datetime import date, timedelta
from typing import List, Optional

from database import db_manager
from repositories import TargetTickerRepository, JobStatusRepository, StockDataRepository
from collectors import StockDataCollector
from utils import (
    get_kst_today, is_business_day, get_business_days_between,
    get_previous_business_day
)
from config import settings


def setup_logging():
    """Setup logging for daily update process."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("logs/daily_update.log"),
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
        
        # Initialize repositories
        target_ticker_repo = TargetTickerRepository()
        job_status_repo = JobStatusRepository()
        collector = StockDataCollector()
        
        logger.info("Components initialized successfully")
        return target_ticker_repo, job_status_repo, collector
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


def determine_update_dates(job_status_repo: JobStatusRepository) -> List[date]:
    """Determine which dates need to be updated (self-healing logic)."""
    logger = logging.getLogger(__name__)
    
    # Get the last successful daily_update job
    last_successful_date = job_status_repo.get_last_successful_date("daily_update")
    today = get_kst_today()
    
    if last_successful_date is None:
        # No previous successful run, start from yesterday
        logger.info("No previous successful daily_update found")
        start_date = get_previous_business_day(today)
    else:
        # Start from the day after last successful date
        start_date = last_successful_date + timedelta(days=1)
        logger.info(f"Last successful daily_update: {last_successful_date}")
    
    # Get all business days from start_date to today (exclusive)
    # We update up to yesterday, not today (market might still be open)
    end_date = get_previous_business_day(today)
    
    if start_date > end_date:
        logger.info("No dates need updating")
        return []
    
    update_dates = get_business_days_between(start_date, end_date, include_end=True)
    
    logger.info(f"Dates to update: {len(update_dates)} business days from {start_date} to {end_date}")
    for update_date in update_dates:
        logger.info(f"  - {update_date}")
    
    return update_dates


def update_data_for_date(target_date: date, 
                        target_ticker_repo: TargetTickerRepository,
                        collector: StockDataCollector) -> dict:
    """Update stock data for a specific date."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Updating data for {target_date}")
    
    # Get all active tickers
    active_tickers = target_ticker_repo.get_all_active()
    
    if not active_tickers:
        logger.warning("No active target tickers found")
        return {"success": 0, "errors": 0, "total": 0}
    
    success_count = 0
    error_count = 0
    total_count = len(active_tickers)
    
    for i, target_ticker in enumerate(active_tickers):
        ticker = target_ticker.ticker
        
        try:
            logger.debug(f"  Processing {ticker} ({target_ticker.name}) - {i+1}/{total_count}")
            
            # Get OHLCV data for this date
            ohlcv_data = collector.get_single_day_ohlcv(ticker, target_date)
            
            if ohlcv_data is None:
                logger.warning(f"    No data found for {ticker} on {target_date}")
                error_count += 1
                continue
            
            # Store in database
            stock_repo = StockDataRepository(ticker)
            if stock_repo.add_ohlcv_data(ohlcv_data):
                success_count += 1
                logger.debug(f"    Successfully updated {ticker}")
            else:
                logger.warning(f"    Failed to store data for {ticker}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"    Error processing {ticker}: {e}")
            error_count += 1
            continue
    
    result = {
        "success": success_count,
        "errors": error_count,
        "total": total_count,
        "date": target_date
    }
    
    logger.info(f"  Date {target_date} update completed: {success_count}/{total_count} success, {error_count} errors")
    return result


def run_daily_update():
    """Main daily update process with self-healing."""
    logger = logging.getLogger(__name__)
    
    today = get_kst_today()
    job_id = None
    
    try:
        # Initialize components
        target_ticker_repo, job_status_repo, collector = initialize_components()
        
        # Start job tracking
        job_id = job_status_repo.start_job("daily_update", today)
        logger.info(f"Started daily_update job: {job_id}")
        
        # Determine which dates need updating
        update_dates = determine_update_dates(job_status_repo)
        
        if not update_dates:
            logger.info("No dates need updating")
            job_status_repo.complete_job(job_id, records_processed=0)
            return True
        
        # Process each date
        total_records = 0
        total_errors = 0
        
        for update_date in update_dates:
            # Check if this specific date is a business day
            if not is_business_day(update_date):
                logger.info(f"Skipping {update_date} (not a business day)")
                continue
            
            result = update_data_for_date(update_date, target_ticker_repo, collector)
            total_records += result["success"]
            total_errors += result["errors"]
            
            # If we have too many errors for this date, log but continue
            if result["errors"] > result["total"] * 0.5:
                logger.warning(f"High error rate for {update_date}: {result['errors']}/{result['total']}")
        
        # Complete job tracking
        job_status_repo.complete_job(job_id, records_processed=total_records)
        
        logger.info("=" * 60)
        logger.info(f"Daily update completed successfully!")
        logger.info(f"Updated {len(update_dates)} dates")
        logger.info(f"Total records processed: {total_records}")
        logger.info(f"Total errors: {total_errors}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Daily update failed: {e}")
        
        # Mark job as failed
        if job_id:
            job_status_repo.fail_job(job_id, str(e))
        
        return False


def check_prerequisites():
    """Check if prerequisites are met for running daily update."""
    logger = logging.getLogger(__name__)
    
    try:
        # Check database connectivity
        if not db_manager.is_connected():
            db_manager.connect()
        
        # Check if we have target tickers
        target_ticker_repo = TargetTickerRepository()
        active_count = target_ticker_repo.count_documents({"is_active": True})
        
        if active_count == 0:
            logger.error("No active target tickers found. Run manual_setup.py first.")
            return False
        
        logger.info(f"Prerequisites check passed: {active_count} active tickers")
        return True
        
    except Exception as e:
        logger.error(f"Prerequisites check failed: {e}")
        return False


def main():
    """Main entry point."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting daily stock data update...")
    logger.info(f"Current KST time: {get_kst_today()}")
    logger.info("=" * 60)
    
    try:
        # Check prerequisites
        if not check_prerequisites():
            logger.error("Prerequisites not met. Exiting.")
            sys.exit(1)
        
        # Run daily update
        success = run_daily_update()
        
        if success:
            logger.info("Daily update process completed successfully")
            sys.exit(0)
        else:
            logger.error("Daily update process failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Daily update interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Daily update failed with unexpected error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if db_manager._client:
            db_manager.disconnect()


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Daily Stock Data Update Script")
            print("")
            print("This script updates stock data with self-healing capability.")
            print("It automatically detects and backfills missing data.")
            print("")
            print("Usage:")
            print("  python daily_update.py [--dry-run]")
            print("")
            print("Options:")
            print("  --dry-run         Show what would be updated without making changes")
            print("  --help, -h        Show this help message")
            print("")
            print("Cron schedule: 0 19 * * 1-5 (Mon-Fri 19:00 KST)")
            sys.exit(0)
        
        elif sys.argv[1] == "--dry-run":
            # Dry run mode - show what would be updated
            logger = setup_logging()
            logger.info("DRY RUN MODE - No data will be updated")
            
            try:
                db_manager.connect()
                job_status_repo = JobStatusRepository()
                update_dates = determine_update_dates(job_status_repo)
                
                if not update_dates:
                    logger.info("No dates would be updated")
                else:
                    logger.info(f"Would update {len(update_dates)} dates:")
                    for update_date in update_dates:
                        logger.info(f"  - {update_date}")
                        
            except Exception as e:
                logger.error(f"Dry run failed: {e}")
            finally:
                if db_manager._client:
                    db_manager.disconnect()
                    
            sys.exit(0)
    
    # Normal execution
    main()