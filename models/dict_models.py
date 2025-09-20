"""
Pydantic 우회를 위한 딕셔너리 기반 모델 관리 시스템
MongoDB와 호환되는 스키마 정의 및 검증 함수 제공
"""

import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

# 환경변수 로딩
load_dotenv()

logger = logging.getLogger(__name__)


def get_mongodb_client():
    """MongoDB 클라이언트 가져오기"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    return MongoClient(mongodb_url)

# ===== 스키마 정의 =====

class SchemaError(Exception):
    """스키마 검증 오류"""
    pass

def target_ticker_schema() -> Dict[str, Any]:
    """대상 종목 스키마"""
    return {
        "ticker": str,
        "name": str,
        "market_cap": int,
        "added_date": datetime,
        "is_active": bool,
        "last_analyzed_date": Optional[datetime]
    }

def ohlcv_data_schema() -> Dict[str, Any]:
    """OHLCV 데이터 스키마"""
    return {
        "date": datetime,
        "ticker": str,
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "volume": int,
        "created_at": datetime
    }

def technical_indicators_schema() -> Dict[str, Any]:
    """기술적 지표 스키마"""
    return {
        "date": datetime,
        "ticker": str,
        "sma_5": Optional[float],
        "sma_20": Optional[float],
        "sma_60": Optional[float],
        "ema_12": Optional[float],
        "ema_26": Optional[float],
        "macd": Optional[float],
        "macd_signal": Optional[float],
        "macd_histogram": Optional[float],
        "rsi_14": Optional[float],
        "bollinger_upper": Optional[float],
        "bollinger_middle": Optional[float],
        "bollinger_lower": Optional[float],
        "stoch_k": Optional[float],
        "stoch_d": Optional[float],
        "created_at": datetime
    }

def job_status_schema() -> Dict[str, Any]:
    """작업 상태 스키마"""
    return {
        "_id": str,
        "job_name": str,
        "date_kst": datetime,
        "status": str,  # "running", "completed", "failed"
        "start_time_utc": datetime,
        "end_time_utc": Optional[datetime],
        "error_message": Optional[str],
        "records_processed": Optional[int]
    }

# ===== 모델 생성 함수 =====

def create_target_ticker(ticker: str, name: str, market_cap: int,
                        added_date: Optional[datetime] = None,
                        is_active: bool = True,
                        last_analyzed_date: Optional[datetime] = None) -> Dict[str, Any]:
    """대상 종목 모델 생성"""
    if added_date is None:
        added_date = datetime.utcnow()

    return {
        "ticker": ticker,
        "name": name,
        "market_cap": market_cap,
        "added_date": added_date,
        "is_active": is_active,
        "last_analyzed_date": last_analyzed_date
    }

def create_ohlcv_data(date: datetime, ticker: str, open_price: float, high: float,
                     low: float, close: float, volume: int,
                     created_at: Optional[datetime] = None) -> Dict[str, Any]:
    """OHLCV 데이터 모델 생성"""
    if created_at is None:
        created_at = datetime.utcnow()

    return {
        "date": date,
        "ticker": ticker,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "created_at": created_at
    }

def create_technical_indicators(date: datetime, ticker: str,
                              sma_5: Optional[float] = None,
                              sma_20: Optional[float] = None,
                              sma_60: Optional[float] = None,
                              ema_12: Optional[float] = None,
                              ema_26: Optional[float] = None,
                              macd: Optional[float] = None,
                              macd_signal: Optional[float] = None,
                              macd_histogram: Optional[float] = None,
                              rsi_14: Optional[float] = None,
                              bollinger_upper: Optional[float] = None,
                              bollinger_middle: Optional[float] = None,
                              bollinger_lower: Optional[float] = None,
                              stoch_k: Optional[float] = None,
                              stoch_d: Optional[float] = None,
                              created_at: Optional[datetime] = None) -> Dict[str, Any]:
    """기술적 지표 모델 생성"""
    if created_at is None:
        created_at = datetime.utcnow()

    return {
        "date": date,
        "ticker": ticker,
        "sma_5": sma_5,
        "sma_20": sma_20,
        "sma_60": sma_60,
        "ema_12": ema_12,
        "ema_26": ema_26,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_histogram": macd_histogram,
        "rsi_14": rsi_14,
        "bollinger_upper": bollinger_upper,
        "bollinger_middle": bollinger_middle,
        "bollinger_lower": bollinger_lower,
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "created_at": created_at
    }

def create_job_status(job_id: str, job_name: str, date_kst: datetime,
                     status: str = "running",
                     start_time_utc: Optional[datetime] = None,
                     end_time_utc: Optional[datetime] = None,
                     error_message: Optional[str] = None,
                     records_processed: Optional[int] = None) -> Dict[str, Any]:
    """작업 상태 모델 생성"""
    if start_time_utc is None:
        start_time_utc = datetime.utcnow()

    return {
        "_id": job_id,
        "job_name": job_name,
        "date_kst": date_kst,
        "status": status,
        "start_time_utc": start_time_utc,
        "end_time_utc": end_time_utc,
        "error_message": error_message,
        "records_processed": records_processed
    }

# ===== 검증 함수 =====

def validate_type(value: Any, expected_type: type, field_name: str) -> bool:
    """타입 검증"""
    if expected_type == Optional[datetime] or expected_type == Optional[float] or expected_type == Optional[int] or expected_type == Optional[str]:
        if value is None:
            return True
        # Optional 타입에서 실제 타입 추출
        actual_type = expected_type.__args__[0] if hasattr(expected_type, '__args__') else expected_type
        return isinstance(value, actual_type)

    if expected_type == datetime and isinstance(value, datetime):
        return True
    elif expected_type == str and isinstance(value, str):
        return True
    elif expected_type == int and isinstance(value, int):
        return True
    elif expected_type == float and (isinstance(value, float) or isinstance(value, int)):
        return True
    elif expected_type == bool and isinstance(value, bool):
        return True

    return False

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """스키마 검증"""
    try:
        for field_name, expected_type in schema.items():
            if field_name not in data:
                # Optional 필드는 누락 허용
                if str(expected_type).startswith('typing.Union') or str(expected_type).startswith('typing.Optional'):
                    continue
                raise SchemaError(f"Required field '{field_name}' is missing")

            value = data[field_name]
            if not validate_type(value, expected_type, field_name):
                raise SchemaError(f"Field '{field_name}' has invalid type. Expected {expected_type}, got {type(value)}")

        return True

    except SchemaError as e:
        logger.error(f"Schema validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return False

def validate_target_ticker(data: Dict[str, Any]) -> bool:
    """대상 종목 데이터 검증"""
    return validate_schema(data, target_ticker_schema())

def validate_ohlcv_data(data: Dict[str, Any]) -> bool:
    """OHLCV 데이터 검증"""
    schema_valid = validate_schema(data, ohlcv_data_schema())
    if not schema_valid:
        return False

    # 추가 비즈니스 로직 검증
    if data.get('open', 0) <= 0 or data.get('high', 0) <= 0 or data.get('low', 0) <= 0 or data.get('close', 0) <= 0:
        logger.error("Invalid price: all prices must be positive")
        return False

    if data.get('high', 0) < data.get('low', 0):
        logger.error("Invalid price: high price cannot be lower than low price")
        return False

    if data.get('volume', 0) < 0:
        logger.error("Invalid volume: volume cannot be negative")
        return False

    return True

def validate_technical_indicators(data: Dict[str, Any]) -> bool:
    """기술적 지표 데이터 검증"""
    schema_valid = validate_schema(data, technical_indicators_schema())
    if not schema_valid:
        return False

    # RSI 범위 검증 (0-100)
    rsi = data.get('rsi_14')
    if rsi is not None and (rsi < 0 or rsi > 100):
        logger.error(f"Invalid RSI value: {rsi}. Must be between 0 and 100")
        return False

    # Stochastic 범위 검증 (0-100)
    stoch_k = data.get('stoch_k')
    stoch_d = data.get('stoch_d')
    if stoch_k is not None and (stoch_k < 0 or stoch_k > 100):
        logger.error(f"Invalid Stochastic %K value: {stoch_k}. Must be between 0 and 100")
        return False
    if stoch_d is not None and (stoch_d < 0 or stoch_d > 100):
        logger.error(f"Invalid Stochastic %D value: {stoch_d}. Must be between 0 and 100")
        return False

    return True

def validate_job_status(data: Dict[str, Any]) -> bool:
    """작업 상태 데이터 검증"""
    schema_valid = validate_schema(data, job_status_schema())
    if not schema_valid:
        return False

    # 상태 값 검증
    valid_statuses = ["running", "completed", "failed"]
    if data.get('status') not in valid_statuses:
        logger.error(f"Invalid status: {data.get('status')}. Must be one of {valid_statuses}")
        return False

    return True

# ===== API 응답 모델 =====

def create_api_response(success: bool, data: Any = None, message: str = "",
                       error: str = "", total_count: Optional[int] = None) -> Dict[str, Any]:
    """표준 API 응답 생성"""
    response = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message
    }

    if success:
        response["data"] = data
        if total_count is not None:
            response["total_count"] = total_count
    else:
        response["error"] = error

    return response

def create_stock_list_response(tickers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """주식 목록 응답 생성"""
    active_count = sum(1 for ticker in tickers if ticker.get('is_active', False))

    return create_api_response(
        success=True,
        data={
            "tickers": tickers,
            "total_count": len(tickers),
            "active_count": active_count
        }
    )

def create_stock_detail_response(ticker_info: Dict[str, Any],
                                recent_data: List[Dict[str, Any]],
                                last_update: Optional[datetime] = None) -> Dict[str, Any]:
    """주식 상세 정보 응답 생성"""
    return create_api_response(
        success=True,
        data={
            "ticker_info": ticker_info,
            "recent_data": recent_data[:30],  # 최근 30개만
            "last_update": last_update.isoformat() if last_update else None
        }
    )

# ===== 유틸리티 함수 =====

def convert_date_fields(data: Dict[str, Any], date_fields: List[str]) -> Dict[str, Any]:
    """날짜 필드를 datetime 객체로 변환"""
    converted = data.copy()

    for field in date_fields:
        if field in converted and isinstance(converted[field], str):
            try:
                converted[field] = datetime.fromisoformat(converted[field])
            except ValueError:
                logger.warning(f"Failed to convert {field} to datetime: {converted[field]}")

    return converted

def sanitize_for_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    """MongoDB 저장을 위한 데이터 정리"""
    sanitized = {}

    for key, value in data.items():
        if value is not None:
            # date 객체를 datetime으로 변환
            if isinstance(value, date) and not isinstance(value, datetime):
                sanitized[key] = datetime.combine(value, datetime.min.time())
            else:
                sanitized[key] = value

    return sanitized

def prepare_for_api(data: Dict[str, Any]) -> Dict[str, Any]:
    """API 응답을 위한 데이터 준비"""
    prepared = {}

    for key, value in data.items():
        if key == '_id':
            # MongoDB _id 필드는 제외하거나 id로 변경
            prepared['id'] = str(value)
        elif isinstance(value, datetime):
            # datetime을 ISO 형식으로 변환
            prepared[key] = value.isoformat()
        else:
            prepared[key] = value

    return prepared

# ===== 사용 예시 =====

if __name__ == "__main__":
    # 사용 예시
    print("=== 딕셔너리 기반 모델 시스템 테스트 ===")

    # 1. 대상 종목 생성
    ticker_data = create_target_ticker(
        ticker="005930",
        name="삼성전자",
        market_cap=400000000000000
    )
    print("✅ Target ticker created:", validate_target_ticker(ticker_data))

    # 2. OHLCV 데이터 생성
    ohlcv_data = create_ohlcv_data(
        date=datetime(2024, 12, 20),
        ticker="005930",
        open_price=52700.0,
        high=53100.0,
        low=51900.0,
        close=53000.0,
        volume=24674774
    )
    print("✅ OHLCV data created:", validate_ohlcv_data(ohlcv_data))

    # 3. API 응답 생성
    api_response = create_api_response(
        success=True,
        data={"ticker": "005930", "price": 53000},
        message="Data retrieved successfully"
    )
    print("✅ API response created:", api_response['success'])

    print("\n🎉 딕셔너리 기반 모델 시스템 테스트 완료!")