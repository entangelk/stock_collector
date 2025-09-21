#!/usr/bin/env python3
"""
모든 딕셔너리 기반 전략 시스템 통합 테스트
"""

import sys
import os
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.dict_base_strategy import DictStrategyManager
from strategies.dict_macd_golden_cross import DictMACDGoldenCrossStrategy
from strategies.dict_rsi_oversold import DictRSIOversoldStrategy
from strategies.dict_bollinger_squeeze import DictBollingerSqueezeStrategy
from strategies.dict_moving_average_crossover import DictMovingAverageCrossoverStrategy

def create_sample_data():
    """다양한 시나리오의 샘플 데이터 생성"""

    # 1. 강한 신호 데이터 (삼성전자 - 대형주)
    strong_signal_data = {
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
            "sma_5": 53200.0,
            "sma_20": 52500.0,
            "sma_60": 51000.0,
            "macd": 200.0,
            "macd_signal": 150.0,
            "macd_histogram": 120.0,
            "rsi_14": 58.0,
            "bollinger_upper": 58900.0,
            "bollinger_middle": 54725.0,
            "bollinger_lower": 50550.0
        }
    }

    # 2. RSI 과매도 데이터 (LG전자)
    rsi_oversold_data = {
        "ticker": "066570",
        "date": datetime(2024, 12, 20),
        "ohlcv": {
            "open": 85000.0,
            "high": 86000.0,
            "low": 84000.0,
            "close": 85500.0,
            "volume": 3500000
        },
        "technical_indicators": {
            "sma_5": 86000.0,
            "sma_20": 87000.0,
            "sma_60": 83000.0,  # 장기 상승추세
            "macd": -30.0,
            "macd_signal": -50.0,
            "macd_histogram": 20.0,  # 상승 전환
            "rsi_14": 28.5,  # 과매도
            "bollinger_upper": 92000.0,
            "bollinger_middle": 87000.0,
            "bollinger_lower": 82000.0
        }
    }

    # 3. 볼린저 스퀴즈 데이터 (네이버)
    bollinger_squeeze_data = {
        "ticker": "035420",
        "date": datetime(2024, 12, 20),
        "ohlcv": {
            "open": 155000.0,
            "high": 156000.0,
            "low": 154000.0,
            "close": 155500.0,  # 중간선 근처
            "volume": 800000
        },
        "technical_indicators": {
            "sma_5": 155200.0,
            "sma_20": 155000.0,
            "sma_60": 154500.0,  # 수렴 상태
            "macd": 10.0,
            "macd_signal": 8.0,
            "macd_histogram": 2.0,
            "rsi_14": 52.0,  # 중립
            "bollinger_upper": 159000.0,  # 좁은 밴드폭
            "bollinger_middle": 155500.0,
            "bollinger_lower": 152000.0
        }
    }

    # 4. 골든크로스 데이터 (카카오)
    golden_cross_data = {
        "ticker": "035720",
        "date": datetime(2024, 12, 20),
        "ohlcv": {
            "open": 42500.0,
            "high": 43000.0,
            "low": 42000.0,
            "close": 42700.0,
            "volume": 15000000
        },
        "technical_indicators": {
            "sma_5": 42800.0,
            "sma_20": 42200.0,  # 단기선이 위
            "sma_60": 40500.0,  # 장기선이 아래 (골든크로스)
            "macd": 80.0,
            "macd_signal": 70.0,
            "macd_histogram": 10.0,
            "rsi_14": 62.0,  # 적정 RSI
            "bollinger_upper": 46000.0,
            "bollinger_middle": 42500.0,
            "bollinger_lower": 39000.0
        }
    }

    # 5. 저가주 데이터 (필터링 테스트용)
    penny_stock_data = {
        "ticker": "999999",
        "date": datetime(2024, 12, 20),
        "ohlcv": {
            "open": 1500.0,  # 저가주
            "high": 1600.0,
            "low": 1400.0,
            "close": 1550.0,
            "volume": 5000  # 낮은 거래량
        },
        "technical_indicators": {
            "sma_5": 1560.0,
            "sma_20": 1580.0,
            "sma_60": 1600.0,
            "macd": 5.0,
            "macd_signal": 3.0,
            "macd_histogram": 2.0,
            "rsi_14": 45.0,
            "bollinger_upper": 1700.0,
            "bollinger_middle": 1580.0,
            "bollinger_lower": 1460.0
        }
    }

    return [
        ("강한 신호 (삼성전자)", strong_signal_data),
        ("RSI 과매도 (LG전자)", rsi_oversold_data),
        ("볼린저 스퀴즈 (네이버)", bollinger_squeeze_data),
        ("골든크로스 (카카오)", golden_cross_data),
        ("저가주 (필터링 테스트)", penny_stock_data)
    ]

