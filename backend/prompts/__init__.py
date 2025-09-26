"""
AI analysis prompts package.
"""
from .base_prompt import BasePrompt, PromptManager, prompt_manager
from .technical_analysis_prompt import TechnicalAnalysisPrompt
from .market_overview_prompt import MarketOverviewPrompt
from .trading_opportunity_prompt import TradingOpportunityPrompt
from .risk_assessment_prompt import RiskAssessmentPrompt

__all__ = [
    "BasePrompt",
    "PromptManager",
    "prompt_manager",
    "TechnicalAnalysisPrompt",
    "MarketOverviewPrompt", 
    "TradingOpportunityPrompt",
    "RiskAssessmentPrompt"
]