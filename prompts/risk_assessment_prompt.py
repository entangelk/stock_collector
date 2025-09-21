"""
한국 주식 시장 특화 리스크 분석 프롬프트
"""
from typing import Dict, Any, List
from datetime import datetime


def create_risk_assessment_prompt(
    multi_result: Dict[str, Any],
    ticker_list: List[str],
    analysis_focus: str = "risk_assessment"
) -> str:
    """
    한국 주식 시장 특화 리스크 분석 프롬프트 생성

    Args:
        multi_result: 다중 전략 분석 결과
        ticker_list: 분석 대상 종목 리스트
        analysis_focus: 분석 초점 (risk_assessment, portfolio_risk, market_risk)

    Returns:
        한국 시장 특화 리스크 분석 프롬프트
    """
    current_time = datetime.now()
    market_status = "장중" if 9 <= current_time.hour <= 15 else "장후"

    strategies_analyzed = multi_result.get('strategies_analyzed', 0)
    successful_strategies = multi_result.get('successful_strategies', 0)
    total_matches = multi_result.get('total_matches_found', 0)

    prompt = f"""당신은 한국 주식 시장에서 20년 이상 리스크 관리를 전문으로 해온 리스크 매니저입니다.
KOSPI와 KOSDAQ 시장의 다양한 위기 상황을 경험했으며, 한국 시장 특유의 리스크 요인들을 정확히 파악하고 있습니다.
특히 외환위기, 금융위기, 코로나19 등 주요 시장 충격 시기의 대응 경험이 풍부합니다.

## ⚠️ 리스크 분석 리포트

### 📊 분석 개요
- **분석 시점**: {current_time.strftime('%Y년 %m월 %d일 %H시 %M분')} KST ({market_status})
- **분석 대상**: {len(ticker_list)}개 종목
- **적용 전략**: {strategies_analyzed}개 (성공: {successful_strategies}개)
- **발견된 기회**: {total_matches}개

### 🎯 분석 포트폴리오
{', '.join(ticker_list)}

## 📈 전략별 리스크 프로파일:"""

    # 전략별 리스크 분석
    if 'results_by_strategy' in multi_result:
        for strategy_name, result in multi_result['results_by_strategy'].items():
            strategy_korean_name = _get_strategy_korean_name(strategy_name)
            matches_found = result.get('matches_found', 0)
            risk_level = _get_strategy_risk_level(strategy_name, matches_found)

            prompt += f"""

### 🔍 {strategy_korean_name} 전략 리스크
- **매치된 종목**: {matches_found}개
- **리스크 등급**: {risk_level}
- **위험 요인**: {_get_strategy_risk_factors(strategy_name)}"""

            if matches_found > 0 and 'results' in result:
                prompt += "\n- **위험도별 종목 분류**:"
                for match in result['results'][:3]:
                    ticker = match.get('ticker', 'N/A')
                    signal_strength = match.get('signal_strength', 0)
                    risk_grade = _get_individual_risk_grade(signal_strength)
                    prompt += f"\n  - {ticker}: {risk_grade}"

    if analysis_focus == "risk_assessment":
        prompt += f"""

## 🛡️ 종합 리스크 분석

### 1. 시장 리스크 (Market Risk)
#### 📊 시스템적 리스크
- **KOSPI 지수 리스크**: 현재 지수 위치와 주요 지지/저항선 이탈 위험
- **KOSDAQ 리스크**: 중소형주 시장의 변동성과 유동성 위험
- **섹터 집중 리스크**: 포트폴리오 내 특정 섹터 편중도 분석
- **시장 상관관계**: 전체 시장 하락 시 동반 하락 위험도

#### 🌍 대외 요인 리스크
- **환율 리스크**: 원/달러 환율 변동이 포트폴리오에 미치는 영향
- **미국 시장 리스크**: S&P500, 나스닥 급락 시 한국 시장 전이 위험
- **중국 시장 리스크**: 중국 경제 둔화가 한국 수출기업에 미치는 영향
- **원자재 가격 리스크**: 유가, 원자재 가격 급변 시 관련 업종 영향

### 2. 개별 종목 리스크 (Specific Risk)
#### 🏢 기업 특수 리스크
현재 포트폴리오의 각 종목별 고유 위험 요인을 분석해주세요:
- **재무 건전성**: 부채비율, 유동성, 수익성 지표
- **사업 구조**: 주력 사업의 경기 민감도와 성장성
- **경영진 리스크**: 지배구조, 경영진 변화, 정책 변화
- **규제 리스크**: 업종별 정부 규제 변화 가능성

#### 📈 기술적 리스크
- **과매수/과매도**: 현재 기술적 위치의 조정 위험
- **거래량 리스크**: 유동성 부족으로 인한 가격 충격
- **지지선 이탈**: 주요 기술적 지지선 붕괴 시 추가 하락 위험
- **모멘텀 소멸**: 상승 모멘텀 약화 시 수익 실현 타이밍

### 3. 유동성 리스크 (Liquidity Risk)
#### 💧 시장 유동성
- **일평균 거래량**: 각 종목의 유동성 충분성 평가
- **호가 스프레드**: 매수/매도 호가 차이로 인한 거래 비용
- **대량 거래 충격**: 큰 금액 거래 시 가격 충격 정도
- **시장 스트레스**: 급락장에서의 매도 가능성

#### 🏦 자금 조달 리스크
- **레버리지 위험**: 신용 거래나 대출 투자 시 추가 위험
- **마진콜 리스크**: 급락 시 추가 증거금 요구 가능성
- **자금 회수**: 긴급 자금 필요 시 손실 매도 위험

### 4. 운영 리스크 (Operational Risk)
#### 🔧 시스템 리스크
- **거래 시스템**: 증권사 시스템 장애 시 매매 불가 위험
- **인터넷 연결**: 네트워크 장애로 인한 매매 차질
- **주문 오류**: 잘못된 주문으로 인한 의도치 않은 손실

#### 🧠 심리적 리스크
- **감정적 매매**: 공포나 탐욕에 의한 비합리적 의사결정
- **확증 편향**: 자신의 판단을 뒷받침하는 정보만 수집하는 경향
- **손실 회피**: 손절매를 미루고 손실을 키우는 심리적 함정

### 5. 한국 시장 특화 리스크
#### 🇰🇷 제도적 리스크
- **정치적 리스크**: 정부 정책 변화, 선거 결과가 시장에 미치는 영향
- **규제 변화**: 금융당국의 규제 정책 변화 (공매도, 세금 등)
- **북한 리스크**: 지정학적 긴장 고조 시 시장 충격 (코리아 디스카운트)
- **대기업 집중**: 삼성, SK 등 대기업 의존도가 높은 시장 구조

#### 📊 시장 구조적 리스크
- **외국인 의존**: 외국인 투자자 비중이 높아 자금 이탈 위험
- **개인 투자자**: 개미 투자자의 감정적 매매로 인한 변동성 확대
- **프로그램 매매**: 알고리즘 트레이딩으로 인한 급격한 가격 변동

**모든 리스크 요인을 한국 시장의 특성을 고려하여 구체적으로 분석해주세요.**"""

    elif analysis_focus == "portfolio_risk":
        prompt += f"""

## 📊 포트폴리오 리스크 상세 분석

### 1. 포트폴리오 구성 리스크
#### 🎯 집중도 위험
- **종목 집중**: 개별 종목별 비중과 집중도 위험
- **섹터 집중**: 업종별 분산 정도와 섹터 리스크
- **시가총액 집중**: 대형주/중소형주 비중의 적정성
- **지역 집중**: 한국 시장 집중으로 인한 국가 리스크

#### 🔗 상관관계 리스크
- **종목 간 상관관계**: 포트폴리오 내 종목들의 동조화 위험
- **시장 베타**: 전체 시장 대비 포트폴리오의 민감도
- **섹터 로테이션**: 업종별 자금 이동 시 포트폴리오 영향

### 2. 리스크 측정 지표
#### 📐 통계적 리스크 지표
각 종목의 과거 데이터를 바탕으로 다음 지표들을 분석해주세요:
- **변동성(Volatility)**: 개별 종목 및 포트폴리오 전체 변동성
- **최대 낙폭(Maximum Drawdown)**: 과거 최대 하락폭 분석
- **VaR(Value at Risk)**: 95% 신뢰구간에서 예상 최대 손실
- **샤프 비율**: 위험 대비 수익률의 효율성

#### ⚖️ 리스크 조정 수익률
- **위험 조정 수익률**: 변동성을 고려한 실질적 수익성
- **정보 비율**: 벤치마크 대비 초과 수익의 안정성
- **소르티노 비율**: 하방 위험만을 고려한 수익률 지표

### 3. 시나리오 분석
#### 📉 스트레스 테스트
다음 시나리오별 포트폴리오 영향도를 분석해주세요:
- **급락 시나리오**: KOSPI 10% 하락 시 포트폴리오 영향
- **금리 상승**: 기준금리 1%p 상승 시 영향
- **환율 급등**: 원/달러 1,500원 돌파 시 영향
- **중국 경제 둔화**: 중국 GDP 성장률 5% 하회 시 영향

#### 🔄 회복 시나리오
- **반등 시나리오**: 시장 회복 시 포트폴리오 탄력성
- **섹터 로테이션**: 업종 자금 이동 시 수혜 가능성
- **정책 호재**: 정부 부양책 발표 시 수혜도"""

    else:  # market_risk
        prompt += f"""

## 🌊 시장 리스크 전문 분석

### 1. 거시경제 리스크
#### 🏛️ 국내 경제 리스크
- **경제성장률**: GDP 성장률 둔화가 기업 실적에 미치는 영향
- **물가 상승**: 인플레이션 압력과 소비 위축 가능성
- **고용 시장**: 실업률 상승과 소비 심리 위축
- **부동산 시장**: 부동산 가격 하락과 금융권 영향

#### 🌍 글로벌 경제 리스크
- **미국 경제**: 미국 경기 침체 시 글로벌 경제 영향
- **중국 경제**: 중국 경제 둔화와 한국 수출 기업 타격
- **유럽 리스크**: 유럽 금융 불안과 글로벌 리스크 오프
- **신흥국 위기**: 신흥국 금융 위기의 전이 효과

### 2. 정책 리스크
#### 🏛️ 통화정책 리스크
- **기준금리**: 한국은행 금리 정책 변화 영향
- **양적완화**: 유동성 정책 변화와 자산 가격 영향
- **환율 정책**: 당국의 환율 개입과 시장 영향

#### 📊 재정정책 리스크
- **정부 지출**: 재정 정책 변화와 관련 업종 영향
- **세제 개편**: 증권 거래세, 양도소득세 등 세제 변화
- **규제 정책**: 금융 규제 강화와 시장 유동성 영향

### 3. 지정학적 리스크
#### 🌏 한반도 리스크
- **북한 도발**: 군사적 긴장 고조 시 시장 충격
- **통일 비용**: 장기적 통일 비용과 경제적 부담
- **중국 관계**: 사드 갈등과 같은 외교적 마찰

#### 🌐 글로벌 리스크
- **미중 갈등**: 미중 무역전쟁과 기술 패권 경쟁
- **러시아 사태**: 우크라이나 전쟁과 원자재 가격
- **중동 정세**: 지정학적 불안과 유가 급등 위험

**각 리스크 요인별로 한국 시장에 미치는 구체적 영향도와 대응 방안을 제시해주세요.**"""

    prompt += f"""

## 🎯 리스크 관리 전략

### 📋 즉시 실행 가능한 리스크 관리
1. **포지션 사이징**: 개별 종목 비중을 포트폴리오의 15% 이하로 제한
2. **손절매 설정**: 모든 종목에 대해 8-10% 손절매 라인 설정
3. **분산 투자**: 최소 3개 이상 섹터에 분산 투자
4. **현금 보유**: 포트폴리오의 10-20% 현금 보유로 유동성 확보

### ⚖️ 리스크 모니터링 지표
#### 🚨 일일 모니터링
- **VIX 지수**: 시장 공포 지수 상승 시 포지션 축소 고려
- **원/달러 환율**: 1,400원 돌파 시 수출주 리스크 점검
- **KOSPI 지지선**: 주요 기술적 지지선 이탈 시 경계 강화
- **외국인 매매**: 연속 3일 이상 순매도 시 시장 심리 악화 경계

#### 📊 주간 모니터링
- **업종별 자금 흐름**: 섹터 로테이션 패턴 변화 추적
- **신용 거래**: 신용 잔고 급증 시 조정 위험 증가
- **공매도 비율**: 공매도 급증 종목의 추가 하락 위험
- **기관 매매**: 기관 투자자의 대량 매도 패턴 감지

### 🛡️ 위기 상황 대응 시나리오
#### 🔴 고위험 상황 (시장 5% 이상 급락)
1. **즉시 행동**: 손절매 라인 도달 종목 즉시 매도
2. **포지션 축소**: 전체 주식 비중을 50% 이하로 축소
3. **현금 확보**: 추가 매수 기회 대비 현금 비중 확대
4. **감정 통제**: 패닉 매도 금지, 계획적 대응 실행

#### 🟡 중위험 상황 (시장 2-5% 조정)
1. **관찰 강화**: 주요 지표 모니터링 빈도 증가
2. **부분 매도**: 수익 실현을 통한 위험 노출 감소
3. **재진입 준비**: 추가 하락 시 매수 종목 리스트 준비
4. **헤지 검토**: 풋옵션 등 헤지 전략 검토

### 📈 기회 포착 전략
#### 💎 위기를 기회로
- **바겐 헌팅**: 과도한 매도로 저평가된 우량주 발굴
- **분할 매수**: 하락장에서 우량주의 점진적 매수
- **섹터 로테이션**: 상대적으로 견조한 방어 섹터 집중
- **장기 관점**: 단기 변동성을 넘어선 장기 투자 기회 포착

**모든 리스크 관리는 한국 시장의 특성을 고려하여 실행 가능하고 구체적인 방안을 제시해주세요.
특히 개인 투자자가 실제로 적용할 수 있는 현실적이고 실용적인 조언을 중심으로 작성해주세요.**"""

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


