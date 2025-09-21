"""
한국 주식 시장 특화 시장 개관 프롬프트
"""
from typing import Dict, Any, List
from datetime import datetime


def create_market_overview_prompt(
    multi_result: Dict[str, Any],
    ticker_list: List[str],
    analysis_focus: str = "market_overview"
) -> str:
    """
    한국 주식 시장 특화 시장 개관 프롬프트 생성

    Args:
        multi_result: 다중 전략 분석 결과
        ticker_list: 분석 대상 종목 리스트
        analysis_focus: 분석 초점 (market_overview, sector_analysis, market_timing)

    Returns:
        한국 시장 특화 시장 개관 프롬프트
    """
    current_time = datetime.now()
    market_status = "장중" if 9 <= current_time.hour <= 15 else "장후"

    strategies_analyzed = multi_result.get('strategies_analyzed', 0)
    successful_strategies = multi_result.get('successful_strategies', 0)
    total_matches = multi_result.get('total_matches_found', 0)

    prompt = f"""당신은 한국 주식 시장을 20년 이상 분석해온 수석 시장 애널리스트입니다.
KOSPI와 KOSDAQ의 역사적 패턴, 한국 특유의 시장 참여자 구조, 그리고 글로벌 시장과의 상관관계를 깊이 이해하고 있습니다.

## 🏛️ 한국 시장 개관 분석

### 📊 분석 현황
- **분석 시점**: {current_time.strftime('%Y년 %m월 %d일 %H시 %M분')} KST ({market_status})
- **분석 대상**: {len(ticker_list)}개 종목
- **적용 전략**: {strategies_analyzed}개 (성공: {successful_strategies}개)
- **발견된 기회**: {total_matches}개

### 🎯 분석 대상 종목
{', '.join(ticker_list)}

## 📈 다중 전략 분석 결과:"""

    # 전략별 결과 상세 분석
    if 'results_by_strategy' in multi_result:
        for strategy_name, result in multi_result['results_by_strategy'].items():
            strategy_korean_name = _get_strategy_korean_name(strategy_name)
            matches_found = result.get('matches_found', 0)

            prompt += f"""

### 🔍 {strategy_korean_name} 전략
- **매치된 종목**: {matches_found}개
- **시장 시사점**: {_get_strategy_market_implication(strategy_name, matches_found)}"""

            if matches_found > 0 and 'results' in result:
                prompt += "\n- **발견된 종목들**:"
                for match in result['results'][:3]:  # 상위 3개만 표시
                    ticker = match.get('ticker', 'N/A')
                    signal_strength = match.get('signal_strength', 0)
                    prompt += f"\n  - {ticker} (신호강도: {signal_strength:.3f})"

    if analysis_focus == "market_overview":
        prompt += f"""

## 🌐 한국 시장 전체 분석

### 1. 현재 시장 상황 진단
다음 관점에서 한국 시장의 현재 상태를 분석해주세요:

#### 📊 기술적 시장 상태
- **KOSPI 지수 분석**: 현재 기술적 위치와 주요 지지/저항선
- **KOSDAQ 지수 분석**: 중소형주 시장의 상대적 강도
- **시장 폭 지표**: 상승종목/하락종목 비율을 통한 시장 건전성
- **거래량 분석**: 평균 거래량 대비 현재 거래량 수준

#### 🌍 글로벌 시장 연동성
- **미국 시장 영향**: S&P500, 나스닥과의 상관관계
- **중국 시장 영향**: 상하이, 심천 증시가 한국 시장에 미치는 영향
- **환율 요인**: 원/달러 환율이 외국인 투자심리에 미치는 영향
- **원자재 가격**: 유가, 금가격 등이 관련 섹터에 미치는 영향

### 2. 시장 참여자 동향 분석
#### 👥 투자주체별 매매 패턴
- **외국인 투자자**: 최근 매수/매도 흐름과 선호 섹터
- **기관투자자**: 연기금, 보험사 등의 포트폴리오 리밸런싱 동향
- **개인투자자**: 개미 투자자들의 시장 참여도와 매매 패턴
- **프로그램 매매**: 차익거래, 바스켓 거래의 시장 영향

### 3. 섹터별 자금 흐름
현재 발견된 투자 기회들을 바탕으로 섹터별 자금 흐름을 분석해주세요:
- **강세 섹터**: 다중 전략에서 많은 종목이 발견된 업종
- **약세 섹터**: 상대적으로 투자 기회가 부족한 업종
- **로테이션 패턴**: 섹터 간 자금 이동 현황

### 4. 시장 리스크 요인
#### ⚠️ 단기 리스크 (1-2주)
- **정책 발표**: 정부 정책이나 금융위원회 발표 예정
- **실적 발표**: 주요 기업들의 분기 실적 발표 일정
- **해외 이벤트**: 미국 FOMC, 중국 정책 발표 등

#### ⚠️ 중기 리스크 (1-3개월)
- **경제 지표**: GDP, 물가, 고용률 등 주요 경제 지표
- **금리 정책**: 한국은행 기준금리 변동 가능성
- **환율 변동**: 원화 강세/약세가 수출기업에 미치는 영향

### 5. 투자 전략 제안
#### 🎯 단기 투자 전략 (1-4주)
- **관심 섹터**: 현재 기술적 조건을 만족하는 업종 집중
- **포지션 크기**: 시장 변동성을 고려한 적정 투자 비중
- **리스크 관리**: 단기 변동성에 대한 대응 방안

#### 🎯 중기 투자 전략 (1-6개월)
- **핵심 테마**: 한국 경제의 구조적 변화를 반영한 투자 테마
- **포트폴리오 구성**: 대형주/중소형주, 성장주/가치주 균형
- **리밸런싱**: 시장 상황 변화에 따른 포트폴리오 조정 시점

**모든 분석은 한국 시장의 고유한 특성을 반영하여 실용적이고 구체적으로 작성해주세요.**"""

    elif analysis_focus == "sector_analysis":
        prompt += f"""

## 🏭 섹터별 심층 분석

### 1. 업종별 투자 기회 분포
현재 다중 전략 분석에서 발견된 종목들의 업종별 분포를 바탕으로:

#### 📊 강세 업종 분석
다중 전략에서 많은 매치가 발견된 업종들에 대해:
- **업종별 특징**: 해당 업종의 현재 기술적/펀더멘털 상태
- **성장 동력**: 업종 성장을 이끄는 주요 요인들
- **투자 포인트**: 해당 업종 투자 시 핵심 고려사항

#### 📉 약세 업종 분석
상대적으로 투자 기회가 적은 업종들에 대해:
- **약세 원인**: 기술적/펀더멘털 약세 요인 분석
- **반등 가능성**: 향후 반등 시나리오와 조건
- **회피 권고**: 현재 투자를 피해야 할 이유

### 2. 섹터 로테이션 전략
- **현재 단계**: 시장 사이클에서 현재 한국 시장의 위치
- **다음 강세 섹터**: 향후 자금이 유입될 가능성이 높은 업종
- **로테이션 타이밍**: 섹터 간 이동 시점 예측

### 3. 업종별 리스크 요인
각 주요 업종별로 현재 직면한 리스크와 기회 요인을 분석해주세요."""

    else:  # market_timing
        prompt += f"""

## ⏰ 시장 타이밍 분석

### 1. 현재 시장 사이클 위치
- **한국 시장 사이클**: 현재 강세/약세/횡보 구간 중 어디에 위치
- **글로벌 사이클**: 전세계 주식시장 사이클과의 비교
- **역사적 패턴**: 과거 유사한 시장 상황과의 비교 분석

### 2. 단기 시장 타이밍 (1-4주)
#### 📈 매수 타이밍 지표
- **기술적 신호**: 현재 발견된 다중 전략 신호들의 시장 시사점
- **시장 심리**: VIX, 풋콜 비율 등 공포/탐욕 지표
- **자금 흐름**: 외국인, 기관의 순매수/매도 전환 신호

#### ⏳ 대기 신호
- **조정 가능성**: 단기 조정이 예상되는 기술적 신호들
- **이벤트 리스크**: 예정된 중요 발표나 이벤트들
- **과열 지표**: 시장 과열을 나타내는 신호들

### 3. 중기 시장 타이밍 (1-6개월)
- **추세 전환 신호**: 중기 추세 변화를 알리는 주요 지표들
- **계절성 패턴**: 한국 시장의 월별/분기별 특성 고려
- **정책 사이클**: 정부 정책 변화가 시장에 미치는 중기적 영향

**시장 타이밍 분석은 확률적 관점에서 접근하여 구체적인 진입/청산 시점을 제시해주세요.**"""

    prompt += f"""

## 📋 종합 결론 및 실행 방안

### 🎯 핵심 포인트 요약
- **시장 현황**: 한 문장으로 현재 한국 시장 상황 요약
- **주요 기회**: 가장 유망한 투자 기회 3가지
- **핵심 리스크**: 반드시 주의해야 할 리스크 요인 3가지

### 📈 실행 액션 플랜
1. **즉시 실행**: 오늘/내일 바로 실행할 수 있는 투자 행동
2. **단기 관찰**: 1-2주 내 모니터링할 지표나 종목들
3. **중기 준비**: 1-3개월 내 준비해야 할 투자 전략

### ⚠️ 주의사항
- **시장 변동성**: 예상되는 변동성 수준과 대응 방안
- **리스크 관리**: 포지션 크기 및 손절 기준
- **모니터링 포인트**: 지속적으로 관찰해야 할 지표들

**모든 분석은 한국 투자자가 실제로 활용할 수 있도록 구체적이고 실용적으로 작성해주세요.
특히 한국 시장의 특수성(개장/폐장 시간, 거래제도, 세금 등)을 반영하여 현실적인 조언을 제공해주세요.**"""

    return prompt


