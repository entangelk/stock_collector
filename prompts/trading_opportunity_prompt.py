"""
한국 주식 시장 특화 매매 기회 발굴 프롬프트
"""
from typing import Dict, Any
from datetime import datetime


def create_trading_opportunity_prompt(
    strategy_result: Dict[str, Any],
    analysis_type: str = "trading_opportunity"
) -> str:
    """
    한국 주식 시장 특화 매매 기회 발굴 프롬프트 생성

    Args:
        strategy_result: 전략 분석 결과
        analysis_type: 분석 타입 (trading_opportunity, entry_signals, exit_signals)

    Returns:
        한국 시장 특화 매매 기회 프롬프트
    """
    strategy_name = strategy_result.get('strategy_name', 'Unknown')
    matches_found = strategy_result.get('matches_found', 0)
    results = strategy_result.get('results', [])

    current_time = datetime.now()
    market_hours = "장중" if 9 <= current_time.hour <= 15 else "장후"
    trading_session = _get_trading_session(current_time.hour)

    prompt = f"""당신은 한국 주식 시장에서 15년 이상의 실전 매매 경험을 가진 전문 트레이더입니다.
단타, 스윙, 중장기 투자의 모든 영역에 정통하며, 한국 시장의 독특한 매매 패턴과 투자자 심리를 완벽히 파악하고 있습니다.

## 🎯 매매 기회 분석 리포트

### 📊 현재 시장 상황
- **분석 시점**: {current_time.strftime('%Y년 %m월 %d일 %H시 %M분')} KST
- **시장 상태**: {market_hours} ({trading_session})
- **분석 전략**: {_get_strategy_korean_name(strategy_name)}
- **발견된 기회**: {matches_found}개

### 🔍 전략별 매매 포인트
{_get_strategy_trading_characteristics(strategy_name)}

## 💰 구체적 매매 기회"""

    if not results:
        prompt += """

### ⚠️ 현재 매매 기회 부재

**상황 분석:**
- 설정된 기술적 조건을 만족하는 종목이 현재 없습니다
- 시장이 전략에 적합하지 않은 구간에 있을 가능성이 높습니다

**대응 전략:**
1. **조건 완화**: 신호 강도 기준을 낮춰 더 많은 기회 탐색
2. **다른 전략**: 현재 시장 상황에 더 적합한 전략으로 전환
3. **관망**: 조건이 갖춰질 때까지 대기하며 모니터링
4. **시간대 변경**: 다른 시간대에 재분석 실시

**추천 행동:**
- 오늘은 신규 포지션보다는 기존 포지션 관리에 집중
- 내일 장 시작 전 재분석으로 새로운 기회 탐색"""
        return prompt

    for i, result in enumerate(results[:3], 1):  # 상위 3개 집중 분석
        ticker = result.get('ticker', 'N/A')
        signal_strength = result.get('signal_strength', 0)
        current_price = result.get('current_price', 0)

        prompt += f"""

### {i}. 🎯 {ticker} - 신호강도 {signal_strength:.3f}

#### 📈 매매 기본 정보
- **현재가**: {current_price:,}원
- **매매 등급**: {_get_trading_grade(signal_strength)}
- **포지션 크기**: {_get_position_size_recommendation(signal_strength)}
- **투자 성향**: {_get_investment_style_match(current_price)}

#### 🚨 진입 전략
- **즉시 매수가**: {current_price:,}원 (현재가 수준)
- **분할 매수**: {_get_split_buy_strategy(current_price)}
- **최대 대기가**: {int(current_price * 0.97):,}원 (3% 하회 시)

#### 🎯 목표가 설정
{_get_target_price_strategy(current_price, signal_strength)}

#### ⛔ 손절 기준
- **기술적 손절**: {int(current_price * 0.92):,}원 (8% 손실)
- **시간 손절**: 진입 후 5거래일 내 목표 달성 실패 시
- **추세 손절**: 이동평균선 이탈 시

#### ⏰ 시간대별 매매 전략
{_get_time_based_trading_strategy(current_time.hour)}"""

    prompt += f"""

## 📋 실전 매매 체크리스트

### ✅ 매수 전 최종 점검
1. **자금 관리**: 투자 가능 자금 내에서 매수인가?
2. **리스크 한도**: 전체 포트폴리오 대비 적정 비중인가?
3. **시장 상황**: 전체 시장 분위기가 매수에 적합한가?
4. **뉴스 체크**: 해당 종목/섹터 악재 뉴스는 없는가?
5. **기술적 확인**: 다른 기술적 지표도 매수를 지지하는가?

### 📊 포지션 관리 원칙
1. **분산 투자**: 한 종목 집중도 20% 이하 유지
2. **손절 준수**: 설정된 손절선 반드시 준수
3. **수익 실현**: 목표 수익률 달성 시 단계적 매도
4. **재진입**: 매도 후 재차 좋은 신호 시 재진입 고려
5. **감정 통제**: FOMO나 패닉에 의한 충동 매매 금지

### 🚨 위험 신호 모니터링
- **시장 지수**: KOSPI 주요 지지선 이탈 시 전체 포지션 축소
- **외국인 동향**: 연속 3일 이상 순매도 시 신중 모드 전환
- **환율**: 원/달러 1,400원 돌파 시 수출주 포지션 점검
- **유가**: 10% 이상 급등/급락 시 관련 섹터 영향 점검

**모든 매매는 계획에 의해 실행하고, 감정에 의한 즉흥적 결정은 피하세요.
한국 시장의 특성상 변동성이 크므로 항상 충분한 안전마진을 확보하시기 바랍니다.**"""

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


