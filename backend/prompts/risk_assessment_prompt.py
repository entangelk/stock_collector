"""
Risk assessment and portfolio management prompt template.
"""
from typing import List, Dict, Any, Optional
from .base_prompt import BasePrompt
from schemas import AnalyzedStockData


class RiskAssessmentPrompt(BasePrompt):
    """Prompt template for risk assessment and portfolio management."""
    
    def __init__(self):
        super().__init__()
        self.description = "Comprehensive risk assessment and portfolio risk management analysis"
        self.max_tokens = 2800
        self.temperature = 0.2
    
    def generate_prompt(self, stocks_data: List[AnalyzedStockData], 
                       context: Optional[Dict[str, Any]] = None) -> str:
        """Generate risk assessment prompt."""
        
        if not stocks_data:
            return "분석할 주식 데이터가 제공되지 않았습니다."
        
        # Header
        prompt = f"""다음 {len(stocks_data)}개 종목에 대한 종합적인 리스크 분석을 수행하고 포트폴리오 리스크 관리 방안을 제시해주세요.

**분석 대상 종목:**
"""
        
        # Add stock data with risk focus
        for i, stock_data in enumerate(stocks_data, 1):
            indicators = stock_data.technical_indicators
            ohlcv = stock_data.ohlcv
            
            # Calculate some basic risk metrics
            volatility_signal = ""
            if indicators.bollinger_upper and indicators.bollinger_lower:
                band_width = (indicators.bollinger_upper - indicators.bollinger_lower) / indicators.bollinger_middle * 100
                volatility_signal = f", 변동성: {band_width:.1f}%"
            
            prompt += f"""
{i}. **{stock_data.ticker}**
   - 현재가: {ohlcv.close:,.0f}원
   - RSI: {indicators.rsi_14:.1f} {'(과매수)' if indicators.rsi_14 > 70 else '(과매도)' if indicators.rsi_14 < 30 else '(중립)'}
   - MACD: {indicators.macd:.2f} {'(상승)' if indicators.macd > indicators.macd_signal else '(하락)'}
   - SMA20 대비: {((ohlcv.close/indicators.sma_20-1)*100):+.1f}%{volatility_signal}
"""
        
        # Analysis framework
        prompt += """

**리스크 분석 프레임워크:**

### 1. 개별 종목 리스크 분석

각 종목에 대해:

**[종목코드] 리스크 프로필**
- **리스크 등급:** 높음/보통/낮음
- **주요 위험요소:**
  - 기술적 위험: (차트상 위험 신호)
  - 변동성 위험: (가격 변동폭 분석)
  - 유동성 위험: (거래량 분석)
  - 추세 전환 위험: (지지선/저항선)

- **손실 시나리오 분석:**
  - 1주일 내 최대 예상 하락률: -X%
  - 1개월 내 최대 예상 하락률: -X%
  - 최악의 시나리오: -X% (조건)

- **리스크 관리 방안:**
  - 적정 포지션 크기: 포트폴리오의 X%
  - 손절선: X,XXX원 (-X%)
  - 모니터링 지표: (핵심 관찰 포인트)

### 2. 포트폴리오 레벨 리스크 분석

**전체 포트폴리오 리스크 매트릭스:**
- **분산 효과:** 종목간 상관관계 분석
- **집중 리스크:** 특정 섹터/테마 집중도
- **시스템 리스크:** 시장 전체 하락 시 영향도
- **유동성 리스크:** 동시 매도 시 영향

**포트폴리오 통계:**
- 예상 최대 손실(VaR): 1일/1주/1개월
- 샤프 비율 예측
- 최대 낙폭(Maximum Drawdown) 시나리오

### 3. 시장 리스크 요소

**거시경제 리스크:**
- 금리 변동 영향도
- 환율 변동 영향도  
- 글로벌 시장 연동성

**기술적 리스크:**
- 주요 지수 지지선 이탈 가능성
- 섹터 로테이션 리스크
- 변동성 급증 가능성

### 4. 리스크 관리 전략

**포지션 사이징:**
- 종목별 가중치 제안
- 리스크 기여도 기준 배분
- 최적 포트폴리오 구성

**헷지 전략:**
- 방어적 종목 포함 검토
- 현금 비중 제안
- 대체 투자 고려사항

**모니터링 체계:**
- 일일 체크리스트
- 주간 리밸런싱 기준
- 경고 신호 및 대응 방안

### 5. 시나리오별 대응 전략

**시장 급락 시(-10% 이상):**
- 손절 실행 순서
- 추가 매수 기회 평가
- 포트폴리오 재구성 방안

**횡보장 지속 시:**
- 수익 실현 타이밍
- 종목 교체 전략
- 대기 자금 운용

**급등장 진입 시:**
- 이익 실현 단계별 전략
- 위험자산 비중 조절
- 버블 경계 신호

### 6. 종합 권고사항

**위험도별 투자자 유형:**
- 보수적 투자자: (구체적 제안)
- 중도적 투자자: (구체적 제안)  
- 공격적 투자자: (구체적 제안)

**현재 시장 환경에서의 핵심 메시지와 행동 지침을 제시해주세요.**
"""
        
        # Add context if provided
        if context:
            if "portfolio_value" in context:
                prompt += f"\n\n**포트폴리오 규모:** {context['portfolio_value']}"
            
            if "risk_tolerance" in context:
                prompt += f"\n**위험허용도:** {context['risk_tolerance']}"
            
            if "investment_horizon" in context:
                prompt += f"\n**투자기간:** {context['investment_horizon']}"
        
        return prompt