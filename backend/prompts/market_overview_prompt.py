"""
Market overview and sector analysis prompt template.
"""
from typing import List, Dict, Any, Optional
from .base_prompt import BasePrompt
from schemas import AnalyzedStockData


class MarketOverviewPrompt(BasePrompt):
    """Prompt template for market overview and sector analysis."""
    
    def __init__(self):
        super().__init__()
        self.description = "Market overview and sector trend analysis"
        self.max_tokens = 2500
        self.temperature = 0.3
    
    def generate_prompt(self, stocks_data: List[AnalyzedStockData], 
                       context: Optional[Dict[str, Any]] = None) -> str:
        """Generate market overview prompt."""
        
        if not stocks_data:
            return "분석할 주식 데이터가 제공되지 않았습니다."
        
        # Header
        prompt = f"""다음 {len(stocks_data)}개 대형주 종목들의 데이터를 바탕으로 한국 주식시장의 현재 상황과 섹터별 동향을 분석해주세요.

**제공된 주식 데이터:**
"""
        
        # Add stock data in summary format
        for i, stock_data in enumerate(stocks_data, 1):
            indicators = stock_data.technical_indicators
            ohlcv = stock_data.ohlcv
            
            prompt += f"""
{i}. **{stock_data.ticker}** - 현재가: {ohlcv.close:,.0f}원
   - RSI: {indicators.rsi_14:.1f}, MACD: {indicators.macd:.2f}
   - SMA20 대비: {((ohlcv.close/indicators.sma_20-1)*100):+.1f}%
   - 거래량: {ohlcv.volume:,}주
"""
        
        # Analysis framework
        prompt += """

**분석 요청사항:**

### 1. 전체 시장 현황 분석
- 제공된 대형주들의 전반적인 기술적 상태를 통해 본 시장 분위기
- 강세/약세/횡보 중 어느 구간에 있는지 판단
- 시장 참여자들의 심리 상태 (공포/탐욕 지수 관점에서)

### 2. 기술적 지표 종합 분석
- RSI 평균값과 분포를 통한 시장 과열/침체 판단
- MACD 신호들의 종합적 해석
- 이동평균선 배열 상태의 시장 의미

### 3. 섹터별 강도 분석
- 각 종목이 속한 섹터의 상대적 강도
- 리더십 섹터 식별
- 아웃퍼폼/언더퍼폼 섹터 구분

### 4. 시장 리스크 요소
- 현재 기술적 지표들이 시사하는 위험 신호
- 주의해야 할 저항선/지지선 수준
- 변동성 수준 평가

### 5. 향후 시장 전망
- 단기 (1-2주) 시장 방향성 예측
- 중기 (1-2개월) 추세 전망
- 투자자들이 주목해야 할 핵심 포인트

### 6. 투자 전략 제언
- 현재 시장 상황에 적합한 투자 접근법
- 포트폴리오 배분 방향성
- 리스크 관리 방안

**각 섹션별로 구체적인 데이터와 수치를 인용하여 근거 있는 분석을 제공해주세요.**
"""
        
        # Add context if provided
        if context:
            if "market_index_data" in context:
                prompt += f"\n\n**참고 지수 정보:** {context['market_index_data']}"
            
            if "global_market_context" in context:
                prompt += f"\n**글로벌 시장 상황:** {context['global_market_context']}"
        
        return prompt