def _get_trading_session(hour: int) -> str:
    """현재 시간에 따른 거래 세션 구분"""
    if 9 <= hour < 10:
        return "장 시작 구간"
    elif 10 <= hour < 12:
        return "오전 활발 구간"
    elif 12 <= hour < 13:
        return "점심 시간대"
    elif 13 <= hour < 15:
        return "오후 거래 구간"
    elif hour == 15:
        return "마감 구간"
    else:
        return "장후 시간"


def _get_strategy_trading_characteristics(strategy_name: str) -> str:
    """전략별 매매 특성 설명"""
    characteristics = {
        'dictmacdgoldencrossstrategy': """
**MACD 골든크로스 매매 특성:**
- **투자 기간**: 2-4주 스윙 트레이딩
- **성공률**: 약 65-70% (한국 시장 기준)
- **평균 수익률**: 8-15%
- **최적 시장**: 상승 추세 또는 횡보 후 상승 전환 구간
- **주의사항**: 하락장에서는 거짓 신호 가능성 높음""",
        'dictrsioversoldstrategy': """
**RSI 과매도 반등 매매 특성:**
- **투자 기간**: 3-7일 단기 반등 매매
- **성공률**: 약 60-65% (변동성 시장에서 효과적)
- **평균 수익률**: 5-12%
- **최적 시장**: 급락 후 반등 구간, 박스권 하단
- **주의사항**: 지속적 하락 추세에서는 추가 하락 위험""",
        'dictbollingersqueezestrategy': """
**볼린저 밴드 스퀴즈 매매 특성:**
- **투자 기간**: 1-3주 돌파 후 추세 추종
- **성공률**: 약 55-60% (큰 수익 vs 작은 손실)
- **평균 수익률**: 12-25% (성공 시)
- **최적 시장**: 박스권 횡보 후 추세 돌파 구간
- **주의사항**: 방향성 예측 어려움, 빠른 손절 중요""",
        'dictmovingaveragecrossoverstrategy': """
**이동평균선 교차 매매 특성:**
- **투자 기간**: 2-6주 중기 추세 투자
- **성공률**: 약 55-60% (안정적 수익)
- **평균 수익률**: 10-20%
- **최적 시장**: 명확한 추세 형성 구간
- **주의사항**: 횡보장에서 잦은 거짓 신호 발생"""
    }
    return characteristics.get(strategy_name, "매매 특성 정보를 확인 중입니다.")