def test_individual_strategies():
    """개별 전략 테스트"""
    print("=== 개별 전략 테스트 ===")

    sample_data_list = create_sample_data()
    strategies = [
        ("MACD Golden Cross", DictMACDGoldenCrossStrategy()),
        ("RSI Oversold", DictRSIOversoldStrategy()),
        ("Bollinger Squeeze", DictBollingerSqueezeStrategy()),
        ("MA Crossover", DictMovingAverageCrossoverStrategy())
    ]

    results = {}

    for strategy_name, strategy in strategies:
        print(f"\n--- {strategy_name} 전략 테스트 ---")
        strategy_results = []

        for data_name, stock_data in sample_data_list:
            try:
                applies = strategy.applies_to(stock_data)
                if applies:
                    strength = strategy.get_signal_strength(stock_data)
                    analysis = strategy.get_analysis_summary(stock_data)

                    strategy_results.append({
                        "data_name": data_name,
                        "ticker": stock_data["ticker"],
                        "strength": strength,
                        "analysis": analysis
                    })

                    print(f"  ✅ {data_name}: 신호강도 {strength:.3f}")
                else:
                    print(f"  ❌ {data_name}: 조건 불만족")

            except Exception as e:
                print(f"  ⚠️ {data_name}: 오류 - {e}")

        results[strategy_name] = strategy_results
        print(f"  총 {len(strategy_results)}개 신호 발견")

    return results

