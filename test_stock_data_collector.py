#!/usr/bin/env python3
"""
StockDataCollector 클래스 실제 테스트 스크립트
"""

import sys
import os
from datetime import date, timedelta
import logging

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(level=logging.INFO)

def test_stock_data_collector_imports():
    """StockDataCollector 클래스 import 테스트"""
    print("=== StockDataCollector Import 테스트 ===")

    try:
        # 필요한 모듈들 import
        from schemas import OHLCVData, TargetTicker
        from utils import get_kst_today, is_business_day, get_business_days_between
        from config import settings
        from collectors.stock_data_collector import StockDataCollector

        print("✅ 모든 모듈 import 성공")
        return True

    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("   dependencies 설치가 필요할 수 있습니다.")
        return False
    except Exception as e:
        print(f"❌ 기타 오류: {e}")
        return False

def test_collector_basic_methods():
    """기본적인 데이터 수집 메서드 테스트"""
    print("\n=== StockDataCollector 기본 메서드 테스트 ===")

    try:
        from collectors.stock_data_collector import StockDataCollector

        collector = StockDataCollector()
        print("✅ StockDataCollector 인스턴스 생성 성공")

        # 1. 종목 리스트 가져오기
        print("1. 종목 리스트 테스트...")
        kospi_tickers = collector.get_market_tickers("KOSPI")
        print(f"   ✅ KOSPI 종목 수: {len(kospi_tickers)}개")

        kosdaq_tickers = collector.get_market_tickers("KOSDAQ")
        print(f"   ✅ KOSDAQ 종목 수: {len(kosdaq_tickers)}개")

        all_tickers = collector.get_market_tickers("ALL")
        print(f"   ✅ 전체 종목 수: {len(all_tickers)}개")

        # 2. 종목 정보 가져오기
        print("2. 종목 정보 테스트...")
        test_ticker = "005930"  # 삼성전자
        ticker_info = collector.get_ticker_info(test_ticker)

        if ticker_info:
            print(f"   ✅ {test_ticker} 정보:")
            print(f"      종목명: {ticker_info['name']}")
            print(f"      시가총액: {ticker_info['market_cap']:,}원")
            print(f"      조회일: {ticker_info['date']}")
        else:
            print(f"   ❌ {test_ticker} 정보 조회 실패")
            return False

        # 3. OHLCV 데이터 가져오기
        print("3. OHLCV 데이터 테스트...")
        end_date = date(2024, 12, 20)
        start_date = end_date - timedelta(days=7)

        ohlcv_data = collector.get_ohlcv_data(test_ticker, start_date, end_date)

        if ohlcv_data:
            print(f"   ✅ {test_ticker} OHLCV 데이터 {len(ohlcv_data)}건 수집")
            latest_data = ohlcv_data[-1]
            print(f"      최신 데이터 ({latest_data.date}):")
            print(f"      종가: {latest_data.close:,}원")
            print(f"      거래량: {latest_data.volume:,}주")
        else:
            print(f"   ❌ {test_ticker} OHLCV 데이터 조회 실패")
            return False

        return True

    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_collector_advanced_methods():
    """고급 데이터 수집 메서드 테스트"""
    print("\n=== StockDataCollector 고급 메서드 테스트 ===")

    try:
        from collectors.stock_data_collector import StockDataCollector

        collector = StockDataCollector()

        # 1. 단일 날짜 OHLCV 테스트
        print("1. 단일 날짜 OHLCV 테스트...")
        test_ticker = "005930"
        target_date = date(2024, 12, 20)

        single_data = collector.get_single_day_ohlcv(test_ticker, target_date)
        if single_data:
            print(f"   ✅ {test_ticker} {target_date} 데이터:")
            print(f"      종가: {single_data.close:,}원")
        else:
            print(f"   ⚠️ {test_ticker} {target_date} 데이터 없음 (휴장일 가능)")

        # 2. 히스토리컬 데이터 수집 테스트
        print("2. 히스토리컬 데이터 수집 테스트...")
        historical_data = collector.collect_historical_data(test_ticker, days_back=30)

        if historical_data:
            print(f"   ✅ {test_ticker} 최근 30일 데이터 {len(historical_data)}건 수집")

            # 데이터 검증
            validation = collector.validate_data_integrity(test_ticker, historical_data)
            print(f"   검증 결과: {'✅ 유효' if validation['valid'] else '⚠️ 문제 있음'}")
            print(f"   총 레코드: {validation['total_records']}건")
            print(f"   기간: {validation['date_range']}")
            if validation['issues']:
                print(f"   문제점: {', '.join(validation['issues'])}")
        else:
            print(f"   ❌ {test_ticker} 히스토리컬 데이터 수집 실패")
            return False

        return True

    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_large_cap_collection():
    """대형주 수집 테스트 (제한적)"""
    print("\n=== 대형주 수집 테스트 (샘플) ===")

    try:
        from collectors.stock_data_collector import StockDataCollector

        collector = StockDataCollector()

        # 매우 높은 시가총액 기준으로 소수의 종목만 테스트
        min_market_cap = 100_000_000_000_000  # 100조원 (삼성전자 정도만)

        print(f"시가총액 {min_market_cap:,}원 이상 종목 수집...")
        large_cap_tickers = collector.collect_large_cap_tickers(
            min_market_cap=min_market_cap,
            target_date=date(2024, 12, 20)
        )

        print(f"✅ 대형주 {len(large_cap_tickers)}개 종목 수집:")
        for ticker in large_cap_tickers[:5]:  # 상위 5개만 출력
            print(f"   {ticker.ticker}({ticker.name}): {ticker.market_cap:,}원")

        return True

    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("StockDataCollector 클래스 실제 테스트를 시작합니다...\n")

    results = []

    # 1. Import 테스트
    results.append(("Import 테스트", test_stock_data_collector_imports()))

    # Import가 성공한 경우에만 나머지 테스트 진행
    if results[-1][1]:
        # 2. 기본 메서드 테스트
        results.append(("기본 메서드 테스트", test_collector_basic_methods()))

        # 3. 고급 메서드 테스트
        results.append(("고급 메서드 테스트", test_collector_advanced_methods()))

        # 4. 대형주 수집 테스트
        results.append(("대형주 수집 테스트", test_large_cap_collection()))
    else:
        print("Import가 실패하여 나머지 테스트를 건너뜁니다.")

    # 결과 요약
    print("\n" + "="*50)
    print("StockDataCollector 테스트 결과 요약")
    print("="*50)

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")

    print(f"\n전체: {passed_tests}/{total_tests} 테스트 통과")

    if passed_tests == total_tests:
        print("🎉 모든 StockDataCollector 테스트가 성공했습니다!")
        print("📊 데이터 수집 시스템이 정상적으로 작동하고 있습니다.")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        print("🔧 의존성 설치나 설정을 확인해주세요.")

if __name__ == "__main__":
    main()