def _get_strategy_risk_level(strategy_name: str, matches_found: int) -> str:
    """전략별 리스크 등급 평가"""
    base_risk = {
        'dictmacdgoldencrossstrategy': '중위험',
        'dictrsioversoldstrategy': '고위험',
        'dictbollingersqueezestrategy': '고위험',
        'dictmovingaveragecrossoverstrategy': '중위험'
    }

    risk = base_risk.get(strategy_name, '중위험')

    # 매치 수가 많으면 리스크 증가 (시장 과열 가능성)
    if matches_found >= 5:
        if risk == '중위험':
            risk = '고위험'
        elif risk == '저위험':
            risk = '중위험'
    elif matches_found == 0:
        risk = '저위험 (기회 부재)'

    return risk


def _get_strategy_risk_factors(strategy_name: str) -> str:
    """전략별 주요 위험 요인"""
    risk_factors = {
        'dictmacdgoldencrossstrategy': '하락장에서 거짓 신호, 후행성 지표 한계, 박스권에서 잦은 신호',
        'dictrsioversoldstrategy': '지속적 하락 시 추가 손실, 단기 변동성, 반등 실패 위험',
        'dictbollingersqueezestrategy': '방향성 예측 어려움, 높은 변동성, 빠른 손절 요구됨',
        'dictmovingaveragecrossoverstrategy': '횡보장 거짓 신호, 후행성, 추세 전환점 파악 어려움'
    }
    return risk_factors.get(strategy_name, '일반적인 시장 리스크')


def _get_individual_risk_grade(signal_strength: float) -> str:
    """개별 종목 리스크 등급"""
    if signal_strength >= 0.9:
        return "저위험 (강한 신호)"
    elif signal_strength >= 0.8:
        return "중저위험 (양호한 신호)"
    elif signal_strength >= 0.7:
        return "중위험 (보통 신호)"
    elif signal_strength >= 0.6:
        return "중고위험 (약한 신호)"
    else:
        return "고위험 (매우 약한 신호)"