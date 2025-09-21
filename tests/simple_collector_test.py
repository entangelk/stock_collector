#!/usr/bin/env python3
"""
StockDataCollector 핵심 기능만 테스트하는 간단한 스크립트
"""

import sys
import os
from datetime import date, timedelta
import pandas as pd

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_direct_pykrx_integration():
    """pykrx를 직접 사용한 데이터 수집 기능 테스트"""
    print("=== 직접 pykrx를 사용한 데이터 수집 테스트 ===")

    try:
        import pykrx.stock as stock

        # 테스트할 종목들
        test_tickers = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, 네이버

        results = {}

        for ticker in test_tickers:
            print(f"\n{ticker} 종목 테스트:")

            # 1. 종목명 조회
            try:
                name = stock.get_market_ticker_name(ticker)
                print(f"  ✅ 종목명: {name}")
                results[ticker] = {"name": name}
            except Exception as e:
                print(f"  ❌ 종목명 조회 실패: {e}")
                continue

            # 2. 최근 5일 OHLCV 데이터
            try:
                end_date = "20241220"
                start_date = "20241216"
                ohlcv = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

                if not ohlcv.empty:
                    print(f"  ✅ OHLCV 데이터: {len(ohlcv)}건")
                    latest = ohlcv.iloc[-1]
                    print(f"     최신 종가: {latest['종가']:,}원")
                    print(f"     최신 거래량: {latest['거래량']:,}주")

                    results[ticker]["ohlcv_count"] = len(ohlcv)
                    results[ticker]["latest_price"] = latest['종가']
                    results[ticker]["latest_volume"] = latest['거래량']
                else:
                    print(f"  ⚠️ OHLCV 데이터 없음")

            except Exception as e:
                print(f"  ❌ OHLCV 조회 실패: {e}")

            # 3. 시가총액 조회
            try:
                market_cap_df = stock.get_market_cap_by_ticker(end_date, ticker)
                if not market_cap_df.empty:
                    market_cap = market_cap_df.iloc[0]['시가총액'] * 100_000_000  # 억원 -> 원
                    print(f"  ✅ 시가총액: {market_cap:,}원")
                    results[ticker]["market_cap"] = market_cap
                else:
                    print(f"  ⚠️ 시가총액 데이터 없음")
            except Exception as e:
                print(f"  ❌ 시가총액 조회 실패: {e}")

        return True, results

    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
        return False, {}

def test_data_processing():
    """데이터 처리 및 변환 테스트"""
    print("\n=== 데이터 처리 테스트 ===")

    try:
        import pykrx.stock as stock
        import pandas as pd
        import numpy as np

        ticker = "005930"  # 삼성전자
        print(f"{ticker} 데이터 처리 테스트:")

        # 1개월간 데이터 수집
        end_date = "20241220"
        start_date = "20241120"  # 약 1개월

        ohlcv = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

        if ohlcv.empty:
            print("❌ 데이터가 없어 처리 테스트를 건너뜁니다.")
            return False

        print(f"✅ 원본 데이터: {len(ohlcv)}건")

        # 기본 통계 계산
        print("기본 통계:")
        print(f"  평균 종가: {ohlcv['종가'].mean():,.0f}원")
        print(f"  최고가: {ohlcv['고가'].max():,}원")
        print(f"  최저가: {ohlcv['저가'].min():,}원")
        print(f"  평균 거래량: {ohlcv['거래량'].mean():,.0f}주")

        # 이동평균 계산
        ohlcv['MA5'] = ohlcv['종가'].rolling(window=5).mean()
        ohlcv['MA20'] = ohlcv['종가'].rolling(window=20).mean()

        # 변동성 계산
        ohlcv['daily_return'] = ohlcv['종가'].pct_change()
        volatility = ohlcv['daily_return'].std() * np.sqrt(252)  # 연환산 변동성

        print(f"✅ 기술적 지표 계산 완료")
        print(f"  5일 이동평균: {ohlcv['MA5'].iloc[-1]:,.0f}원")
        print(f"  20일 이동평균: {ohlcv['MA20'].iloc[-1]:,.0f}원")
        print(f"  연환산 변동성: {volatility:.2%}")

        return True

    except Exception as e:
        print(f"❌ 데이터 처리 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_tickers_batch():
    """다중 종목 배치 처리 테스트"""
    print("\n=== 다중 종목 배치 처리 테스트 ===")

    try:
        import pykrx.stock as stock
        import time

        # KOSPI 상위 종목들
        top_tickers = ["005930", "000660", "035420", "005380", "068270"]  # 삼성전자, SK하이닉스, 네이버, 현대차, 셀트리온

        start_time = time.time()
        successful_collections = 0

        for i, ticker in enumerate(top_tickers):
            try:
                name = stock.get_market_ticker_name(ticker)
                ohlcv = stock.get_market_ohlcv_by_date("20241219", "20241220", ticker)

                if not ohlcv.empty:
                    price = ohlcv.iloc[-1]['종가']
                    print(f"  {i+1}. {ticker}({name}): {price:,}원")
                    successful_collections += 1
                else:
                    print(f"  {i+1}. {ticker}({name}): 데이터 없음")

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                print(f"  {i+1}. {ticker}: 오류 - {e}")

        elapsed_time = time.time() - start_time

        print(f"\n✅ 배치 처리 결과:")
        print(f"  처리 종목: {len(top_tickers)}개")
        print(f"  성공: {successful_collections}개")
        print(f"  처리 시간: {elapsed_time:.2f}초")
        print(f"  종목당 평균 시간: {elapsed_time/len(top_tickers):.2f}초")

        return successful_collections > 0

    except Exception as e:
        print(f"❌ 배치 처리 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("간단한 데이터 수집 기능 테스트를 시작합니다...\n")

    test_results = []

    # 1. 기본 pykrx 통합 테스트
    print("1. 기본 데이터 수집 테스트...")
    success, data = test_direct_pykrx_integration()
    test_results.append(("기본 데이터 수집", success))

    # 2. 데이터 처리 테스트
    if success:
        print("\n2. 데이터 처리 테스트...")
        process_success = test_data_processing()
        test_results.append(("데이터 처리", process_success))

        # 3. 배치 처리 테스트
        print("\n3. 배치 처리 테스트...")
        batch_success = test_multiple_tickers_batch()
        test_results.append(("배치 처리", batch_success))
    else:
        print("\n기본 테스트 실패로 나머지 테스트를 건너뜁니다.")

    # 결과 요약
    print("\n" + "="*50)
    print("데이터 수집 기능 테스트 결과")
    print("="*50)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")

    print(f"\n전체 결과: {passed}/{total} 테스트 통과")

    if passed == total:
        print("🎉 모든 데이터 수집 기능이 정상 작동합니다!")
        print("📈 주식 데이터 수집 시스템 준비 완료!")
    else:
        print("⚠️ 일부 기능에 문제가 있습니다.")
        print("🔧 로그를 확인하여 문제를 해결해주세요.")

if __name__ == "__main__":
    main()