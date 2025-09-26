"""
Technical analysis focused prompt template.
"""
from typing import List, Dict, Any, Optional
from .base_prompt import BasePrompt
from schemas import AnalyzedStockData


class TechnicalAnalysisPrompt(BasePrompt):
    """Prompt template for detailed technical analysis."""
    
    def __init__(self):
        super().__init__()
        self.description = "Detailed technical analysis of selected stocks"
        self.max_tokens = 3000
        self.temperature = 0.2
    
    def generate_prompt(self, stocks_data: List[AnalyzedStockData], 
                       context: Optional[Dict[str, Any]] = None) -> str:
        """Generate technical analysis prompt."""
        
        if not stocks_data:
            return "분석할 주식 데이터가 제공되지 않았습니다."
        
        # Header
        prompt = f"""다음 {len(stocks_data)}개 종목에 대한 상세한 기술적 분석을 수행해주세요.

**분석 요청사항:**
1. 각 종목의 현재 기술적 상태 평가
2. 주요 기술적 지표들의 시그널 해석
3. 지지선과 저항선 분석
4. 단기/중기 추세 방향 예측
5. 매매 타이밍 및 목표가/손절가 제시

**제공된 주식 데이터:**
"""
        
        # Add stock data
        for i, stock_data in enumerate(stocks_data, 1):
            prompt += f"\n{i}. {self.format_stock_data(stock_data)}\n"
        
        # Analysis framework
        prompt += """

**분석 지침:**

각 종목에 대해 다음 형식으로 분석해주세요:

### [종목코드] 기술적 분석

**1. 현재 상태 요약**
- 전반적인 기술적 상태 (강세/약세/중립)
- 주요 특징점

**2. 기술적 지표 분석**
- RSI: 과매수/과매도 상태 및 의미
- MACD: 추세 전환 신호 여부
- 이동평균선: 정배열/역배열 상태
- 볼린저 밴드: 현재 위치 및 의미

**3. 차트 패턴 및 추세**
- 단기 추세 (3-5일)
- 중기 추세 (2-4주)
- 주요 차트 패턴 (존재하는 경우)

**4. 지지/저항 수준**
- 주요 지지선 가격대
- 주요 저항선 가격대
- 돌파 시 목표가

**5. 매매 전략**
- 추천 포지션 (매수/매도/관망)
- 진입 가격대
- 목표 수익가
- 손절 가격
- 주의사항

**전체 시장 관점에서의 종합 의견도 마지막에 포함해주세요.**
"""
        
        # Add context if provided
        if context:
            if "strategy_used" in context:
                prompt += f"\n\n**참고:** 이 종목들은 '{context['strategy_used']}' 전략으로 선별되었습니다."
            
            if "market_condition" in context:
                prompt += f"\n현재 시장 상황: {context['market_condition']}"
        
        return prompt