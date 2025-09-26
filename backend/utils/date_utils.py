"""
Date and business day utilities for Korean stock market.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
import pytz
import logging
from calendar import monthrange

from config import settings

logger = logging.getLogger(__name__)

# Cache for Korean market holidays by year
_HOLIDAY_CACHE = {}


def get_kst_now() -> datetime:
    """Get current time in KST timezone."""
    return datetime.now(settings.kst_timezone)


def get_kst_today() -> date:
    """Get today's date in KST timezone."""
    return get_kst_now().date()


def utc_to_kst(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to KST."""
    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)
    return utc_dt.astimezone(settings.kst_timezone)


def kst_to_utc(kst_dt: datetime) -> datetime:
    """Convert KST datetime to UTC."""
    if kst_dt.tzinfo is None:
        kst_dt = settings.kst_timezone.localize(kst_dt)
    return kst_dt.astimezone(pytz.UTC)


def get_market_holidays(year: int) -> List[date]:
    """Get Korean stock market holidays for the given year using pykrx."""
    global _HOLIDAY_CACHE
    
    if year in _HOLIDAY_CACHE:
        return _HOLIDAY_CACHE[year]
    
    try:
        import pykrx.stock.stock as krx_stock
        holidays_df = krx_stock.get_market_holidays(str(year))
        
        # Convert to list of date objects
        holidays = []
        for holiday_date in holidays_df:
            if hasattr(holiday_date, 'date'):
                holidays.append(holiday_date.date())
            else:
                # If it's already a date object or string, convert appropriately
                if isinstance(holiday_date, str):
                    holidays.append(datetime.strptime(holiday_date, '%Y-%m-%d').date())
                else:
                    holidays.append(holiday_date)
        
        _HOLIDAY_CACHE[year] = holidays
        logger.debug(f"Loaded {len(holidays)} holidays for {year}")
        return holidays
        
    except Exception as e:
        logger.warning(f"Failed to get market holidays for {year}, using fallback: {e}")
        
        # Fallback to basic Korean holidays if pykrx fails
        fallback_holidays = [
            date(year, 1, 1),   # 신정
            date(year, 3, 1),   # 삼일절  
            date(year, 5, 5),   # 어린이날
            date(year, 6, 6),   # 현충일
            date(year, 8, 15),  # 광복절
            date(year, 10, 3),  # 개천절
            date(year, 10, 9),  # 한글날
            date(year, 12, 25), # 크리스마스
        ]
        
        _HOLIDAY_CACHE[year] = fallback_holidays
        return fallback_holidays


def is_business_day(target_date: date) -> bool:
    """Check if given date is a business day (excludes weekends and holidays)."""
    # Check weekend (Saturday=5, Sunday=6)
    if target_date.weekday() >= 5:
        return False
    
    # Check Korean market holidays using pykrx
    year_holidays = get_market_holidays(target_date.year)
    if target_date in year_holidays:
        return False
    
    return True


def get_previous_business_day(target_date: date) -> date:
    """Get the previous business day."""
    prev_date = target_date - timedelta(days=1)
    
    while not is_business_day(prev_date):
        prev_date -= timedelta(days=1)
    
    return prev_date


def get_next_business_day(target_date: date) -> date:
    """Get the next business day."""
    next_date = target_date + timedelta(days=1)
    
    while not is_business_day(next_date):
        next_date += timedelta(days=1)
    
    return next_date


def get_business_days_between(start_date: date, end_date: date, 
                             include_start: bool = True, 
                             include_end: bool = True) -> List[date]:
    """Get list of business days between two dates."""
    if start_date > end_date:
        return []
    
    business_days = []
    current_date = start_date
    
    # Handle start date
    if not include_start:
        current_date = current_date + timedelta(days=1)
    
    # Handle end date
    actual_end_date = end_date
    if not include_end:
        actual_end_date = actual_end_date - timedelta(days=1)
    
    while current_date <= actual_end_date:
        if is_business_day(current_date):
            business_days.append(current_date)
        current_date += timedelta(days=1)
    
    return business_days


def get_recent_business_days(count: int, end_date: Optional[date] = None) -> List[date]:
    """Get list of recent business days."""
    if end_date is None:
        end_date = get_kst_today()
    
    business_days = []
    current_date = end_date
    
    while len(business_days) < count and current_date >= date(2020, 1, 1):
        if is_business_day(current_date):
            business_days.append(current_date)
        current_date -= timedelta(days=1)
    
    return sorted(business_days)


def get_last_n_months_business_days(months: int, 
                                   end_date: Optional[date] = None) -> List[date]:
    """Get business days for the last N months."""
    if end_date is None:
        end_date = get_kst_today()
    
    # Calculate start date (approximately)
    start_year = end_date.year
    start_month = end_date.month - months
    
    if start_month <= 0:
        start_year -= 1
        start_month += 12
    
    start_date = date(start_year, start_month, 1)
    
    return get_business_days_between(start_date, end_date)


def is_market_open_time() -> bool:
    """Check if Korean stock market is currently open."""
    now_kst = get_kst_now()
    
    # Market is closed on weekends and holidays
    if not is_business_day(now_kst.date()):
        return False
    
    # Market hours: 9:00 - 15:30 KST
    market_open = now_kst.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now_kst.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now_kst <= market_close


def get_market_status() -> dict:
    """Get current market status information."""
    now_kst = get_kst_now()
    today = now_kst.date()
    
    is_business = is_business_day(today)
    is_open = is_market_open_time()
    
    status = {
        "current_kst_time": now_kst.strftime("%Y-%m-%d %H:%M:%S KST"),
        "is_business_day": is_business,
        "is_market_open": is_open,
        "market_status": "open" if is_open else ("closed" if is_business else "holiday"),
        "today": today.isoformat()
    }
    
    if is_business:
        market_open = now_kst.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now_kst.replace(hour=15, minute=30, second=0, microsecond=0)
        
        status.update({
            "market_open_time": market_open.strftime("%H:%M:%S KST"),
            "market_close_time": market_close.strftime("%H:%M:%S KST")
        })
        
        if now_kst < market_open:
            status["market_opens_in"] = str(market_open - now_kst)
        elif now_kst > market_close:
            next_business_day = get_next_business_day(today)
            next_open = settings.kst_timezone.localize(
                datetime.combine(next_business_day, market_open.time())
            )
            status["next_market_open"] = next_open.strftime("%Y-%m-%d %H:%M:%S KST")
    else:
        next_business_day = get_next_business_day(today)
        next_open = settings.kst_timezone.localize(
            datetime.combine(next_business_day, datetime.min.time().replace(hour=9))
        )
        status["next_market_open"] = next_open.strftime("%Y-%m-%d %H:%M:%S KST")
    
    return status


def validate_date_range(start_date: date, end_date: date, 
                       max_days: int = 365) -> tuple[bool, str]:
    """Validate date range for data collection."""
    if start_date > end_date:
        return False, "Start date must be before end date"
    
    if end_date > get_kst_today():
        return False, "End date cannot be in the future"
    
    days_diff = (end_date - start_date).days
    if days_diff > max_days:
        return False, f"Date range too large. Maximum {max_days} days allowed"
    
    # Check if start_date is too old (before 2000)
    if start_date < date(2000, 1, 1):
        return False, "Start date cannot be before 2000-01-01"
    
    return True, "Valid date range"


def format_date_for_display(target_date: date) -> str:
    """Format date for user display."""
    return target_date.strftime("%Y년 %m월 %d일")


def parse_date_string(date_str: str) -> Optional[date]:
    """Parse date string in various formats."""
    formats = [
        "%Y-%m-%d",
        "%Y%m%d", 
        "%Y.%m.%d",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


def get_month_business_days(year: int, month: int) -> List[date]:
    """Get all business days in a specific month."""
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    return get_business_days_between(start_date, end_date)


def calculate_business_days_ago(days_ago: int, 
                               reference_date: Optional[date] = None) -> date:
    """Calculate date that is N business days ago from reference date."""
    if reference_date is None:
        reference_date = get_kst_today()
    
    current_date = reference_date
    business_days_counted = 0
    
    while business_days_counted < days_ago:
        current_date -= timedelta(days=1)
        if is_business_day(current_date):
            business_days_counted += 1
    
    return current_date


def get_quarter_business_days(year: int, quarter: int) -> List[date]:
    """Get all business days in a specific quarter."""
    quarter_months = {
        1: [1, 2, 3],
        2: [4, 5, 6], 
        3: [7, 8, 9],
        4: [10, 11, 12]
    }
    
    if quarter not in quarter_months:
        raise ValueError("Quarter must be 1, 2, 3, or 4")
    
    months = quarter_months[quarter]
    start_date = date(year, months[0], 1)
    
    # Get last day of last month in quarter
    _, last_day = monthrange(year, months[2])
    end_date = date(year, months[2], last_day)
    
    return get_business_days_between(start_date, end_date)