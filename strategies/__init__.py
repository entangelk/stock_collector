"""
Trading strategies package for stock screening.
"""
# 딕셔너리 기반 전략 시스템 (Pydantic 우회)
from .dict_base_strategy import DictBaseStrategy, DictStrategyManager, dict_strategy_manager
from .dict_macd_golden_cross import DictMACDGoldenCrossStrategy
from .dict_rsi_oversold import DictRSIOversoldStrategy
from .dict_bollinger_squeeze import DictBollingerSqueezeStrategy
from .dict_moving_average_crossover import DictMovingAverageCrossoverStrategy

# 기존 Pydantic 기반 전략들 (호환성 문제로 주석 처리)
# from .base_strategy import BaseStrategy, StrategyManager, strategy_manager
# from .macd_golden_cross import MACDGoldenCrossStrategy
# from .rsi_oversold import RSIOversoldStrategy
# from .bollinger_squeeze import BollingerSqueezeStrategy
# from .moving_average_crossover import MovingAverageCrossoverStrategy

__all__ = [
    # 딕셔너리 기반 전략 클래스들
    "DictBaseStrategy",
    "DictStrategyManager",
    "dict_strategy_manager",
    "DictMACDGoldenCrossStrategy",
    "DictRSIOversoldStrategy",
    "DictBollingerSqueezeStrategy",
    "DictMovingAverageCrossoverStrategy",

    # 기존 클래스들 (주석 처리)
    # "BaseStrategy",
    # "StrategyManager",
    # "strategy_manager",
    # "MACDGoldenCrossStrategy",
    # "RSIOversoldStrategy",
    # "BollingerSqueezeStrategy",
    # "MovingAverageCrossoverStrategy"
]