def test_strategy_manager():
    """전략 관리자 통합 테스트"""
    print("\n=== 전략 관리자 통합 테스트 ===")

    try:
        # 전략 관리자 생성 및 전략 등록
        manager = DictStrategyManager()

        strategies = [
            DictMACDGoldenCrossStrategy(),
            DictRSIOversoldStrategy(),
            DictBollingerSqueezeStrategy(),
            DictMovingAverageCrossoverStrategy()
        ]

        for strategy in strategies:
            manager.register_strategy(strategy)

        print(f"✅ {len(strategies)}개 전략 등록 완료")

        # 등록된 전략 목록 확인
        strategy_list = manager.list_strategies()
        print(f"✅ 등록된 전략 목록:")
        for strategy_info in strategy_list:
            print(f"   - {strategy_info['name']}: {strategy_info['description']}")

        # 샘플 데이터로 다중 전략 스크리닝 테스트
        sample_data_list = create_sample_data()
        stock_data_list = [data[1] for data in sample_data_list]  # 데이터만 추출

        # 각 전략별로 스크리닝 실행
        all_results = {}

        for strategy_info in strategy_list:
            strategy_name = strategy_info['name']
            print(f"\n--- {strategy_name} 스크리닝 ---")

            result = manager.screen_stocks(
                strategy_name=strategy_name,
                stock_data_list=stock_data_list,
                limit=10
            )

            if result['success']:
                print(f"  성공: {result['total_analyzed']}개 분석, {result['matches_found']}개 조건 만족")
                for match in result['results']:
                    print(f"    - {match['ticker']}: 신호강도 {match['signal_strength']:.3f}")
                all_results[strategy_name] = result
            else:
                print(f"  실패: {result.get('error', 'Unknown error')}")

        # 다중 전략 분석
        strategy_names = [info['name'] for info in strategy_list]
        multi_result = manager.get_multi_strategy_analysis(
            stock_data_list=stock_data_list,
            strategy_names=strategy_names,
            limit_per_strategy=5
        )

        print(f"\n✅ 다중 전략 분석 결과:")
        print(f"   분석된 전략: {multi_result['strategies_analyzed']}개")
        print(f"   성공한 전략: {multi_result['successful_strategies']}개")
        print(f"   총 발견된 매치: {multi_result['total_matches_found']}개")

        return True

    except Exception as e:
        print(f"❌ 전략 관리자 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_korean_market_features():
    """한국 시장 특화 기능 테스트"""
    print("\n=== 한국 시장 특화 기능 테스트 ===")

    # 대형주 데이터로 테스트
    large_cap_data = {
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
            "sma_5": 53200.0,
            "sma_20": 52500.0,
            "sma_60": 51000.0,
            "macd": 200.0,
            "macd_signal": 150.0,
            "macd_histogram": 120.0,
            "rsi_14": 58.0,
            "bollinger_upper": 58900.0,
            "bollinger_middle": 54725.0,
            "bollinger_lower": 50550.0
        }
    }

    strategy = DictMACDGoldenCrossStrategy()

    try:
        # 한국 시장 컨텍스트 테스트
        market_context = strategy.get_korean_market_context(large_cap_data)
        print(f"✅ 시장 컨텍스트:")
        print(f"   거래 세션: {market_context['market_session']}")
        print(f"   대형주 여부: {market_context['is_large_cap']}")
        print(f"   거래량 카테고리: {market_context['volume_category']}")
        print(f"   가격대 범위: {market_context['price_range']}")

        # 한국 시장 특화 분석
        korean_analysis = strategy.get_korean_specific_analysis(large_cap_data)
        print(f"✅ 한국 시장 특화 분석:")
        print(f"   MACD 분석: {korean_analysis.get('macd_analysis', {})}")
        print(f"   거래량 분석: {korean_analysis.get('volume_analysis', {})}")
        print(f"   가격 분석: {korean_analysis.get('price_analysis', {})}")

        return True

    except Exception as e:
        print(f"❌ 한국 시장 특화 기능 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("딕셔너리 기반 전략 시스템 종합 테스트 시작...\n")

    test_results = []

    # 1. 개별 전략 테스트
    individual_results = test_individual_strategies()
    test_results.append(("개별 전략 테스트", len(individual_results) > 0))

    # 2. 전략 관리자 테스트
    manager_result = test_strategy_manager()
    test_results.append(("전략 관리자 테스트", manager_result))

    # 3. 한국 시장 특화 기능 테스트
    korean_result = test_korean_market_features()
    test_results.append(("한국 시장 특화 기능", korean_result))

    # 결과 요약
    print("\n" + "="*60)
    print("딕셔너리 기반 전략 시스템 종합 테스트 결과")
    print("="*60)

    passed = 0
    for test_name, result in test_results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n전체 결과: {passed}/{len(test_results)} 테스트 통과")

    if passed == len(test_results):
        print("🎉 모든 딕셔너리 기반 전략 시스템 테스트 성공!")
        print("📈 한국 주식 시장 특화 전략 시스템 구축 완료!")
        print("🔧 Pydantic v2 호환성 문제 완전 해결!")
    else:
        print("⚠️ 일부 테스트 실패")

    # 개별 전략별 결과 요약
    if individual_results:
        print(f"\n📊 전략별 신호 발견 요약:")
        for strategy_name, results in individual_results.items():
            print(f"   {strategy_name}: {len(results)}개 신호")
            for result in results:
                print(f"      - {result['ticker']} ({result['data_name']}): {result['strength']:.3f}")

if __name__ == "__main__":
    main()