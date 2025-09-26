"""
Base strategy class for stock screening.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from schemas import AnalyzedStockData

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """Base class for all screening strategies."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = ""
        self.parameters = {}
    
    @abstractmethod
    def applies_to(self, stock_data: AnalyzedStockData) -> bool:
        """Check if this strategy applies to the given stock data."""
        pass
    
    @abstractmethod
    def get_signal_strength(self, stock_data: AnalyzedStockData) -> float:
        """Get signal strength (0.0 to 1.0, where 1.0 is strongest signal)."""
        pass
    
    def get_description(self) -> str:
        """Get strategy description."""
        return self.description or f"{self.name} screening strategy"
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.parameters.copy()
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set strategy parameters."""
        self.parameters.update(parameters)
    
    def validate_data(self, stock_data: AnalyzedStockData) -> bool:
        """Validate that stock data has required indicators."""
        return (
            stock_data.technical_indicators is not None and
            stock_data.ohlcv is not None
        )
    
    def get_analysis_summary(self, stock_data: AnalyzedStockData) -> Dict[str, Any]:
        """Get analysis summary for this strategy."""
        if not self.applies_to(stock_data):
            return {
                "strategy": self.name,
                "applies": False,
                "signal_strength": 0.0
            }
        
        signal_strength = self.get_signal_strength(stock_data)
        
        return {
            "strategy": self.name,
            "applies": True,
            "signal_strength": signal_strength,
            "ticker": stock_data.ticker,
            "date": stock_data.date.isoformat(),
            "current_price": stock_data.ohlcv.close,
            "parameters": self.get_parameters()
        }


class StrategyManager:
    """Manager for all screening strategies."""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self._register_default_strategies()
    
    def register_strategy(self, strategy: BaseStrategy) -> None:
        """Register a new strategy."""
        self.strategies[strategy.name.lower()] = strategy
        logger.info(f"Registered strategy: {strategy.name}")
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """Get strategy by name."""
        return self.strategies.get(strategy_name.lower())
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """List all available strategies."""
        return [
            {
                "name": name,
                "description": strategy.get_description(),
                "parameters": strategy.get_parameters()
            }
            for name, strategy in self.strategies.items()
        ]
    
    def screen_stocks(self, strategy_name: str, 
                     stock_data_list: List[AnalyzedStockData],
                     parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Screen stocks using specified strategy."""
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            raise ValueError(f"Strategy '{strategy_name}' not found")
        
        # Set parameters if provided
        if parameters:
            strategy.set_parameters(parameters)
        
        results = []
        
        for stock_data in stock_data_list:
            try:
                if not strategy.validate_data(stock_data):
                    logger.warning(f"Invalid data for {stock_data.ticker}, skipping")
                    continue
                
                if strategy.applies_to(stock_data):
                    analysis = strategy.get_analysis_summary(stock_data)
                    results.append(analysis)
                    
            except Exception as e:
                logger.error(f"Error screening {stock_data.ticker} with {strategy_name}: {e}")
                continue
        
        # Sort by signal strength (descending)
        results.sort(key=lambda x: x["signal_strength"], reverse=True)
        
        return results
    
    def _register_default_strategies(self) -> None:
        """Register default strategies."""
        # Import here to avoid circular imports
        from .macd_golden_cross import MACDGoldenCrossStrategy
        from .rsi_oversold import RSIOversoldStrategy
        from .bollinger_squeeze import BollingerSqueezeStrategy
        from .moving_average_crossover import MovingAverageCrossoverStrategy
        
        self.register_strategy(MACDGoldenCrossStrategy())
        self.register_strategy(RSIOversoldStrategy())
        self.register_strategy(BollingerSqueezeStrategy())
        self.register_strategy(MovingAverageCrossoverStrategy())


# Global strategy manager instance
strategy_manager = StrategyManager()