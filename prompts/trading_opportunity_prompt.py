"""
Trading opportunity identification prompt template.
"""
from typing import List, Dict, Any, Optional
from .base_prompt import BasePrompt
from schemas import AnalyzedStockData


class TradingOpportunityPrompt(BasePrompt):
    """Prompt template for identifying specific trading opportunities."""
    
    def __init__(self):
        super().__init__()
        self.description = "Identification of specific trading opportunities with entry/exit strategies"
        self.max_tokens = 3500
        self.temperature = 0.25
    
    def generate_prompt(self, stocks_data: List[AnalyzedStockData], 
                       context: Optional[Dict[str, Any]] = None) -> str:
        """Generate trading opportunity identification prompt."""
        
        if not stocks_data:
            return "분석할 주식 데이터가 제공되지 않았습니다."
        
        # Header
        prompt = f"""다음 {len(stocks_data)}개 종목에서 구체적인 매매 기회를 식별하고 실전 트레이딩 전략을 수립해주세요.

**제공된 종목 데이터:**
"""
        
        # Add detailed stock data
        for i, stock_data in enumerate(stocks_data, 1):
            prompt += f"\n{i}. {self.format_stock_data(stock_data)}\n"
        
        # Analysis framework
        prompt += """

**트레이딩 기회 분석 요청:**

각 종목에 대해 다음 형식으로 매매 전략을 수립해주세요:

### [종목코드] 트레이딩 전략

**1. 기회 등급 평가**
- 매매 기회 점수: ★☆☆☆☆ (5점 만점)
- 기회 유형: (단기 스윙, 중기 추세, 단기 리바운드 등)
- 신뢰도: (높음/보통/낮음)

**2. 현재 상황 진단**
- 기술적 신호 요약
- 모멘텀 상태 (강함/약함/중립)
- 주요 패턴 식별

**3. 구체적 매매 전략**

**[매수 전략]** (해당하는 경우)
- 진입 신호: (구체적 조건)
- 매수가격대: X,XXX원 ~ X,XXX원
- 분할매수 방식: (1회/2-3회 분할 등)
- 매수 근거: (기술적 근거 3가지)

**[매도 전략]** (해당하는 경우)  
- 매도 신호: (구체적 조건)
- 매도가격대: X,XXX원 ~ X,XXX원
- 분할매도 방식
- 매도 근거: (기술적 근거)

**4. 리스크 관리**
- 손절가: X,XXX원 (-X.X%)
- 손절 이유: (지지선 이탈 등)
- 포지션 크기: 포트폴리오의 X%
- 최대 허용 손실: -X%

**5. 수익 목표**
- 1차 목표가: X,XXX원 (+X.X%)
- 2차 목표가: X,XXX원 (+X.X%)
- 최종 목표가: X,XXX원 (+X.X%)
- 각 목표가 도달 근거

**6. 모니터링 포인트**
- 관찰할 기술적 지표
- 중요 뉴스/이벤트 일정
- 섹터/시장 변화 요인

**7. 대안 시나리오**
- 예상과 다른 움직임 시 대응책
- 시장 급변 시 전략 수정 방안

### 전체 포트폴리오 관점

**1. 종목간 상관관계**
- 동조화 위험성 평가
- 분산투자 효과

**2. 시장 타이밍**
- 현재 시장 상황의 매매 적합성
- 전체적인 리스크 수준

**3. 우선순위 랭킹**
1위: [종목] - 이유
2위: [종목] - 이유
3위: [종목] - 이유

**실전 트레이딩을 위한 구체적이고 실행 가능한 전략을 제시해주세요.**
"""
        
        # Add context if provided
        if context:
            if "risk_level" in context:
                prompt += f"\n\n**투자 위험성향:** {context['risk_level']}"
            
            if "time_horizon" in context:
                prompt += f"\n**투자 기간:** {context['time_horizon']}"
            
            if "portfolio_size" in context:
                prompt += f"\n**포트폴리오 규모:** {context['portfolio_size']}"
                
            if "strategy_used" in context:
                prompt += f"\n**선별 전략:** 이 종목들은 '{context['strategy_used']}' 전략으로 선별되었습니다."
        
        return prompt