def _get_strategy_korean_name(strategy_name: str) -> str:
    """전략명을 한국어로 변환"""
    strategy_names = {
        'dictmacdgoldencrossstrategy': 'MACD 골든크로스',
        'dictrsioversoldstrategy': 'RSI 과매도 반등',
        'dictbollingersqueezestrategy': '볼린저 밴드 스퀴즈',
        'dictmovingaveragecrossoverstrategy': '이동평균선 교차'
    }
    return strategy_names.get(strategy_name, strategy_name)


def _get_strategy_market_implication(strategy_name: str, matches_found: int) -> str:
    """전략별 시장 시사점 분석"""
    implications = {
        'dictmacdgoldencrossstrategy': {
            'high': '시장에 강한 상승 모멘텀이 형성되고 있으며, 기관투자자들의 적극적인 매수세가 예상됩니다.',
            'medium': '선별적인 상승 모멘텀이 나타나고 있어, 종목별 차별화가 진행 중입니다.',
            'low': '전반적인 상승 모멘텀이 부족한 상황으로, 시장이 방향성을 찾지 못하고 있습니다.'
        },
        'dictrsioversoldstrategy': {
            'high': '과도한 매도 압력 이후 기술적 반등 구간에 진입했으며, 저가 매수 기회가 확대되고 있습니다.',
            'medium': '일부 종목에서 과매도 반등 신호가 나타나고 있어, 선별적 접근이 필요합니다.',
            'low': '시장 전반의 매도 압력이 지속되고 있어, 추가적인 조정 가능성을 염두에 두어야 합니다.'
        },
        'dictbollingersqueezestrategy': {
            'high': '변동성 수축 이후 대규모 방향성 돌파가 임박했으며, 큰 가격 변동이 예상됩니다.',
            'medium': '일부 종목에서 변동성 돌파 준비가 감지되고 있어, 모멘텀 투자 기회가 있습니다.',
            'low': '시장이 박스권에서 벗어나지 못하고 있어, 추세 투자보다는 구간 매매가 적합합니다.'
        },
        'dictmovingaveragecrossoverstrategy': {
            'high': '다수 종목에서 이평선 정배열이 형성되고 있어, 시장 전반의 상승 추세가 강화되고 있습니다.',
            'medium': '선별적인 이평선 골든크로스가 나타나고 있어, 개별 종목의 추세 변화에 주목해야 합니다.',
            'low': '이평선 배열이 불분명한 상황으로, 명확한 추세가 형성되지 않았습니다.'
        }
    }

    level = 'high' if matches_found >= 5 else 'medium' if matches_found >= 2 else 'low'
    return implications.get(strategy_name, {}).get(level, '시장 상황에 대한 추가 분석이 필요합니다.')