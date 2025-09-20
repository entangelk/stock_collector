"""
딕셔너리 기반 모델 시스템
Pydantic 문제를 우회하여 MongoDB와 API에서 사용할 수 있는 모델들을 제공
"""

from .dict_models import (
    # 스키마 함수들
    target_ticker_schema,
    ohlcv_data_schema,
    technical_indicators_schema,
    job_status_schema,

    # 모델 생성 함수들
    create_target_ticker,
    create_ohlcv_data,
    create_technical_indicators,
    create_job_status,

    # 검증 함수들
    validate_target_ticker,
    validate_ohlcv_data,
    validate_technical_indicators,
    validate_job_status,

    # API 응답 함수들
    create_api_response,
    create_stock_list_response,
    create_stock_detail_response,

    # 유틸리티 함수들
    convert_date_fields,
    sanitize_for_mongo,
    prepare_for_api,

    # 예외
    SchemaError
)

__all__ = [
    # 스키마
    "target_ticker_schema",
    "ohlcv_data_schema",
    "technical_indicators_schema",
    "job_status_schema",

    # 모델 생성
    "create_target_ticker",
    "create_ohlcv_data",
    "create_technical_indicators",
    "create_job_status",

    # 검증
    "validate_target_ticker",
    "validate_ohlcv_data",
    "validate_technical_indicators",
    "validate_job_status",

    # API 응답
    "create_api_response",
    "create_stock_list_response",
    "create_stock_detail_response",

    # 유틸리티
    "convert_date_fields",
    "sanitize_for_mongo",
    "prepare_for_api",

    # 예외
    "SchemaError"
]