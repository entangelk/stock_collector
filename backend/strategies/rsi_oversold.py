"""
RSI Oversold strategy - detects potentially oversold stocks.
"""
from typing import Dict, Any
from .base_strategy import BaseStrategy
from schemas import AnalyzedStockData


class RSIOversoldStrategy(BaseStrategy):
    """RSI Oversold screening strategy."""
    
    def __init__(self):
        super().__init__()
        self.description = "Detects stocks that are potentially oversold based on RSI"
        self.parameters = {
            "max_rsi": 30,  # RSI threshold for oversold
            "min_rsi": 15,  # Minimum RSI to avoid extreme situations
            "require_uptrend": True,  # Require price above long-term MA
            "min_volume_ratio": 1.1   # Minimum volume ratio
        }
    
    def applies_to(self, stock_data: AnalyzedStockData) -> bool:
        """Check if RSI oversold strategy applies."""
        indicators = stock_data.technical_indicators
        
        # RSI must be available
        if indicators.rsi_14 is None:
            return False
        
        max_rsi = self.parameters.get("max_rsi", 30)
        min_rsi = self.parameters.get("min_rsi", 15)
        
        # RSI must be in oversold range but not extremely low
        rsi_in_range = min_rsi <= indicators.rsi_14 <= max_rsi
        
        if not rsi_in_range:
            return False
        
        # Optional: require overall uptrend (price above long-term MA)
        require_uptrend = self.parameters.get("require_uptrend", True)
        if require_uptrend and indicators.sma_60 is not None:
            current_price = stock_data.ohlcv.close
            in_uptrend = current_price > indicators.sma_60
            if not in_uptrend:
                return False
        
        return True
    
    def get_signal_strength(self, stock_data: AnalyzedStockData) -> float:
        """Calculate signal strength based on RSI and supporting indicators."""
        indicators = stock_data.technical_indicators
        
        if not self.applies_to(stock_data):
            return 0.0
        
        # RSI strength - stronger signal when RSI is lower (more oversold)
        max_rsi = self.parameters.get("max_rsi", 30)
        min_rsi = self.parameters.get("min_rsi", 15)
        
        rsi_range = max_rsi - min_rsi
        rsi_strength = (max_rsi - indicators.rsi_14) / rsi_range
        rsi_strength = max(0.0, min(rsi_strength, 1.0))
        
        # Support from moving averages
        ma_strength = 0.0
        current_price = stock_data.ohlcv.close
        
        # Bonus if price is near or above short-term MA (potential bounce)
        if indicators.sma_20 is not None:
            price_to_sma20 = current_price / indicators.sma_20
            if 0.95 <= price_to_sma20 <= 1.05:  # Within 5% of SMA20
                ma_strength += 0.2
        
        # Bonus if still in long-term uptrend
        if indicators.sma_60 is not None:
            if current_price > indicators.sma_60:
                ma_strength += 0.2
        
        # MACD support (if MACD is turning positive)
        macd_strength = 0.0
        if (indicators.macd is not None and 
            indicators.macd_signal is not None and 
            indicators.macd_histogram is not None):
            
            # Bonus if MACD histogram is turning positive
            if indicators.macd_histogram > 0:
                macd_strength += 0.1
            
            # Bonus if MACD is above signal line
            if indicators.macd > indicators.macd_signal:
                macd_strength += 0.1
        
        # Bollinger Bands support
        bb_strength = 0.0
        if (indicators.bollinger_lower is not None and 
            indicators.bollinger_middle is not None):
            
            # Bonus if price is near lower Bollinger Band
            if current_price <= indicators.bollinger_lower * 1.02:  # Within 2%
                bb_strength += 0.2
        
        # Combine all factors
        total_strength = (
            rsi_strength * 0.5 +     # RSI is primary factor
            ma_strength * 0.3 +      # MA support
            macd_strength * 0.1 +    # MACD confirmation
            bb_strength * 0.1        # Bollinger Band support
        )
        
        return min(total_strength, 1.0)
    
    def get_analysis_summary(self, stock_data: AnalyzedStockData) -> Dict[str, Any]:
        """Get detailed analysis summary."""
        base_summary = super().get_analysis_summary(stock_data)
        
        if base_summary["applies"]:
            indicators = stock_data.technical_indicators
            current_price = stock_data.ohlcv.close
            
            # Calculate price distances from key levels
            price_vs_sma20 = None
            price_vs_sma60 = None
            price_vs_bb_lower = None
            
            if indicators.sma_20:
                price_vs_sma20 = (current_price / indicators.sma_20 - 1) * 100
            
            if indicators.sma_60:
                price_vs_sma60 = (current_price / indicators.sma_60 - 1) * 100
            
            if indicators.bollinger_lower:
                price_vs_bb_lower = (current_price / indicators.bollinger_lower - 1) * 100
            
            base_summary.update({
                "details": {
                    "rsi_14": indicators.rsi_14,
                    "price_vs_sma20_pct": price_vs_sma20,
                    "price_vs_sma60_pct": price_vs_sma60,
                    "price_vs_bb_lower_pct": price_vs_bb_lower,
                    "macd": indicators.macd,
                    "macd_histogram": indicators.macd_histogram
                },
                "signal_type": "oversold_bounce",
                "recommendation": self._get_recommendation(stock_data)
            })
        
        return base_summary
    
    def _get_recommendation(self, stock_data: AnalyzedStockData) -> str:
        """Get trading recommendation based on signal strength."""
        strength = self.get_signal_strength(stock_data)
        
        if strength >= 0.8:
            return "Strong Buy (Oversold Bounce)"
        elif strength >= 0.6:
            return "Buy (Oversold)"
        elif strength >= 0.4:
            return "Watch (Potential Bounce)"
        else:
            return "Caution (Weak Signal)"