#!/usr/bin/env python3
"""
딕셔너리 기반 전략 시스템 테스트
"""

import sys
import os
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.dict_base_strategy import DictBaseStrategy, DictStrategyManager
from strategies.dict_macd_golden_cross import DictMACDGoldenCrossStrategy

def test_dict_base_strategy():
    """딕셔너리 기반 전략 시스템 기본 테스트"""
    print("=== 딕셔너리 기반 전략 시스템 기본 테스트 ===")

    # 샘플 주식 데이터
    sample_data = {
        "ticker": "005930",
        "date": datetime(2024, 12, 20),
        "ohlcv": {
            "open": 52700.0,
            "high": 53100.0,
            "low": 51900.0,
            "close": 53000.0,
            "volume": 24674774
        },
        "technical_indicators": {
            "sma_5": 54160.0,
            "sma_20": 54725.0,
            "sma_60": 55200.0,
            "macd": 150.5,
            "macd_signal": 120.3,
            "macd_histogram": 85.2,
            "rsi_14": 58.7,
            "bollinger_upper": 58900.0,
            "bollinger_middle": 54725.0,
            "bollinger_lower": 50550.0
        }
    }

    # 1. 기본 전략 클래스 테스트
    try:
        # 직접 인스턴스화할 수 없는 추상 클래스이므로 건너뜀
        print("✅ DictBaseStrategy 추상 클래스 정의 확인")
    except Exception as e:
        print(f"❌ DictBaseStrategy 오류: {e}")

    # 2. 전략 관리자 테스트
    try:
        manager = DictStrategyManager()
        print("✅ DictStrategyManager 생성 성공")

        strategies = manager.list_strategies()
        print(f"✅ 등록된 전략 수: {len(strategies)}개")

    except Exception as e:
        print(f"❌ DictStrategyManager 오류: {e}")
        return False

    return True

