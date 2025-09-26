"""
Bollinger Squeeze strategy - detects low volatility periods that may precede breakouts.
"""
from typing import Dict, Any
from .base_strategy import BaseStrategy
from schemas import AnalyzedStockData


class BollingerSqueezeStrategy(BaseStrategy):
    """Bollinger Squeeze screening strategy."""
    
    def __init__(self):
        super().__init__()
        self.description = "Detects stocks in low volatility squeeze that may breakout"
        self.parameters = {
            "max_band_width": 0.10,  # Maximum Bollinger Band width (as % of middle)
            "min_volume_ratio": 0.8,  # Minimum volume ratio (lower volume during squeeze)
            "breakout_threshold": 0.02,  # Price movement % to confirm breakout
            "require_consolidation": True  # Require price to be consolidating
        }
    
    def applies_to(self, stock_data: AnalyzedStockData) -> bool:
        """Check if Bollinger squeeze applies."""
        indicators = stock_data.technical_indicators
        
        # Bollinger Bands must be available
        if (indicators.bollinger_upper is None or 
            indicators.bollinger_middle is None or 
            indicators.bollinger_lower is None):
            return False
        
        # Calculate band width as percentage of middle band
        band_width = (indicators.bollinger_upper - indicators.bollinger_lower) / indicators.bollinger_middle
        max_band_width = self.parameters.get("max_band_width", 0.10)
        
        # Band width must be narrow (squeeze condition)
        is_squeezed = band_width <= max_band_width
        
        if not is_squeezed:
            return False
        
        # Optional: check for consolidation pattern
        require_consolidation = self.parameters.get("require_consolidation", True)
        if require_consolidation:
            current_price = stock_data.ohlcv.close
            
            # Price should be relatively close to middle band
            price_to_middle = abs(current_price - indicators.bollinger_middle) / indicators.bollinger_middle
            if price_to_middle > 0.03:  # More than 3% away from middle
                return False
        
        return True
    
    def get_signal_strength(self, stock_data: AnalyzedStockData) -> float:
        """Calculate signal strength based on squeeze characteristics."""
        indicators = stock_data.technical_indicators
        
        if not self.applies_to(stock_data):
            return 0.0
        
        current_price = stock_data.ohlcv.close
        
        # Band width strength - tighter squeeze = higher strength
        band_width = (indicators.bollinger_upper - indicators.bollinger_lower) / indicators.bollinger_middle
        max_band_width = self.parameters.get("max_band_width", 0.10)
        
        # Invert band width for strength (narrower = stronger)
        width_strength = 1.0 - (band_width / max_band_width)
        width_strength = max(0.0, min(width_strength, 1.0))
        
        # Price position strength - closer to middle = stronger
        price_distance = abs(current_price - indicators.bollinger_middle) / indicators.bollinger_middle
        position_strength = max(0.0, 1.0 - (price_distance / 0.03))  # Normalize to 3%
        
        # RSI neutrality bonus (RSI near 50 suggests balanced momentum)
        rsi_strength = 0.0
        if indicators.rsi_14 is not None:
            rsi_distance_from_50 = abs(indicators.rsi_14 - 50)
            # Bonus when RSI is between 40-60 (neutral zone)
            if rsi_distance_from_50 <= 10:
                rsi_strength = (10 - rsi_distance_from_50) / 10 * 0.3
        
        # Volume strength - lower volume during squeeze is typical
        # Note: We'd need historical volume data to calculate this properly
        volume_strength = 0.1  # Default small bonus
        
        # Moving average convergence bonus
        ma_strength = 0.0
        if indicators.sma_20 is not None and indicators.sma_60 is not None:
            ma_convergence = abs(indicators.sma_20 - indicators.sma_60) / indicators.sma_60
            # Bonus when moving averages are close (convergence)
            if ma_convergence < 0.05:  # Within 5%
                ma_strength = 0.2
        
        # Combine all factors
        total_strength = (
            width_strength * 0.4 +      # Band width is primary factor
            position_strength * 0.3 +   # Price position
            rsi_strength * 0.2 +        # RSI neutrality
            ma_strength * 0.1           # MA convergence
        )
        
        return min(total_strength, 1.0)
    
    def get_analysis_summary(self, stock_data: AnalyzedStockData) -> Dict[str, Any]:
        """Get detailed analysis summary."""
        base_summary = super().get_analysis_summary(stock_data)
        
        if base_summary["applies"]:
            indicators = stock_data.technical_indicators
            current_price = stock_data.ohlcv.close
            
            # Calculate key metrics
            band_width_pct = ((indicators.bollinger_upper - indicators.bollinger_lower) / 
                            indicators.bollinger_middle * 100)
            
            price_to_upper_pct = ((indicators.bollinger_upper - current_price) / 
                                current_price * 100)
            
            price_to_lower_pct = ((current_price - indicators.bollinger_lower) / 
                                current_price * 100)
            
            base_summary.update({
                "details": {
                    "band_width_pct": round(band_width_pct, 2),
                    "price_to_upper_pct": round(price_to_upper_pct, 2),
                    "price_to_lower_pct": round(price_to_lower_pct, 2),
                    "bollinger_upper": indicators.bollinger_upper,
                    "bollinger_middle": indicators.bollinger_middle,
                    "bollinger_lower": indicators.bollinger_lower,
                    "rsi_14": indicators.rsi_14,
                    "volume": stock_data.ohlcv.volume
                },
                "signal_type": "volatility_squeeze",
                "recommendation": self._get_recommendation(stock_data),
                "breakout_levels": {
                    "upper_breakout": indicators.bollinger_upper,
                    "lower_breakdown": indicators.bollinger_lower
                }
            })
        
        return base_summary
    
    def _get_recommendation(self, stock_data: AnalyzedStockData) -> str:
        """Get trading recommendation based on signal strength."""
        strength = self.get_signal_strength(stock_data)
        
        if strength >= 0.8:
            return "Strong Watch (Breakout Imminent)"
        elif strength >= 0.6:
            return "Watch (Squeeze Pattern)"
        elif strength >= 0.4:
            return "Monitor (Potential Squeeze)"
        else:
            return "Neutral (Weak Squeeze)"