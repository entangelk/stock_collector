"""
MACD Golden Cross strategy - detects when MACD line crosses above signal line.
"""
from typing import Dict, Any
from .base_strategy import BaseStrategy
from schemas import AnalyzedStockData


class MACDGoldenCrossStrategy(BaseStrategy):
    """MACD Golden Cross screening strategy."""
    
    def __init__(self):
        super().__init__()
        self.description = "Detects when MACD line crosses above signal line (bullish signal)"
        self.parameters = {
            "min_histogram": 0.1,  # Minimum MACD histogram value
            "min_volume_ratio": 1.2,  # Minimum volume ratio vs average
            "max_rsi": 80  # Maximum RSI to avoid overbought stocks
        }
    
    def applies_to(self, stock_data: AnalyzedStockData) -> bool:
        """Check if MACD golden cross applies."""
        indicators = stock_data.technical_indicators
        
        # Check required indicators are present
        if (indicators.macd is None or 
            indicators.macd_signal is None or 
            indicators.macd_histogram is None):
            return False
        
        # MACD line must be above signal line
        macd_above_signal = indicators.macd > indicators.macd_signal
        
        # MACD histogram should be positive and above minimum
        min_histogram = self.parameters.get("min_histogram", 0.1)
        histogram_positive = indicators.macd_histogram > min_histogram
        
        # Optional: check volume and RSI constraints
        volume_ok = True
        rsi_ok = True
        
        # Volume constraint (if we had previous volume data)
        min_volume_ratio = self.parameters.get("min_volume_ratio", 1.2)
        # Note: We'd need historical volume data to calculate this properly
        
        # RSI constraint - avoid overbought stocks
        max_rsi = self.parameters.get("max_rsi", 80)
        if indicators.rsi_14 is not None:
            rsi_ok = indicators.rsi_14 < max_rsi
        
        return macd_above_signal and histogram_positive and volume_ok and rsi_ok
    
    def get_signal_strength(self, stock_data: AnalyzedStockData) -> float:
        """Calculate signal strength based on MACD characteristics."""
        indicators = stock_data.technical_indicators
        
        if not self.applies_to(stock_data):
            return 0.0
        
        # Base strength from MACD histogram
        histogram_strength = min(abs(indicators.macd_histogram) / 10.0, 1.0)
        
        # Additional strength from MACD distance from signal
        macd_distance = abs(indicators.macd - indicators.macd_signal)
        distance_strength = min(macd_distance / 5.0, 0.5)
        
        # RSI contribution (stronger signal when RSI is moderate)
        rsi_strength = 0.0
        if indicators.rsi_14 is not None:
            # Optimal RSI range is 40-70 for golden cross
            if 40 <= indicators.rsi_14 <= 70:
                rsi_strength = 0.3
            elif 30 <= indicators.rsi_14 < 40 or 70 < indicators.rsi_14 <= 80:
                rsi_strength = 0.2
            else:
                rsi_strength = 0.1
        
        # Price position relative to moving averages
        ma_strength = 0.0
        current_price = stock_data.ohlcv.close
        
        if indicators.sma_20 is not None:
            if current_price > indicators.sma_20:
                ma_strength += 0.1
        
        if indicators.sma_60 is not None:
            if current_price > indicators.sma_60:
                ma_strength += 0.1
        
        # Combine all factors
        total_strength = histogram_strength + distance_strength + rsi_strength + ma_strength
        
        # Normalize to 0-1 range
        return min(total_strength, 1.0)
    
    def get_analysis_summary(self, stock_data: AnalyzedStockData) -> Dict[str, Any]:
        """Get detailed analysis summary."""
        base_summary = super().get_analysis_summary(stock_data)
        
        if base_summary["applies"]:
            indicators = stock_data.technical_indicators
            
            base_summary.update({
                "details": {
                    "macd": indicators.macd,
                    "macd_signal": indicators.macd_signal,
                    "macd_histogram": indicators.macd_histogram,
                    "rsi_14": indicators.rsi_14,
                    "sma_20": indicators.sma_20,
                    "price_vs_sma20": stock_data.ohlcv.close - indicators.sma_20 if indicators.sma_20 else None
                },
                "signal_type": "bullish",
                "recommendation": self._get_recommendation(stock_data)
            })
        
        return base_summary
    
    def _get_recommendation(self, stock_data: AnalyzedStockData) -> str:
        """Get trading recommendation based on signal strength."""
        strength = self.get_signal_strength(stock_data)
        
        if strength >= 0.8:
            return "Strong Buy"
        elif strength >= 0.6:
            return "Buy"
        elif strength >= 0.4:
            return "Weak Buy"
        else:
            return "Watch"