"""
한국 주식 기술적 분석기
- 기존 BTC 시스템의 기술적 분석 로직을 참조하여 한국 주식에 최적화
- 한국 주식 일봉에 맞게 매개변수 조정
- 완전 독립적으로 동작
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta, date
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from schemas import OHLCVData, TechnicalIndicators, AnalyzedStockData

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """한국 주식 기술적 분석기"""
    
    def __init__(self):
        # 일봉 기준 매개변수 설정
        self.macd_config = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        }
        self.rsi_config = {
            "period": 14
        }
        self.bb_config = {
            "period": 20,
            "std": 2
        }
        
        # 반전 분석 설정 (일봉 조정)
        self.reversal_config = {
            "support_resistance_period": 90,
            "volume_analysis_period": 20
        }
    
    def calculate_sma(self, prices: List[float], window: int) -> List[Optional[float]]:
        """Calculate Simple Moving Average."""
        if len(prices) < window:
            return [None] * len(prices)
        
        sma_values = []
        for i in range(len(prices)):
            if i < window - 1:
                sma_values.append(None)
            else:
                sma = sum(prices[i-window+1:i+1]) / window
                sma_values.append(sma)
        
        return sma_values
    
    def calculate_ema(self, prices: List[float], window: int) -> List[Optional[float]]:
        """Calculate Exponential Moving Average."""
        if len(prices) < window:
            return [None] * len(prices)
        
        alpha = 2 / (window + 1)
        ema_values = []
        
        # First EMA is SMA
        first_sma = sum(prices[:window]) / window
        ema_values.extend([None] * (window - 1))
        ema_values.append(first_sma)
        
        # Calculate subsequent EMAs
        for i in range(window, len(prices)):
            ema = alpha * prices[i] + (1 - alpha) * ema_values[-1]
            ema_values.append(ema)
        
        return ema_values
    
    def calculate_macd(self, prices: List[float], 
                      fast_period: int = 12, slow_period: int = 26, 
                      signal_period: int = 9) -> Dict[str, List[Optional[float]]]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < max(fast_period, slow_period):
            return {
                "macd": [None] * len(prices),
                "signal": [None] * len(prices), 
                "histogram": [None] * len(prices)
            }
        
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line.append(ema_fast[i] - ema_slow[i])
            else:
                macd_line.append(None)
        
        # Calculate signal line (EMA of MACD)
        macd_values_for_signal = [v for v in macd_line if v is not None]
        if len(macd_values_for_signal) >= signal_period:
            signal_ema = self.calculate_ema(macd_values_for_signal, signal_period)
            
            # Map back to original length
            signal_line = [None] * len(prices)
            signal_idx = 0
            for i, macd_val in enumerate(macd_line):
                if macd_val is not None:
                    if signal_idx < len(signal_ema) and signal_ema[signal_idx] is not None:
                        signal_line[i] = signal_ema[signal_idx]
                    signal_idx += 1
        else:
            signal_line = [None] * len(prices)
        
        # Calculate histogram (MACD - Signal)
        histogram = []
        for i in range(len(prices)):
            if macd_line[i] is not None and signal_line[i] is not None:
                histogram.append(macd_line[i] - signal_line[i])
            else:
                histogram.append(None)
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    def calculate_rsi(self, prices: List[float], window: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index."""
        if len(prices) < window + 1:
            return [None] * len(prices)
        
        # Calculate price changes
        price_changes = []
        for i in range(1, len(prices)):
            price_changes.append(prices[i] - prices[i-1])
        
        rsi_values = [None]  # First value is always None
        
        # Calculate gains and losses
        gains = [max(change, 0) for change in price_changes]
        losses = [abs(min(change, 0)) for change in price_changes]
        
        for i in range(window - 1, len(price_changes)):
            if i == window - 1:
                # First RSI calculation uses simple average
                avg_gain = sum(gains[i-window+1:i+1]) / window
                avg_loss = sum(losses[i-window+1:i+1]) / window
            else:
                # Subsequent calculations use exponential smoothing
                alpha = 1 / window
                avg_gain = alpha * gains[i] + (1 - alpha) * avg_gain
                avg_loss = alpha * losses[i] + (1 - alpha) * avg_loss
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    def calculate_bollinger_bands(self, prices: List[float], window: int = 20, 
                                 std_dev: float = 2) -> Dict[str, List[Optional[float]]]:
        """Calculate Bollinger Bands."""
        if len(prices) < window:
            return {
                "upper": [None] * len(prices),
                "middle": [None] * len(prices),
                "lower": [None] * len(prices)
            }
        
        sma_values = self.calculate_sma(prices, window)
        
        upper_band = []
        middle_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < window - 1:
                upper_band.append(None)
                middle_band.append(None)
                lower_band.append(None)
            else:
                # Calculate standard deviation for this window
                price_window = prices[i-window+1:i+1]
                mean_price = sum(price_window) / window
                variance = sum((p - mean_price) ** 2 for p in price_window) / window
                std = variance ** 0.5
                
                middle = sma_values[i]
                upper = middle + (std_dev * std)
                lower = middle - (std_dev * std)
                
                upper_band.append(upper)
                middle_band.append(middle)
                lower_band.append(lower)
        
        return {
            "upper": upper_band,
            "middle": middle_band,
            "lower": lower_band
        }
    
    def calculate_stochastic(self, highs: List[float], lows: List[float], 
                           closes: List[float], k_window: int = 14, 
                           d_window: int = 3) -> Dict[str, List[Optional[float]]]:
        """Calculate Stochastic Oscillator (%K and %D)."""
        if len(closes) < k_window:
            return {
                "k": [None] * len(closes),
                "d": [None] * len(closes)
            }
        
        k_values = []
        
        for i in range(len(closes)):
            if i < k_window - 1:
                k_values.append(None)
            else:
                # Find highest high and lowest low in the window
                high_window = highs[i-k_window+1:i+1]
                low_window = lows[i-k_window+1:i+1]
                
                highest_high = max(high_window)
                lowest_low = min(low_window)
                
                if highest_high == lowest_low:
                    k_percent = 50  # Avoid division by zero
                else:
                    k_percent = ((closes[i] - lowest_low) / 
                               (highest_high - lowest_low)) * 100
                
                k_values.append(k_percent)
        
        # Calculate %D (SMA of %K)
        k_values_for_d = [v for v in k_values if v is not None]
        if len(k_values_for_d) >= d_window:
            d_sma = self.calculate_sma(k_values_for_d, d_window)
            
            # Map back to original length
            d_values = [None] * len(closes)
            d_idx = 0
            for i, k_val in enumerate(k_values):
                if k_val is not None:
                    if d_idx < len(d_sma) and d_sma[d_idx] is not None:
                        d_values[i] = d_sma[d_idx]
                    d_idx += 1
        else:
            d_values = [None] * len(closes)
        
        return {
            "k": k_values,
            "d": d_values
        }
    
    def analyze_ohlcv_data(self, ohlcv_data: List[OHLCVData]) -> List[AnalyzedStockData]:
        """Calculate all technical indicators for OHLCV data."""
        if not ohlcv_data:
            return []
        
        # Sort by date
        sorted_data = sorted(ohlcv_data, key=lambda x: x.date)
        
        # Extract price series
        opens = [d.open for d in sorted_data]
        highs = [d.high for d in sorted_data]
        lows = [d.low for d in sorted_data]
        closes = [d.close for d in sorted_data]
        
        logger.info(f"Calculating technical indicators for {len(sorted_data)} data points")
        
        # Calculate all indicators
        sma_5 = self.calculate_sma(closes, 5)
        sma_20 = self.calculate_sma(closes, 20)
        sma_60 = self.calculate_sma(closes, 60)
        ema_12 = self.calculate_ema(closes, 12)
        ema_26 = self.calculate_ema(closes, 26)
        
        macd_data = self.calculate_macd(closes)
        rsi_14 = self.calculate_rsi(closes, 14)
        bollinger = self.calculate_bollinger_bands(closes)
        stochastic = self.calculate_stochastic(highs, lows, closes)
        
        # Create analyzed data
        analyzed_data = []
        for i, ohlcv in enumerate(sorted_data):
            technical_indicators = TechnicalIndicators(
                sma_5=sma_5[i],
                sma_20=sma_20[i],
                sma_60=sma_60[i],
                ema_12=ema_12[i],
                ema_26=ema_26[i],
                macd=macd_data["macd"][i],
                macd_signal=macd_data["signal"][i],
                macd_histogram=macd_data["histogram"][i],
                rsi_14=rsi_14[i],
                bollinger_upper=bollinger["upper"][i],
                bollinger_middle=bollinger["middle"][i],
                bollinger_lower=bollinger["lower"][i],
                stoch_k=stochastic["k"][i],
                stoch_d=stochastic["d"][i]
            )
            
            analyzed_stock_data = AnalyzedStockData(
                date=ohlcv.date,
                ticker=ohlcv.ticker,
                ohlcv=ohlcv,
                technical_indicators=technical_indicators
            )
            
            analyzed_data.append(analyzed_stock_data)
        
        logger.info(f"Technical analysis completed for {len(analyzed_data)} data points")
        return analyzed_data
    
    def get_analysis_summary(self, analyzed_data: List[AnalyzedStockData]) -> Dict[str, Any]:
        """Get summary of technical analysis."""
        if not analyzed_data:
            return {}
        
        latest_data = analyzed_data[-1]  # Most recent data
        indicators = latest_data.technical_indicators
        
        # Determine trends and signals
        signals = {}
        
        # MACD signals
        if indicators.macd is not None and indicators.macd_signal is not None:
            if indicators.macd > indicators.macd_signal:
                signals["macd"] = "bullish"
            else:
                signals["macd"] = "bearish"
        
        # RSI signals
        if indicators.rsi_14 is not None:
            if indicators.rsi_14 > 70:
                signals["rsi"] = "overbought"
            elif indicators.rsi_14 < 30:
                signals["rsi"] = "oversold"
            else:
                signals["rsi"] = "neutral"
        
        # Moving average signals
        current_price = latest_data.ohlcv.close
        if indicators.sma_20 is not None:
            if current_price > indicators.sma_20:
                signals["sma_20"] = "above"
            else:
                signals["sma_20"] = "below"
        
        # Bollinger Bands signals
        if (indicators.bollinger_upper is not None and 
            indicators.bollinger_lower is not None):
            if current_price > indicators.bollinger_upper:
                signals["bollinger"] = "above_upper"
            elif current_price < indicators.bollinger_lower:
                signals["bollinger"] = "below_lower"
            else:
                signals["bollinger"] = "within_bands"
        
        return {
            "ticker": latest_data.ticker,
            "analysis_date": latest_data.date.isoformat(),
            "current_price": current_price,
            "signals": signals,
            "indicators": {
                "sma_20": indicators.sma_20,
                "rsi_14": indicators.rsi_14,
                "macd": indicators.macd,
                "macd_signal": indicators.macd_signal
            }
        }