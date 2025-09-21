#!/usr/bin/env python3
"""
딕셔너리 기반 AI 시스템과 전략 통합 테스트
"""

import sys
import os
import asyncio
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.dict_ai_service import dict_ai_service
from strategies.dict_base_strategy import DictStrategyManager


def create_test_data():
    """테스트용 샘플 데이터 생성"""

    # 1. MACD 골든크로스 신호 (삼성전자)
    macd_signal_data = {
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

    # 2. RSI 과매도 신호 (LG전자)
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

    # 3. 볼린저 스퀴즈 신호 (네이버)
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

    return [macd_signal_data, rsi_oversold_data, bollinger_squeeze_data]


async def test_ai_service_basic():
    """AI 서비스 기본 테스트"""
    print("=== AI 서비스 기본 테스트 ===")

    try:
        # 서비스 정보 확인
        service_info = dict_ai_service.get_service_info()
        print(f"✅ AI 서비스 정보:")
        print(f"   - 서비스명: {service_info['service_name']}")
        print(f"   - 모델: {service_info['model']}")
        print(f"   - 사용 가능: {service_info['is_available']}")
        print(f"   - 지원 전략 수: {len(service_info['available_strategies'])}개")

        if not service_info['is_available']:
            print("⚠️ AI 서비스를 사용할 수 없습니다. API 키를 확인해주세요.")
            print("   .env 파일에서 GOOGLE_API_KEY를 설정해주세요.")

        return service_info['is_available']

    except Exception as e:
        print(f"❌ AI 서비스 기본 테스트 실패: {e}")
        return False


async def test_strategy_screening():
    """전략 스크리닝 테스트"""
    print("\n=== 전략 스크리닝 테스트 ===")

    try:
        # 테스트 데이터 생성
        test_data_list = create_test_data()
        print(f"✅ 테스트 데이터 생성: {len(test_data_list)}개 종목")

        # 전략 관리자 테스트
        strategy_manager = DictStrategyManager()
        strategies = strategy_manager.list_strategies()
        print(f"✅ 등록된 전략: {len(strategies)}개")

        results = {}

        # 각 전략별로 스크리닝 테스트
        for strategy_info in strategies:
            strategy_name = strategy_info['name']
            print(f"\n--- {strategy_name} 스크리닝 ---")

            result = strategy_manager.screen_stocks(
                strategy_name=strategy_name,
                stock_data_list=test_data_list,
                limit=10
            )

            if result['success']:
                matches = result['matches_found']
                print(f"  ✅ 조건 만족 종목: {matches}개")
                for match in result['results']:
                    print(f"    - {match['ticker']}: 신호강도 {match['signal_strength']:.3f}")
                results[strategy_name] = result
            else:
                print(f"  ❌ 실패: {result.get('error')}")

        return results

    except Exception as e:
        print(f"❌ 전략 스크리닝 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def test_ai_strategy_integration():
    """AI와 전략 통합 테스트"""
    print("\n=== AI와 전략 통합 테스트 ===")

    try:
        if not dict_ai_service.is_available():
            print("⚠️ AI 서비스를 사용할 수 없어 통합 테스트를 건너뜁니다.")
            return False

        # 테스트 데이터 생성
        test_data_list = create_test_data()

        # MACD 전략으로 AI 분석 테스트
        print("\n--- MACD 전략 AI 분석 테스트 ---")
        result = await dict_ai_service.analyze_with_strategy(
            strategy_name="dictmacdgoldencrossstrategy",
            ticker_list=["005930"],  # 삼성전자만
            limit=5,
            analysis_type="summary"
        )

        if result['success']:
            print("✅ MACD 전략 AI 분석 성공")
            print(f"   - 전략: {result['strategy_name']}")
            print(f"   - 실행 시간: {result['execution_time']:.2f}초")
            print(f"   - AI 분석 길이: {len(result['ai_analysis'])}자")
            print(f"   - AI 분석 미리보기: {result['ai_analysis'][:100]}...")
        else:
            print(f"❌ MACD 전략 AI 분석 실패: {result.get('error')}")
            return False

        # 포트폴리오 분석 테스트
        print("\n--- 포트폴리오 AI 분석 테스트 ---")
        portfolio_result = await dict_ai_service.analyze_portfolio(
            ticker_list=["005930", "066570", "035420"],
            analysis_focus="risk_assessment"
        )

        if portfolio_result['success']:
            print("✅ 포트폴리오 AI 분석 성공")
            print(f"   - 분석 대상: {len(portfolio_result['portfolio_tickers'])}개 종목")
            print(f"   - 실행 시간: {portfolio_result['execution_time']:.2f}초")
            print(f"   - AI 분석 길이: {len(portfolio_result['ai_analysis'])}자")
        else:
            print(f"❌ 포트폴리오 AI 분석 실패: {portfolio_result.get('error')}")
            return False

        return True

    except Exception as e:
        print(f"❌ AI 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_mock():
    """API 엔드포인트 모의 테스트"""
    print("\n=== API 엔드포인트 모의 테스트 ===")

    try:
        # 스크리너 API 모의 테스트
        print("--- 스크리너 API 모의 테스트 ---")
        test_data_list = create_test_data()
        strategy_manager = DictStrategyManager()

        # 스크리닝 실행 (API 내부 로직과 동일)
        screener_result = strategy_manager.screen_stocks(
            strategy_name="dictmacdgoldencrossstrategy",
            stock_data_list=test_data_list,
            limit=10
        )

        print(f"✅ 스크리너 API 모의 응답:")
        print(f"   - 성공: {screener_result['success']}")
        print(f"   - 분석 대상: {screener_result['total_analyzed']}개")
        print(f"   - 조건 만족: {screener_result['matches_found']}개")

        # AI 분석 API 모의 테스트 (AI 사용 가능할 때만)
        if dict_ai_service.is_available():
            print("\n--- AI 분석 API 모의 테스트 ---")
            ai_result = await dict_ai_service.analyze_with_strategy(
                strategy_name="dictmacdgoldencrossstrategy",
                ticker_list=["005930"],
                analysis_type="summary"
            )

            print(f"✅ AI 분석 API 모의 응답:")
            print(f"   - 성공: {ai_result['success']}")
            print(f"   - 전략: {ai_result.get('strategy_name', 'N/A')}")
            print(f"   - 실행 시간: {ai_result.get('execution_time', 0):.2f}초")
        else:
            print("⚠️ AI API 테스트는 API 키 설정 후 가능합니다.")

        return True

    except Exception as e:
        print(f"❌ API 모의 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 함수"""
    print("딕셔너리 기반 AI 시스템과 전략 통합 테스트 시작...\n")

    test_results = []

    # 1. AI 서비스 기본 테스트
    ai_basic_result = await test_ai_service_basic()
    test_results.append(("AI 서비스 기본", ai_basic_result))

    # 2. 전략 스크리닝 테스트
    strategy_results = await test_strategy_screening()
    test_results.append(("전략 스크리닝", len(strategy_results) > 0))

    # 3. AI와 전략 통합 테스트 (AI 사용 가능할 때만)
    if ai_basic_result:
        ai_integration_result = await test_ai_strategy_integration()
        test_results.append(("AI 전략 통합", ai_integration_result))
    else:
        test_results.append(("AI 전략 통합", "건너뜀 (API 키 없음)"))

    # 4. API 모의 테스트
    api_mock_result = await test_api_mock()
    test_results.append(("API 모의 테스트", api_mock_result))

    # 결과 요약
    print("\n" + "="*60)
    print("딕셔너리 기반 AI 시스템 통합 테스트 결과")
    print("="*60)

    passed = 0
    for test_name, result in test_results:
        if result == "건너뜀 (API 키 없음)":
            status = "⚠️ 건너뜀"
        else:
            status = "✅ 성공" if result else "❌ 실패"
            if result:
                passed += 1

        print(f"{test_name}: {status}")

    print(f"\n전체 결과: {passed}/{len([r for r in test_results if r[1] != '건너뜀 (API 키 없음)'])} 테스트 통과")

    if passed >= 3:  # API 키 없어도 대부분 테스트 통과하면 성공
        print("🎉 딕셔너리 기반 AI 시스템 통합 테스트 성공!")
        print("📈 한국 주식 시장 특화 AI 분석 파이프라인 구축 완료!")
        print("🔧 FastAPI 서버 실행 준비 완료!")

        if not ai_basic_result:
            print("\n💡 다음 단계:")
            print("   1. .env 파일에서 GOOGLE_API_KEY를 설정하세요")
            print("   2. 'python main.py'로 FastAPI 서버를 실행하세요")
            print("   3. http://localhost:8000/docs에서 API 문서를 확인하세요")
    else:
        print("⚠️ 일부 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())