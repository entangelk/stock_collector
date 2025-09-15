"""
Moving Average Crossover strategy - detects golden/death cross patterns.
"""
from typing import Dict, Any
from .base_strategy import BaseStrategy
from schemas import AnalyzedStockData


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Moving Average Crossover screening strategy."""
    
    def __init__(self):
        super().__init__()
        self.description = "Detects golden cross (bullish) and death cross (bearish) patterns"
        self.parameters = {
            "signal_type": "golden_cross",  # "golden_cross" or "death_cross" or "both"
            "min_separation": 0.01,  # Minimum separation between MAs (1%)
            "volume_confirmation": True,  # Require volume confirmation
            "trend_confirmation": True   # Require overall trend confirmation
        }
    
    def applies_to(self, stock_data: AnalyzedStockData) -> bool:
        """Check if MA crossover pattern applies."""
        indicators = stock_data.technical_indicators
        
        # Both moving averages must be available
        if indicators.sma_20 is None or indicators.sma_60 is None:
            return False
        
        signal_type = self.parameters.get("signal_type", "golden_cross")
        min_separation = self.parameters.get("min_separation", 0.01)
        
        # Calculate separation
        ma_separation = abs(indicators.sma_20 - indicators.sma_60) / indicators.sma_60
        
        # Separation must be above minimum threshold
        if ma_separation < min_separation:
            return False
        
        # Check for crossover patterns
        has_golden_cross = indicators.sma_20 > indicators.sma_60
        has_death_cross = indicators.sma_20 < indicators.sma_60
        
        if signal_type == "golden_cross":
            pattern_match = has_golden_cross
        elif signal_type == "death_cross":
            pattern_match = has_death_cross
        else:  # "both"
            pattern_match = has_golden_cross or has_death_cross
        
        if not pattern_match:
            return False
        
        # Optional: volume confirmation
        volume_confirmation = self.parameters.get("volume_confirmation", True)
        if volume_confirmation:
            # Note: We'd need historical volume data to confirm this properly
            # For now, we'll assume volume is adequate
            pass
        
        # Optional: trend confirmation with longer-term indicators
        trend_confirmation = self.parameters.get("trend_confirmation", True)
        if trend_confirmation:
            current_price = stock_data.ohlcv.close
            
            # For golden cross, price should be above both MAs or trending up
            if has_golden_cross:
                trend_ok = current_price >= indicators.sma_20
            # For death cross, price should be below both MAs or trending down  
            else:
                trend_ok = current_price <= indicators.sma_20
            
            if not trend_ok:
                return False
        
        return True
    
    def get_signal_strength(self, stock_data: AnalyzedStockData) -> float:
        """Calculate signal strength based on crossover characteristics."""
        indicators = stock_data.technical_indicators
        
        if not self.applies_to(stock_data):
            return 0.0
        
        current_price = stock_data.ohlcv.close
        signal_type = self.parameters.get("signal_type", "golden_cross")
        
        # Determine if this is golden or death cross
        is_golden_cross = indicators.sma_20 > indicators.sma_60
        
        # Base strength from MA separation
        ma_separation = abs(indicators.sma_20 - indicators.sma_60) / indicators.sma_60
        separation_strength = min(ma_separation / 0.05, 1.0)  # Normalize to 5%
        
        # Price position strength
        price_strength = 0.0
        if is_golden_cross:
            # For golden cross, stronger when price is above both MAs
            if current_price > indicators.sma_20:
                price_strength += 0.3
            if current_price > indicators.sma_60:
                price_strength += 0.2
        else:
            # For death cross, stronger when price is below both MAs
            if current_price < indicators.sma_20:
                price_strength += 0.3
            if current_price < indicators.sma_60:
                price_strength += 0.2
        
        # RSI confirmation
        rsi_strength = 0.0
        if indicators.rsi_14 is not None:
            if is_golden_cross:
                # Golden cross stronger with RSI in bullish range (40-80)
                if 40 <= indicators.rsi_14 <= 80:
                    rsi_strength = 0.2
                elif indicators.rsi_14 > 80:
                    rsi_strength = 0.1  # Overbought concern
            else:
                # Death cross stronger with RSI in bearish range (20-60)
                if 20 <= indicators.rsi_14 <= 60:
                    rsi_strength = 0.2
                elif indicators.rsi_14 < 20:
                    rsi_strength = 0.1  # Oversold concern
        
        # MACD confirmation
        macd_strength = 0.0
        if (indicators.macd is not None and indicators.macd_signal is not None):
            if is_golden_cross:
                # Golden cross stronger when MACD > signal
                if indicators.macd > indicators.macd_signal:
                    macd_strength = 0.15
            else:
                # Death cross stronger when MACD < signal
                if indicators.macd < indicators.macd_signal:
                    macd_strength = 0.15
        
        # Volume strength (placeholder - would need historical data)
        volume_strength = 0.05  # Small default bonus
        
        # Combine all factors
        total_strength = (
            separation_strength * 0.4 +  # MA separation is primary
            price_strength * 0.3 +       # Price position
            rsi_strength * 0.15 +        # RSI confirmation  
            macd_strength * 0.1 +        # MACD confirmation
            volume_strength * 0.05       # Volume confirmation
        )
        
        return min(total_strength, 1.0)
    
    def get_analysis_summary(self, stock_data: AnalyzedStockData) -> Dict[str, Any]:
        """Get detailed analysis summary."""
        base_summary = super().get_analysis_summary(stock_data)
        
        if base_summary["applies"]:
            indicators = stock_data.technical_indicators
            current_price = stock_data.ohlcv.close
            
            # Determine crossover type
            is_golden_cross = indicators.sma_20 > indicators.sma_60
            crossover_type = "golden_cross" if is_golden_cross else "death_cross"
            
            # Calculate key metrics
            ma_separation_pct = ((indicators.sma_20 - indicators.sma_60) / 
                               indicators.sma_60 * 100)
            
            price_vs_sma20_pct = ((current_price - indicators.sma_20) / 
                                indicators.sma_20 * 100)
            
            price_vs_sma60_pct = ((current_price - indicators.sma_60) / 
                                indicators.sma_60 * 100)
            
            base_summary.update({
                "details": {
                    "crossover_type": crossover_type,
                    "sma_20": indicators.sma_20,
                    "sma_60": indicators.sma_60,
                    "ma_separation_pct": round(ma_separation_pct, 2),
                    "price_vs_sma20_pct": round(price_vs_sma20_pct, 2),
                    "price_vs_sma60_pct": round(price_vs_sma60_pct, 2),
                    "rsi_14": indicators.rsi_14,
                    "macd": indicators.macd,
                    "macd_signal": indicators.macd_signal
                },
                "signal_type": "bullish" if is_golden_cross else "bearish",
                "recommendation": self._get_recommendation(stock_data),
                "target_levels": self._get_target_levels(stock_data)
            })
        
        return base_summary
    
    def _get_target_levels(self, stock_data: AnalyzedStockData) -> Dict[str, float]:
        """Get target and stop levels based on MA analysis."""
        indicators = stock_data.technical_indicators
        current_price = stock_data.ohlcv.close
        
        is_golden_cross = indicators.sma_20 > indicators.sma_60
        
        if is_golden_cross:
            # For golden cross - bullish targets
            support_level = indicators.sma_20
            resistance_level = current_price * 1.10  # 10% above current
            stop_level = indicators.sma_60
        else:
            # For death cross - bearish targets  
            resistance_level = indicators.sma_20
            support_level = current_price * 0.90  # 10% below current
            stop_level = indicators.sma_60
        
        return {
            "support": support_level,
            "resistance": resistance_level,
            "stop_level": stop_level
        }
    
    def _get_recommendation(self, stock_data: AnalyzedStockData) -> str:
        """Get trading recommendation based on signal strength."""
        indicators = stock_data.technical_indicators
        strength = self.get_signal_strength(stock_data)
        is_golden_cross = indicators.sma_20 > indicators.sma_60
        
        if is_golden_cross:
            if strength >= 0.8:
                return "Strong Buy (Golden Cross)"
            elif strength >= 0.6:
                return "Buy (MA Crossover)"
            elif strength >= 0.4:
                return "Weak Buy (Trend Change)"
            else:
                return "Watch (Early Signal)"
        else:
            if strength >= 0.8:
                return "Strong Sell (Death Cross)"
            elif strength >= 0.6:
                return "Sell (MA Crossover)"
            elif strength >= 0.4:
                return "Weak Sell (Trend Change)"
            else:
                return "Watch (Early Warning)"