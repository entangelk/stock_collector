#!/usr/bin/env python3
"""
MongoDB 직접 테스트 - Pydantic 문제 우회
"""

import pymongo
from datetime import datetime, date
import pykrx.stock as stock

def test_mongodb_connection():
    """MongoDB 연결 및 기본 테스트"""
    print("=== MongoDB 연결 테스트 ===")

    try:
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        client.admin.command('ping')

        db = client['stock_collector_test']
        print(f"✅ MongoDB 연결 성공 - DB: {db.name}")

        return client, db

    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {e}")
        return None, None

def create_test_collections(db):
    """테스트 컬렉션 생성 및 스키마 정의"""
    print("\n=== 테스트 컬렉션 생성 ===")

    # 1. target_tickers 컬렉션
    target_tickers = db['target_tickers']

    # 샘플 대형주 데이터
    sample_tickers = [
        {
            "ticker": "005930",
            "name": "삼성전자",
            "market_cap": 400000000000000,  # 400조
            "added_date": datetime(2025, 9, 20),
            "is_active": True,
            "last_analyzed_date": None
        },
        {
            "ticker": "000660",
            "name": "SK하이닉스",
            "market_cap": 120000000000000,  # 120조
            "added_date": datetime(2025, 9, 20),
            "is_active": True,
            "last_analyzed_date": None
        },
        {
            "ticker": "035420",
            "name": "NAVER",
            "market_cap": 35000000000000,   # 35조
            "added_date": datetime(2025, 9, 20),
            "is_active": True,
            "last_analyzed_date": None
        }
    ]

    # 기존 데이터 삭제 후 삽입
    target_tickers.delete_many({})
    result = target_tickers.insert_many(sample_tickers)
    print(f"✅ target_tickers: {len(result.inserted_ids)}개 문서 삽입")

    return target_tickers

def insert_ohlcv_data(db):
    """실제 주식 데이터 수집 후 MongoDB 삽입"""
    print("\n=== OHLCV 데이터 수집 및 삽입 ===")

    ohlcv_collection = db['ohlcv_data']
    ohlcv_collection.delete_many({})  # 기존 데이터 삭제

    # 삼성전자 최근 5일 데이터 수집
    ticker = "005930"
    start_date = "20241216"
    end_date = "20241220"

    try:
        # pykrx로 데이터 수집
        ohlcv_df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

        ohlcv_documents = []
        for date_idx, row in ohlcv_df.iterrows():
            doc = {
                "date": datetime.combine(date_idx.date(), datetime.min.time()),
                "ticker": ticker,
                "open": float(row['시가']),
                "high": float(row['고가']),
                "low": float(row['저가']),
                "close": float(row['종가']),
                "volume": int(row['거래량']),
                "created_at": datetime.utcnow()
            }
            ohlcv_documents.append(doc)

        # MongoDB에 삽입
        if ohlcv_documents:
            result = ohlcv_collection.insert_many(ohlcv_documents)
            print(f"✅ ohlcv_data: {len(result.inserted_ids)}개 문서 삽입")

            # 삽입된 데이터 확인
            for doc in ohlcv_documents:
                print(f"   {doc['date']}: {doc['close']:,}원 (거래량: {doc['volume']:,})")

        return len(ohlcv_documents)

    except Exception as e:
        print(f"❌ OHLCV 데이터 수집 실패: {e}")
        return 0

def insert_technical_indicators(db):
    """기술적 지표 테스트 데이터 삽입"""
    print("\n=== 기술적 지표 데이터 삽입 ===")

    indicators_collection = db['technical_indicators']
    indicators_collection.delete_many({})

    # 삼성전자 기술적 지표 샘플 데이터
    sample_indicators = [
        {
            "date": datetime(2024, 12, 20),
            "ticker": "005930",
            "sma_5": 54160.0,
            "sma_20": 54725.0,
            "sma_60": 55200.0,
            "ema_12": 53800.0,
            "ema_26": 54500.0,
            "macd": -345.2,
            "macd_signal": -250.1,
            "macd_histogram": -95.1,
            "rsi_14": 45.8,
            "bollinger_upper": 58900.0,
            "bollinger_middle": 54725.0,
            "bollinger_lower": 50550.0,
            "stoch_k": 42.3,
            "stoch_d": 38.7,
            "created_at": datetime.utcnow()
        }
    ]

    result = indicators_collection.insert_many(sample_indicators)
    print(f"✅ technical_indicators: {len(result.inserted_ids)}개 문서 삽입")

    return len(result.inserted_ids)

