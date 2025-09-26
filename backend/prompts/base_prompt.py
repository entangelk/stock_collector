"""
Base prompt management for AI analysis.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date
import logging

from schemas import AnalyzedStockData

logger = logging.getLogger(__name__)


class BasePrompt(ABC):
    """Base class for AI analysis prompts."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = ""
        self.max_tokens = 2000
        self.temperature = 0.3
    
    @abstractmethod
    def generate_prompt(self, stocks_data: List[AnalyzedStockData], 
                       context: Optional[Dict[str, Any]] = None) -> str:
        """Generate the prompt string for AI analysis."""
        pass
    
    def get_system_message(self) -> str:
        """Get the system message for the AI model."""
        return """You are a professional Korean stock market analyst with deep expertise in technical analysis and fundamental analysis. 
        
Your role is to:
1. Analyze the provided stock data objectively
2. Identify key technical patterns and indicators
3. Assess market sentiment and trends
4. Provide clear, actionable insights
5. Consider Korean market characteristics and trading patterns

Guidelines:
- Be objective and data-driven in your analysis
- Explain your reasoning clearly
- Mention specific technical indicators and their values
- Consider both opportunities and risks
- Use professional financial terminology
- Provide specific price levels when relevant
- Consider market context and sector trends

Remember: This is for informational purposes only and should not be considered as investment advice."""
    
    def format_stock_data(self, stock_data: AnalyzedStockData) -> str:
        """Format stock data for prompt inclusion."""
        indicators = stock_data.technical_indicators
        ohlcv = stock_data.ohlcv
        
        data_str = f"""
**{stock_data.ticker}**
- 현재가: {ohlcv.close:,.0f}원
- 거래량: {ohlcv.volume:,}주
- 기술적 지표:
  - RSI(14): {indicators.rsi_14:.1f}
  - MACD: {indicators.macd:.2f}
  - MACD Signal: {indicators.macd_signal:.2f}
  - MACD Histogram: {indicators.macd_histogram:.2f}
  - SMA(20): {indicators.sma_20:,.0f}원
  - SMA(60): {indicators.sma_60:,.0f}원
  - 볼린저 밴드 상단: {indicators.bollinger_upper:,.0f}원
  - 볼린저 밴드 하단: {indicators.bollinger_lower:,.0f}원
"""
        return data_str.strip()
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get prompt configuration for AI model."""
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system_message": self.get_system_message()
        }


class PromptManager:
    """Manager for AI analysis prompts."""
    
    def __init__(self):
        self.prompts: Dict[str, BasePrompt] = {}
        self._register_default_prompts()
    
    def register_prompt(self, prompt: BasePrompt) -> None:
        """Register a new prompt template."""
        self.prompts[prompt.name.lower()] = prompt
        logger.info(f"Registered prompt: {prompt.name}")
    
    def get_prompt(self, prompt_name: str) -> Optional[BasePrompt]:
        """Get prompt template by name."""
        return self.prompts.get(prompt_name.lower())
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompt templates."""
        return [
            {
                "name": name,
                "description": prompt.description,
                "max_tokens": prompt.max_tokens,
                "temperature": prompt.temperature
            }
            for name, prompt in self.prompts.items()
        ]
    
    def generate_analysis_prompt(self, prompt_name: str, 
                                stocks_data: List[AnalyzedStockData],
                                context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Generate complete prompt for AI analysis."""
        prompt_template = self.get_prompt(prompt_name)
        if not prompt_template:
            return None
        
        try:
            prompt_text = prompt_template.generate_prompt(stocks_data, context)
            
            return {
                "prompt": prompt_text,
                "system_message": prompt_template.get_system_message(),
                "configuration": prompt_template.get_configuration(),
                "prompt_name": prompt_name
            }
            
        except Exception as e:
            logger.error(f"Failed to generate prompt {prompt_name}: {e}")
            return None
    
    def _register_default_prompts(self) -> None:
        """Register default prompt templates."""
        from .technical_analysis_prompt import TechnicalAnalysisPrompt
        from .market_overview_prompt import MarketOverviewPrompt
        from .trading_opportunity_prompt import TradingOpportunityPrompt
        from .risk_assessment_prompt import RiskAssessmentPrompt
        
        self.register_prompt(TechnicalAnalysisPrompt())
        self.register_prompt(MarketOverviewPrompt())
        self.register_prompt(TradingOpportunityPrompt())
        self.register_prompt(RiskAssessmentPrompt())


# Global prompt manager instance
prompt_manager = PromptManager()