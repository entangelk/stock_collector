"""
한국 주식 시장 특화 기술적 분석 프롬프트
"""
from typing import Dict, Any
from datetime import datetime


def create_technical_analysis_prompt(
    strategy_result: Dict[str, Any],
    analysis_type: str = "detailed"
) -> str:
    """
    한국 주식 시장 특화 기술적 분석 프롬프트 생성

    Args:
        strategy_result: 전략 분석 결과
        analysis_type: 분석 타입 (detailed, summary, trading_signal)

    Returns:
        한국 시장 특화 기술적 분석 프롬프트
    """
    strategy_name = strategy_result.get('strategy_name', 'Unknown')
    matches_found = strategy_result.get('matches_found', 0)
    results = strategy_result.get('results', [])
    total_analyzed = strategy_result.get('total_analyzed', 0)

    # 전략별 한국 시장 특화 설명
    strategy_descriptions = {
        'dictmacdgoldencrossstrategy': {
            'name': 'MACD 골든크로스',
            'korean_context': 'KOSPI/KOSDAQ에서 외국인 매수 심리와 기관 투자자 유입을 나타내는 대표적인 강세 신호',
            'market_timing': '한국 시장 특성상 오전 9시~11시, 오후 2시~3시 거래량 증가 시점과 연계하여 분석'
        },
        'dictrsioversoldstrategy': {
            'name': 'RSI 과매도 반등',
            'korean_context': '한국 투자자들의 공포 매도 후 기술적 반등을 포착하는 전략으로, 특히 중소형주에서 효과적',
            'market_timing': '월말/분기말 리밸런싱과 연계된 매수 타이밍 분석이 중요'
        },
        'dictbollingersqueezestrategy': {
            'name': '볼린저 밴드 스퀴즈',
            'korean_context': '한국 시장의 박스권 횡보 후 급등/급락 패턴을 예측하는 변동성 돌파 전략',
            'market_timing': '실적 발표 시즌과 정책 발표 전후 변동성 확대 구간에서 특히 유의미'
        },
        'dictmovingaveragecrossoverstrategy': {
            'name': '이동평균선 교차',
            'korean_context': '한국 개인투자자들이 가장 선호하는 기술적 분석 신호로, 대중적 매매 심리 반영',
            'market_timing': '코스피 지수와의 동조화 현상 및 섹터 로테이션 관점에서 분석'
        }
    }

    current_strategy = strategy_descriptions.get(strategy_name, {
        'name': strategy_name,
        'korean_context': '한국 주식 시장 맞춤형 분석',
        'market_timing': '한국 시장 거래 패턴 고려 분석'
    })

    prompt = f"""당신은 한국 주식 시장을 15년 이상 분석해온 전문 기술적 분석가입니다.
KOSPI와 KOSDAQ의 고유한 특성을 깊이 이해하고 있으며, 한국 투자자들의 심리와 거래 패턴에 정통합니다.

## 📊 기술적 분석 개요
**분석 전략**: {current_strategy['name']}
**한국 시장 맥락**: {current_strategy['korean_context']}
**시장 타이밍**: {current_strategy['market_timing']}

## 📈 분석 결과 요약
- **조건 만족 종목**: {matches_found}개 (총 {total_analyzed}개 분석)
- **분석 시점**: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')} KST
- **시장 상황**: {"장중" if 9 <= datetime.now().hour <= 15 else "장후"}

## 🎯 발견된 투자 기회:"""

    if not results:
        prompt += """
현재 설정된 기술적 조건을 만족하는 종목이 없습니다.

### 🔍 대안 분석
1. **전략 매개변수 조정**: 현재 조건이 과도하게 엄격할 수 있습니다
2. **시장 환경 고려**: 현재 시장이 횡보 또는 약세 구간일 가능성
3. **섹터별 분석**: 특정 업종에서 기회 탐색 권장
4. **복합 전략**: 다른 기술적 지표와의 조합 고려

**추천 행동**: 전략 조건을 완화하거나 다른 시간대에 재분석을 권장합니다."""
        return prompt

    for i, result in enumerate(results[:5], 1):
        ticker = result.get('ticker', 'N/A')
        signal_strength = result.get('signal_strength', 0)
        current_price = result.get('current_price', 0)
        analysis_date = result.get('date', 'N/A')

        # 신호 강도에 따른 한국어 표현
        strength_desc = "매우 강함" if signal_strength >= 0.9 else "강함" if signal_strength >= 0.7 else "보통"

        prompt += f"""

### {i}. 📌 {ticker} (신호강도: {signal_strength:.3f} - {strength_desc})
- **현재가**: {current_price:,}원
- **분석일**: {analysis_date}
- **기술적 상태**: {_get_technical_status(signal_strength)}
- **한국 시장 포지션**: {_get_market_position(current_price)}"""

    if analysis_type == "detailed":
        prompt += f"""

## 🔬 상세 기술적 분석

### 1. 종목별 투자 매력도
각 종목의 기술적 지표 해석과 한국 시장 특성을 고려한 매력도를 평가해주세요:
- **거래량 패턴**: 외국인/기관/개인 매매 동향 추정
- **가격 모멘텀**: 한국 시장 특유의 급등/급락 패턴 분석
- **섹터 강도**: 업종별 자금 흐름과 연계 분석

### 2. 시장 환경 해석
- **코스피 지수 연동성**: 시장 전체 방향성과의 상관관계
- **거래 시간대별 특성**: 9-11시(오전 장), 13-15시(오후 장) 패턴
- **해외 시장 영향**: 미국, 중국 증시 동향 반영도

### 3. 투자 전략 수립
- **진입 시점**: 최적 매수 타이밍과 분할 매수 전략
- **목표가 설정**: 기술적 저항선 기반 목표가 산정
- **손절 기준**: 지지선 이탈 시 손절매 기준

### 4. 리스크 관리
- **시장 리스크**: 한국 시장 고유의 변동성 요인
- **종목 리스크**: 개별 종목의 기업 특수 상황
- **정책 리스크**: 정부 정책 및 규제 변화 영향

### 5. 포트폴리오 구성
- **비중 조절**: 신호 강도별 투자 비중 제안
- **분산 효과**: 섹터/시가총액별 분산 투자 방안
- **리밸런싱**: 수익률에 따른 포지션 조정 시점

**모든 분석은 한국 투자자의 실전 매매에 도움이 되도록 구체적이고 실용적으로 작성해주세요.**"""

    elif analysis_type == "summary":
        prompt += f"""

## 💡 핵심 투자 포인트

다음 관점에서 간결하고 명확하게 분석해주세요:

### 🎯 투자 추천 우선순위
신호 강도와 한국 시장 특성을 고려한 종목별 투자 매력도 순위를 제시해주세요.

### 📊 기술적 신호 해석
현재 기술적 패턴이 한국 시장에서 갖는 의미와 성공 확률을 설명해주세요.

### ⏰ 투자 타이밍
한국 시장의 거래 패턴을 고려한 최적 진입 시점을 제안해주세요.

### ⚠️ 주요 리스크
현재 시장 환경에서 주의해야 할 리스크 요인을 간단히 요약해주세요.

**3-5개 문장으로 핵심만 간결하게 정리해주세요.**"""

    else:  # trading_signal
        prompt += f"""

## 🚨 매매 신호 분석

### 📈 진입 신호 (매수)
- **즉시 매수**: 신호강도 0.8 이상 종목의 구체적 매수 타이밍
- **분할 매수**: 신호강도 0.6-0.8 종목의 단계적 진입 전략
- **관망**: 신호강도 0.6 미만 종목의 추가 확인 포인트

### 📉 청산 신호 (매도)
- **이익 실현**: 목표 수익률 달성 시 매도 타이밍
- **손절매**: 기술적 지지선 이탈 시 손절 기준
- **부분 매도**: 수익 보호를 위한 단계적 매도 전략

### ⏰ 시간대별 매매 전략
- **장 시작 (9:00-9:30)**: 갭 상승/하락 대응 방안
- **오전 장 (9:30-11:30)**: 주요 매매 세력 동향 파악
- **점심 시간 (11:30-13:00)**: 해외 시장 동향 점검
- **오후 장 (13:00-15:20)**: 마감 대비 포지션 조정
- **장 마감 (15:20-15:30)**: 당일 성과 확인 및 내일 전략

**각 종목별로 구체적인 매수/매도 가격대를 제시해주세요.**"""

    prompt += f"""

## 📋 추가 고려사항
- **업종 동향**: 해당 섹터의 최근 자금 흐름
- **외국인 동향**: 최근 외국인 매매 패턴 영향
- **기관 동향**: 연기금, 보험사 등 기관투자자 움직임
- **개인 심리**: 개미 투자자 매매 패턴과 시장 분위기

**분석 결과는 반드시 한국어로 작성하고, 실제 매매에 활용할 수 있도록 구체적인 수치와 함께 제시해주세요.**"""

    return prompt


def _get_technical_status(signal_strength: float) -> str:
    """신호 강도에 따른 기술적 상태 한국어 표현"""
    if signal_strength >= 0.9:
        return "매우 강한 매수 신호 - 즉시 진입 권장"
    elif signal_strength >= 0.8:
        return "강한 매수 신호 - 적극 매수 고려"
    elif signal_strength >= 0.7:
        return "양호한 매수 신호 - 분할 매수 권장"
    elif signal_strength >= 0.6:
        return "보통 매수 신호 - 신중한 진입"
    else:
        return "약한 신호 - 추가 확인 필요"


def _get_market_position(price: float) -> str:
    """가격대에 따른 한국 시장 포지션 분류"""
    if price >= 100000:
        return "대형주 (외국인/기관 선호)"
    elif price >= 50000:
        return "중형주 (안정성과 성장성 균형)"
    elif price >= 20000:
        return "중소형주 (성장성 중심)"
    elif price >= 5000:
        return "소형주 (높은 변동성)"
    else:
        return "저가주 (고위험 고수익)"