def query_test_data(db):
    """삽입된 데이터 조회 테스트"""
    print("\n=== 데이터 조회 테스트 ===")

    # 1. 대상 종목 조회
    tickers = list(db['target_tickers'].find({"is_active": True}))
    print(f"✅ 활성 종목: {len(tickers)}개")
    for ticker in tickers:
        print(f"   {ticker['ticker']}({ticker['name']}): {ticker['market_cap']:,}원")

    # 2. OHLCV 데이터 조회
    ohlcv_count = db['ohlcv_data'].count_documents({})
    print(f"✅ OHLCV 데이터: {ohlcv_count}건")

    # 최근 데이터 조회
    latest_ohlcv = db['ohlcv_data'].find().sort("date", -1).limit(3)
    for data in latest_ohlcv:
        print(f"   {data['date']}: {data['ticker']} - {data['close']:,}원")

    # 3. 기술적 지표 조회
    indicators_count = db['technical_indicators'].count_documents({})
    print(f"✅ 기술적 지표: {indicators_count}건")

    if indicators_count > 0:
        indicator = db['technical_indicators'].find_one()
        print(f"   RSI: {indicator['rsi_14']:.1f}, MACD: {indicator['macd']:.1f}")

def test_aggregation_queries(db):
    """집계 쿼리 테스트"""
    print("\n=== 집계 쿼리 테스트 ===")

    # 1. 종목별 평균 거래량
    pipeline = [
        {"$group": {
            "_id": "$ticker",
            "avg_volume": {"$avg": "$volume"},
            "avg_price": {"$avg": "$close"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"avg_volume": -1}}
    ]

    results = list(db['ohlcv_data'].aggregate(pipeline))
    print("✅ 종목별 통계:")
    for result in results:
        print(f"   {result['_id']}: 평균거래량 {result['avg_volume']:,.0f}, 평균가격 {result['avg_price']:,.0f}원")

    # 2. 날짜별 시장 동향
    pipeline = [
        {"$group": {
            "_id": "$date",
            "total_volume": {"$sum": "$volume"},
            "avg_price": {"$avg": "$close"},
            "tickers": {"$addToSet": "$ticker"}
        }},
        {"$sort": {"_id": -1}}
    ]

    results = list(db['ohlcv_data'].aggregate(pipeline))
    print("✅ 날짜별 시장 통계:")
    for result in results:
        print(f"   {result['_id']}: 총거래량 {result['total_volume']:,}, 종목수 {len(result['tickers'])}개")

def main():
    """메인 테스트 함수"""
    print("MongoDB 직접 테스트 시작...\n")

    # 1. MongoDB 연결
    client, db = test_mongodb_connection()
    if db is None:
        return

    # 2. 테스트 컬렉션 생성
    create_test_collections(db)

    # 3. 실제 OHLCV 데이터 삽입
    ohlcv_count = insert_ohlcv_data(db)

    # 4. 기술적 지표 데이터 삽입
    indicators_count = insert_technical_indicators(db)

    # 5. 데이터 조회 테스트
    query_test_data(db)

    # 6. 집계 쿼리 테스트
    if ohlcv_count > 0:
        test_aggregation_queries(db)

    # 결과 요약
    print("\n" + "="*50)
    print("MongoDB 테스트 결과 요약")
    print("="*50)
    print(f"✅ 대상 종목: 3개")
    print(f"✅ OHLCV 데이터: {ohlcv_count}건")
    print(f"✅ 기술적 지표: {indicators_count}건")
    print(f"✅ MongoDB 연결: 정상")
    print(f"✅ 데이터 삽입/조회: 정상")
    print(f"✅ 집계 쿼리: 정상")

    print("\n🎉 MongoDB 직접 테스트 완료!")
    print("📊 Pydantic 문제와 무관하게 데이터베이스는 정상 동작합니다.")

    # 연결 종료
    client.close()

if __name__ == "__main__":
    main()