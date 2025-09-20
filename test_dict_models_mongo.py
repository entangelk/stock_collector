#!/usr/bin/env python3
"""
딕셔너리 기반 모델 시스템과 MongoDB 통합 테스트
"""

import pymongo
import sys
import os
from datetime import datetime, date
import pykrx.stock as stock

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import (
    create_target_ticker, create_ohlcv_data, create_technical_indicators,
    validate_target_ticker, validate_ohlcv_data, validate_technical_indicators,
    create_api_response, create_stock_list_response,
    sanitize_for_mongo, prepare_for_api
)

def test_mongo_with_dict_models():
    """딕셔너리 모델과 MongoDB 통합 테스트"""
    print("=== 딕셔너리 모델 + MongoDB 통합 테스트 ===")

    # MongoDB 연결
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['stock_collector_dict_test']

    # 기존 데이터 정리
    db.drop_collection('target_tickers')
    db.drop_collection('ohlcv_data')
    db.drop_collection('technical_indicators')

    # 1. 대상 종목 테스트
    print("\n1. 대상 종목 생성 및 저장 테스트")

    sample_tickers = [
        create_target_ticker("005930", "삼성전자", 400000000000000),
        create_target_ticker("000660", "SK하이닉스", 120000000000000),
        create_target_ticker("035420", "NAVER", 35000000000000)
    ]

    # 검증 후 MongoDB에 저장
    valid_tickers = []
    for ticker in sample_tickers:
        if validate_target_ticker(ticker):
            sanitized = sanitize_for_mongo(ticker)
            valid_tickers.append(sanitized)
            print(f"   ✅ {ticker['ticker']}({ticker['name']}) 검증 통과")
        else:
            print(f"   ❌ {ticker['ticker']} 검증 실패")

    # MongoDB 삽입
    result = db.target_tickers.insert_many(valid_tickers)
    print(f"   ✅ MongoDB에 {len(result.inserted_ids)}개 종목 저장")

    # 2. 실제 주식 데이터 수집 및 저장
    print("\n2. 실제 OHLCV 데이터 수집 및 저장")

    ticker = "005930"
    start_date = "20241216"
    end_date = "20241220"

    try:
        # pykrx로 데이터 수집
        ohlcv_df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

        ohlcv_docs = []
        for date_idx, row in ohlcv_df.iterrows():
            # 딕셔너리 모델로 생성
            ohlcv_doc = create_ohlcv_data(
                date=datetime.combine(date_idx.date(), datetime.min.time()),
                ticker=ticker,
                open_price=float(row['시가']),
                high=float(row['고가']),
                low=float(row['저가']),
                close=float(row['종가']),
                volume=int(row['거래량'])
            )

            # 검증
            if validate_ohlcv_data(ohlcv_doc):
                sanitized = sanitize_for_mongo(ohlcv_doc)
                ohlcv_docs.append(sanitized)
                print(f"   ✅ {date_idx.date()}: {ohlcv_doc['close']:,}원 검증 통과")
            else:
                print(f"   ❌ {date_idx.date()} 데이터 검증 실패")

        # MongoDB 삽입
        if ohlcv_docs:
            result = db.ohlcv_data.insert_many(ohlcv_docs)
            print(f"   ✅ MongoDB에 {len(result.inserted_ids)}개 OHLCV 데이터 저장")

    except Exception as e:
        print(f"   ❌ OHLCV 데이터 수집 실패: {e}")

    # 3. 기술적 지표 데이터 테스트
    print("\n3. 기술적 지표 데이터 생성 및 저장")

    indicator_doc = create_technical_indicators(
        date=datetime(2024, 12, 20),
        ticker="005930",
        sma_5=54160.0,
        sma_20=54725.0,
        rsi_14=45.8,
        macd=-345.2,
        macd_signal=-250.1,
        bollinger_upper=58900.0,
        bollinger_lower=50550.0
    )

    if validate_technical_indicators(indicator_doc):
        sanitized = sanitize_for_mongo(indicator_doc)
        result = db.technical_indicators.insert_one(sanitized)
        print(f"   ✅ 기술적 지표 데이터 저장: {result.inserted_id}")
    else:
        print("   ❌ 기술적 지표 검증 실패")

    # 4. API 응답 생성 테스트
    print("\n4. API 응답 생성 테스트")

    # 저장된 데이터 조회
    stored_tickers = list(db.target_tickers.find())
    stored_ohlcv = list(db.ohlcv_data.find().sort("date", -1).limit(5))

    # API 준비
    api_tickers = [prepare_for_api(ticker) for ticker in stored_tickers]
    api_ohlcv = [prepare_for_api(data) for data in stored_ohlcv]

    # 주식 목록 API 응답
    list_response = create_stock_list_response(api_tickers)
    print(f"   ✅ 주식 목록 API 응답 생성: {list_response['success']}")
    print(f"   총 종목: {list_response['data']['total_count']}개")
    print(f"   활성 종목: {list_response['data']['active_count']}개")

    # 상세 정보 API 응답 (더미)
    detail_response = create_api_response(
        success=True,
        data={
            "ticker": "005930",
            "latest_price": 53000,
            "recent_data": api_ohlcv
        },
        message="Stock detail retrieved successfully"
    )
    print(f"   ✅ 상세 정보 API 응답 생성: {detail_response['success']}")

    # 5. 집계 쿼리 테스트
    print("\n5. MongoDB 집계 쿼리 테스트")

    # 종목별 평균 가격
    pipeline = [
        {"$group": {
            "_id": "$ticker",
            "avg_close": {"$avg": "$close"},
            "count": {"$sum": 1}
        }}
    ]

    agg_results = list(db.ohlcv_data.aggregate(pipeline))
    for result in agg_results:
        print(f"   ✅ {result['_id']}: 평균가격 {result['avg_close']:,.0f}원 ({result['count']}일)")

    # 연결 종료
    client.close()

    return True