def _get_trading_grade(signal_strength: float) -> str:
    """신호 강도에 따른 매매 등급"""
    if signal_strength >= 0.9:
        return "A급 (최우선 매수)"
    elif signal_strength >= 0.8:
        return "B급 (적극 매수)"
    elif signal_strength >= 0.7:
        return "C급 (분할 매수)"
    elif signal_strength >= 0.6:
        return "D급 (신중 매수)"
    else:
        return "E급 (관망 권장)"


def _get_position_size_recommendation(signal_strength: float) -> str:
    """신호 강도에 따른 포지션 크기 권장"""
    if signal_strength >= 0.9:
        return "계획 투자금의 80-100%"
    elif signal_strength >= 0.8:
        return "계획 투자금의 60-80%"
    elif signal_strength >= 0.7:
        return "계획 투자금의 40-60%"
    elif signal_strength >= 0.6:
        return "계획 투자금의 20-40%"
    else:
        return "계획 투자금의 10-20%"


def _get_investment_style_match(price: float) -> str:
    """가격대에 따른 투자 성향 매칭"""
    if price >= 100000:
        return "안정형 투자자 적합 (대형주)"
    elif price >= 50000:
        return "안정추구형 투자자 적합 (우량 중형주)"
    elif price >= 20000:
        return "적극투자형 투자자 적합 (성장 중소형주)"
    elif price >= 5000:
        return "공격투자형 투자자 적합 (고변동성 소형주)"
    else:
        return "투기형 투자자 적합 (저가주)"


def _get_split_buy_strategy(current_price: float) -> str:
    """분할 매수 전략"""
    first_buy = current_price
    second_buy = int(current_price * 0.98)
    third_buy = int(current_price * 0.95)

    return f"""
- **1차**: 현재가 {first_buy:,}원에서 40%
- **2차**: {second_buy:,}원(-2%)에서 40%
- **3차**: {third_buy:,}원(-5%)에서 20%"""


def _get_target_price_strategy(current_price: float, signal_strength: float) -> str:
    """목표가 설정 전략"""
    if signal_strength >= 0.9:
        target1 = int(current_price * 1.08)
        target2 = int(current_price * 1.15)
        target3 = int(current_price * 1.25)
    elif signal_strength >= 0.7:
        target1 = int(current_price * 1.06)
        target2 = int(current_price * 1.12)
        target3 = int(current_price * 1.20)
    else:
        target1 = int(current_price * 1.05)
        target2 = int(current_price * 1.10)
        target3 = int(current_price * 1.15)

    return f"""
- **1차 목표**: {target1:,}원 (50% 매도)
- **2차 목표**: {target2:,}원 (30% 매도)
- **3차 목표**: {target3:,}원 (20% 매도)"""


def _get_time_based_trading_strategy(current_hour: int) -> str:
    """시간대별 매매 전략"""
    if 9 <= current_hour < 10:
        return """
- **즉시 매수**: 갭 하락 시 적극적 매수
- **관망**: 갭 상승 시 10분 후 재평가
- **분할 매수**: 일반적인 경우 1차 매수 실행"""
    elif 10 <= current_hour < 12:
        return """
- **적극 매수**: 거래량 증가와 함께 매수
- **기관 동향**: 외국인/기관 매매 동향 확인 후 매수
- **추세 확인**: 오전 추세 방향 확인 후 진입"""
    elif 13 <= current_hour < 15:
        return """
- **반등 매수**: 오전 하락 후 오후 반등 시 진입
- **마감 매수**: 강한 신호 시 마감 1시간 전 진입
- **내일 준비**: 신호 약화 시 내일 재분석 대기"""
    else:
        return """
- **장후 분석**: 오늘 장 마감 후 내일 전략 수립
- **해외 동향**: 미국/중국 시장 동향 모니터링
- **뉴스 점검**: 관련 종목 뉴스 및 공시 확인"""