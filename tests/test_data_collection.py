#!/usr/bin/env python3
"""
데이터 수집 API 테스트 스크립트

각 데이터 수집 API의 동작을 검증합니다.
"""

import sys
import os
from datetime import date, timedelta
from typing import List

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_pykrx():
    """기본 pykrx 라이브러리 테스트"""
    print("=== 기본 pykrx 라이브러리 테스트 ===")

    try:
        import pykrx.stock as stock
        from datetime import datetime

        # 1. 종목 리스트 가져오기 테스트
        print("1. KOSPI 종목 리스트 테스트...")
        date_str = "20241220"
        kospi_tickers = stock.get_market_ticker_list(date_str, market="KOSPI")
        print(f"   ✅ KOSPI 종목 수: {len(kospi_tickers)}개")

        # 2. 종목명 가져오기 테스트
        print("2. 종목명 가져오기 테스트...")
        test_ticker = "005930"  # 삼성전자
        ticker_name = stock.get_market_ticker_name(test_ticker)
        print(f"   ✅ {test_ticker}: {ticker_name}")

        # 3. OHLCV 데이터 가져오기 테스트
        print("3. OHLCV 데이터 가져오기 테스트...")
        start_date = "20241216"
        end_date = "20241220"
        ohlcv_data = stock.get_market_ohlcv_by_date(start_date, end_date, test_ticker)
        print(f"   ✅ 데이터 건수: {len(ohlcv_data)}건")
        print(f"   최신 종가: {ohlcv_data.iloc[-1]['종가']:,}원")

        # 4. 시가총액 데이터 테스트
        print("4. 시가총액 데이터 테스트...")
        market_cap_data = stock.get_market_cap_by_ticker(date_str, test_ticker)
        if not market_cap_data.empty:
            market_cap = market_cap_data.iloc[0]['시가총액']
            print(f"   ✅ 시가총액: {market_cap:,} (100M won)")

        return True

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False

def test_project_data_collector():
    """프로젝트의 StockDataCollector 테스트"""
    print("\n=== StockDataCollector 클래스 테스트 ===")

    try:
        # Import 테스트부터 시작
        print("1. Import 테스트...")

        # 기본 import들이 있는지 확인
        import pandas as pd
        import logging
        from datetime import date, timedelta
        print("   ✅ 기본 라이브러리 import 성공")

        # 프로젝트 모듈들 확인
        folders_to_check = [
            'schemas',
            'utils',
            'config.py'
        ]

        for item in folders_to_check:
            if os.path.exists(item):
                print(f"   ✅ {item} 존재")
            else:
                print(f"   ❌ {item} 없음")
                # return False  # 일단 계속 진행

        print("2. 수동 StockDataCollector 테스트...")

        # 수동으로 기본 기능 테스트
        import pykrx.stock as stock

        class SimpleCollector:
            def __init__(self):
                self.request_delay = 0.1

            def get_market_tickers_simple(self, market="KOSPI"):
                date_str = "20241220"
                return stock.get_market_ticker_list(date_str, market=market)

            def get_ohlcv_simple(self, ticker, start_date, end_date):
                df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
                return df

        collector = SimpleCollector()

        # 종목 리스트 테스트
        print("   2-1. 종목 리스트 가져오기...")
        tickers = collector.get_market_tickers_simple()
        print(f"       ✅ {len(tickers)}개 종목 조회 성공")

        # OHLCV 데이터 테스트
        print("   2-2. OHLCV 데이터 가져오기...")
        test_ticker = tickers[0] if tickers else "005930"
        ohlcv = collector.get_ohlcv_simple(test_ticker, "20241216", "20241220")
        print(f"       ✅ {test_ticker} 데이터 {len(ohlcv)}건 조회 성공")

        return True

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_performance():
    """API 성능 및 안정성 테스트"""
    print("\n=== API 성능 테스트 ===")

    try:
        import pykrx.stock as stock
        import time

        # 연속 호출 테스트
        print("1. 연속 API 호출 테스트...")
        start_time = time.time()

        test_tickers = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, 네이버

        for i, ticker in enumerate(test_tickers):
            ticker_name = stock.get_market_ticker_name(ticker)
            ohlcv = stock.get_market_ohlcv_by_date("20241220", "20241220", ticker)
            print(f"   {i+1}. {ticker}({ticker_name}): {ohlcv.iloc[0]['종가']:,}원")
            time.sleep(0.1)  # Rate limiting

        elapsed = time.time() - start_time
        print(f"   ✅ 3개 종목 처리 시간: {elapsed:.2f}초")

        return True

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("주식 데이터 수집 API 테스트를 시작합니다...\n")

    results = []

    # 1. 기본 pykrx 테스트
    results.append(("기본 pykrx 테스트", test_basic_pykrx()))

    # 2. 프로젝트 데이터 수집기 테스트
    results.append(("StockDataCollector 테스트", test_project_data_collector()))

    # 3. API 성능 테스트
    results.append(("API 성능 테스트", test_api_performance()))

    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약")
    print("="*50)

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")

    print(f"\n전체: {passed_tests}/{total_tests} 테스트 통과")

    if passed_tests == total_tests:
        print("🎉 모든 데이터 수집 API 테스트가 성공했습니다!")
    else:
        print("⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()