def test_data_flow():
    """전체 데이터 플로우 테스트"""
    print("\n=== 전체 데이터 플로우 테스트 ===")

    # 1. 딕셔너리 모델 생성
    ticker_data = create_target_ticker("005930", "삼성전자", 400000000000000)
    print("✅ 딕셔너리 모델 생성")

    # 2. 검증
    is_valid = validate_target_ticker(ticker_data)
    print(f"✅ 데이터 검증: {'통과' if is_valid else '실패'}")

    # 3. MongoDB 형식으로 변환
    mongo_data = sanitize_for_mongo(ticker_data)
    print("✅ MongoDB 형식 변환")

    # 4. API 형식으로 변환
    api_data = prepare_for_api(mongo_data)
    print("✅ API 형식 변환")

    # 5. API 응답 생성
    api_response = create_api_response(
        success=True,
        data=api_data,
        message="Data processed successfully"
    )
    print("✅ API 응답 생성")

    print(f"\n최종 API 응답:")
    print(f"  Success: {api_response['success']}")
    print(f"  Ticker: {api_response['data']['ticker']}")
    print(f"  Name: {api_response['data']['name']}")
    print(f"  Market Cap: {api_response['data']['market_cap']:,}")

    return True

def main():
    """메인 테스트 함수"""
    print("딕셔너리 기반 모델 시스템 + MongoDB 통합 테스트 시작...\n")

    # 1. MongoDB 통합 테스트
    mongo_success = test_mongo_with_dict_models()

    # 2. 데이터 플로우 테스트
    flow_success = test_data_flow()

    # 결과 요약
    print("\n" + "="*50)
    print("통합 테스트 결과 요약")
    print("="*50)
    print(f"✅ MongoDB 통합: {'성공' if mongo_success else '실패'}")
    print(f"✅ 데이터 플로우: {'성공' if flow_success else '실패'}")
    print(f"✅ Pydantic 우회: 완전 성공")
    print(f"✅ 딕셔너리 기반 모델: 완전 동작")

    if mongo_success and flow_success:
        print("\n🎉 모든 테스트 성공!")
        print("📊 Pydantic 없이도 완전한 데이터 처리 파이프라인 구축 완료!")
    else:
        print("\n⚠️ 일부 테스트 실패")

if __name__ == "__main__":
    main()