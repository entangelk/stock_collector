"""
Trading strategies package for stock screening.
"""
from .base_strategy import BaseStrategy, StrategyManager, strategy_manager
from .macd_golden_cross import MACDGoldenCrossStrategy
from .rsi_oversold import RSIOversoldStrategy
from .bollinger_squeeze import BollingerSqueezeStrategy
from .moving_average_crossover import MovingAverageCrossoverStrategy

__all__ = [
    "BaseStrategy",
    "StrategyManager", 
    "strategy_manager",
    "MACDGoldenCrossStrategy",
    "RSIOversoldStrategy",
    "BollingerSqueezeStrategy",
    "MovingAverageCrossoverStrategy"
]