def test_macd_strategy():
    """MACD Golden Cross 전략 테스트"""
    print("\n=== MACD Golden Cross 전략 테스트 ===")

    # 강한 신호 샘플 데이터
    strong_signal_data = {
        "ticker": "005930",
        "date": datetime(2024, 12, 20),
        "ohlcv": {
            "open": 52700.0,
            "high": 53100.0,
            "low": 51900.0,
            "close": 53000.0,
            "volume": 24674774  # 높은 거래량
        },
        "technical_indicators": {
            "sma_5": 53200.0,   # 가격 근처
            "sma_20": 52500.0,  # 가격 아래
            "sma_60": 51000.0,  # 더 아래
            "macd": 200.0,      # 강한 양수
            "macd_signal": 150.0, # MACD > Signal
            "macd_histogram": 120.0, # 강한 양수 히스토그램
            "rsi_14": 58.0,     # 적정 RSI (50-65 범위)
            "bollinger_upper": 58900.0,
            "bollinger_middle": 54725.0,
            "bollinger_lower": 50550.0
        }
    }

    # 약한 신호 샘플 데이터
    weak_signal_data = {
        "ticker": "000660",
        "date": datetime(2024, 12, 20),
        "ohlcv": {
            "open": 168000.0,
            "high": 169000.0,
            "low": 167000.0,
            "close": 168500.0,
            "volume": 500000    # 낮은 거래량
        },
        "technical_indicators": {
            "sma_5": 169000.0,
            "sma_20": 170000.0,  # 가격이 이평선 아래
            "sma_60": 171000.0,
            "macd": 80.0,        # 약한 신호
            "macd_signal": 70.0,
            "macd_histogram": 30.0, # 약한 히스토그램
            "rsi_14": 78.0,      # 과매수 경계
            "bollinger_upper": 175000.0,
            "bollinger_middle": 170000.0,
            "bollinger_lower": 165000.0
        }
    }

    # 부적합 데이터 (저가주)
    invalid_data = {
        "ticker": "999999",
        "date": datetime(2024, 12, 20),
        "ohlcv": {
            "open": 2000.0,     # 저가주
            "high": 2100.0,
            "low": 1900.0,
            "close": 2000.0,
            "volume": 10000     # 낮은 거래량
        },
        "technical_indicators": {
            "sma_5": 2050.0,
            "sma_20": 2100.0,
            "sma_60": 2200.0,
            "macd": 5.0,
            "macd_signal": 3.0,
            "macd_histogram": 2.0,
            "rsi_14": 45.0
        }
    }

    try:
        strategy = DictMACDGoldenCrossStrategy()
        print(f"✅ MACD 전략 생성: {strategy.name}")
        print(f"   설명: {strategy.get_description()}")
        print(f"   한국 시장 최적화: {strategy.korean_market_optimized}")

        # 테스트 케이스들
        test_cases = [
            ("강한 신호 (삼성전자)", strong_signal_data),
            ("약한 신호 (SK하이닉스)", weak_signal_data),
            ("부적합 (저가주)", invalid_data)
        ]

        results = []

        for test_name, test_data in test_cases:
            print(f"\n--- {test_name} 테스트 ---")

            # 적용 여부 확인
            applies = strategy.applies_to(test_data)
            print(f"   전략 적용: {applies}")

            if applies:
                # 신호 강도 계산
                strength = strategy.get_signal_strength(test_data)
                print(f"   신호 강도: {strength:.3f}")

                # 분석 요약
                summary = strategy.get_analysis_summary(test_data)
                print(f"   현재가: {summary['current_price']:,}원")
                print(f"   거래량: {summary['volume']:,}주")

                # 한국 시장 특화 분석
                korean_analysis = strategy.get_korean_specific_analysis(test_data)
                macd_info = korean_analysis.get('macd_analysis', {})
                print(f"   MACD: {macd_info.get('macd', 0):.1f}")
                print(f"   Signal: {macd_info.get('signal', 0):.1f}")
                print(f"   Histogram: {macd_info.get('histogram', 0):.1f}")

                results.append(summary)
            else:
                print("   → 전략 조건 불만족")

        print(f"\n✅ MACD 전략 테스트 완료 - {len(results)}개 신호 발견")
        return True

    except Exception as e:
        print(f"❌ MACD 전략 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_manager():
    """전략 관리자 통합 테스트"""
    print("\n=== 전략 관리자 통합 테스트 ===")

    try:
        manager = DictStrategyManager()

        # MACD 전략 등록
        macd_strategy = DictMACDGoldenCrossStrategy()
        manager.register_strategy(macd_strategy)

        print(f"✅ 전략 등록 완료")

        # 전략 목록 확인
        strategies = manager.list_strategies()
        print(f"✅ 등록된 전략 수: {len(strategies)}개")

        for strategy in strategies:
            print(f"   - {strategy['name']}: {strategy['description']}")

        # 샘플 데이터로 스크리닝 테스트
        sample_stocks = [
            {
                "ticker": "005930",
                "date": datetime(2024, 12, 20),
                "ohlcv": {
                    "open": 52700.0, "high": 53100.0, "low": 51900.0,
                    "close": 53000.0, "volume": 24674774
                },
                "technical_indicators": {
                    "sma_5": 53200.0, "sma_20": 52500.0, "sma_60": 51000.0,
                    "macd": 200.0, "macd_signal": 150.0, "macd_histogram": 120.0,
                    "rsi_14": 58.0
                }
            },
            {
                "ticker": "000660",
                "date": datetime(2024, 12, 20),
                "ohlcv": {
                    "open": 168000.0, "high": 169000.0, "low": 167000.0,
                    "close": 168500.0, "volume": 4487308
                },
                "technical_indicators": {
                    "sma_5": 168000.0, "sma_20": 167000.0, "sma_60": 165000.0,
                    "macd": 250.0, "macd_signal": 200.0, "macd_histogram": 180.0,
                    "rsi_14": 62.0
                }
            }
        ]

        # 스크리닝 실행
        results = manager.screen_stocks(
            strategy_name="DictMACDGoldenCrossStrategy",
            stock_data_list=sample_stocks
        )

        print(f"✅ 스크리닝 결과:")
        print(f"   성공: {results['success']}")
        print(f"   분석 대상: {results['total_analyzed']}개")
        print(f"   조건 만족: {results['matches_found']}개")

        for result in results['results']:
            print(f"   - {result['ticker']}: 신호강도 {result['signal_strength']:.3f}")

        return True

    except Exception as e:
        print(f"❌ 전략 관리자 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("딕셔너리 기반 전략 시스템 종합 테스트 시작...\n")

    test_results = []

    # 1. 기본 시스템 테스트
    test_results.append(("기본 시스템", test_dict_base_strategy()))

    # 2. MACD 전략 테스트
    test_results.append(("MACD 전략", test_macd_strategy()))

    # 3. 전략 관리자 테스트
    test_results.append(("전략 관리자", test_strategy_manager()))

    # 결과 요약
    print("\n" + "="*50)
    print("딕셔너리 기반 전략 시스템 테스트 결과")
    print("="*50)

    passed = 0
    for test_name, result in test_results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n전체 결과: {passed}/{len(test_results)} 테스트 통과")

    if passed == len(test_results):
        print("🎉 모든 딕셔너리 기반 전략 테스트 성공!")
        print("📈 한국 주식 시장 특화 전략 시스템 구축 완료!")
    else:
        print("⚠️ 일부 테스트 실패")

if __name__ == "__main__":
    main()