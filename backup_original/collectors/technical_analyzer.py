#!/usr/bin/env python3
"""
한국 주식 기술적 분석기
- 기존 BTC 시스템의 기술적 분석 로직을 READ-ONLY로 참조
- 한국 주식 일봉에 맞게 매개변수 조정
- 완전 독립적으로 동작
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List
import pandas as pd
import numpy as np

# 기존 BTC 시스템 모듈을 READ-ONLY로 import
try:
    from docs.investment_ai.indicators.technical_indicators import TechnicalIndicators
    BTC_INDICATORS_AVAILABLE = True
    logging.info("기존 BTC 기술적 지표 모듈 사용 가능")
except ImportError:
    BTC_INDICATORS_AVAILABLE = False
    logging.warning("기존 BTC 기술적 지표 모듈을 불러올 수 없습니다. 독립 구현을 사용합니다.")

from korean_stocks.config.korean_config import TECHNICAL_CONFIG
from korean_stocks.utils.database import get_korean_db
from korean_stocks.utils.resource_monitor import safe_korean_execution

logger = logging.getLogger(__name__)

class KoreanTechnicalAnalyzer:
    """한국 주식 기술적 분석기"""
    
    def __init__(self):
        self.config = TECHNICAL_CONFIG
        self.db_manager = get_korean_db()
        
        # 일봉 기준 매개변수
        self.macd_config = self.config["macd"]
        self.rsi_config = self.config["rsi"] 
        self.bb_config = self.config["bollinger_bands"]
        self.ema_config = self.config["ema"]
        
        # 반전 분석 설정 (기존 1시간봉 → 일봉 조정)
        self.reversal_config = self.config["reversal_analysis"]
        
        # BTC 시스템 기술적 지표 클래스 초기화
        if BTC_INDICATORS_AVAILABLE:
            self.btc_indicators = TechnicalIndicators()
        else:
            self.btc_indicators = None
        
    # ================ 기본 기술적 지표 (한국 주식 최적화) ================
    
    def calculate_korean_macd(self, df: pd.DataFrame) -> Dict:
        """한국 주식용 MACD 계산 (일봉 기준)"""
        try:
            if BTC_INDICATORS_AVAILABLE and self.btc_indicators:
                # 기존 BTC 시스템 클래스 활용 (READ-ONLY)
                df_with_indicators = self.btc_indicators.calculate_trend_indicators(df.copy())
                macd_result = {
                    "macd": df_with_indicators["MACD"].tolist() if "MACD" in df_with_indicators.columns else [],
                    "signal": df_with_indicators["MACD_Signal"].tolist() if "MACD_Signal" in df_with_indicators.columns else [],
                    "histogram": df_with_indicators["MACD_Histogram"].tolist() if "MACD_Histogram" in df_with_indicators.columns else []
                }
            else:
                # 독립 구현
                macd_result = self._calculate_macd_standalone(df)
            
            # 한국 주식 특화 해석 추가
            current_macd = macd_result.get("macd", [0])[-1] if macd_result.get("macd") else 0
            current_signal = macd_result.get("signal", [0])[-1] if macd_result.get("signal") else 0
            current_histogram = macd_result.get("histogram", [0])[-1] if macd_result.get("histogram") else 0
            
            # 7일 MACD 분석 (주간 필터링용)
            weekly_analysis = self._analyze_7day_macd_trend(macd_result.get("histogram", []))
            
            return {
                **macd_result,
                "korean_analysis": {
                    "current_phase": "golden_cross" if current_macd > current_signal else "dead_cross",
                    "histogram_trend": "increasing" if current_histogram > 0 else "decreasing", 
                    "signal_strength": abs(current_histogram) * 100,  # 0-100 스케일
                    "weekly_filter_signal": weekly_analysis["filter_signal"],
                    "reversal_probability": weekly_analysis["reversal_prob"]
                }
            }
            
        except Exception as e:
            logger.error(f"MACD 계산 실패: {e}")
            return {}
    
    def _analyze_7day_macd_trend(self, histogram: List[float]) -> Dict:
        """7일 MACD 히스토그램 추세 분석 (주간 필터링용)"""
        if len(histogram) < 7:
            return {"filter_signal": False, "reversal_prob": 0}
        
        recent_7days = histogram[-7:]
        
        # 7일간 추세 확인
        increasing_days = sum(1 for i in range(1, len(recent_7days)) if recent_7days[i] > recent_7days[i-1])
        decreasing_days = 7 - 1 - increasing_days
        
        # 반전 신호 감지
        has_reversal_signal = False
        reversal_prob = 0
        
        # 상승 반전: 음수에서 양수로, 최근 3일 상승
        if (recent_7days[-3] < 0 and recent_7days[-1] > 0 and 
            sum(recent_7days[-3:]) > sum(recent_7days[-6:-3])):
            has_reversal_signal = True
            reversal_prob = min(increasing_days * 15, 85)
        
        # 하락 반전: 양수에서 음수로, 최근 3일 하락
        elif (recent_7days[-3] > 0 and recent_7days[-1] < 0 and
              sum(recent_7days[-3:]) < sum(recent_7days[-6:-3])):
            has_reversal_signal = True
            reversal_prob = min(decreasing_days * 15, 85)
        
        return {
            "filter_signal": has_reversal_signal,
            "reversal_prob": reversal_prob,
            "trend_days": {"increasing": increasing_days, "decreasing": decreasing_days}
        }
    
    def calculate_korean_rsi(self, df: pd.DataFrame) -> Dict:
        """한국 주식용 RSI 계산"""
        try:
            if BTC_INDICATORS_AVAILABLE and self.btc_indicators:
                # 기존 BTC 시스템 클래스 활용
                df_with_indicators = self.btc_indicators.calculate_momentum_indicators(df.copy())
                rsi_result = {
                    "rsi": df_with_indicators["RSI"].tolist() if "RSI" in df_with_indicators.columns else [50] * len(df)
                }
            else:
                rsi_result = self._calculate_rsi_standalone(df)
            
            current_rsi = rsi_result.get("rsi", [50])[-1] if rsi_result.get("rsi") else 50
            
            # 한국 시장 특화 RSI 해석
            korean_interpretation = {
                "current_value": current_rsi,
                "market_condition": self._interpret_korean_rsi(current_rsi),
                "divergence_signal": self._check_rsi_divergence(df, rsi_result.get("rsi", [])),
                "overbought_oversold": "overbought" if current_rsi > 70 else ("oversold" if current_rsi < 30 else "normal")
            }
            
            return {
                **rsi_result,
                "korean_analysis": korean_interpretation
            }
            
        except Exception as e:
            logger.error(f"RSI 계산 실패: {e}")
            return {}
    
    def _interpret_korean_rsi(self, rsi_value: float) -> str:
        """한국 시장 특성을 반영한 RSI 해석"""
        if rsi_value >= 75:
            return "극도_과매수"  # 한국 시장은 변동성이 커서 75 이상을 극도로 봄
        elif rsi_value >= 65:
            return "과매수"
        elif rsi_value <= 25:
            return "극도_과매도"  # 25 이하를 극도로 봄
        elif rsi_value <= 35:
            return "과매도"
        else:
            return "중립"
    
    def calculate_korean_bollinger_bands(self, df: pd.DataFrame) -> Dict:
        """한국 주식용 볼린저 밴드"""
        try:
            if BTC_INDICATORS_AVAILABLE and self.btc_indicators:
                # 기존 BTC 시스템 클래스 활용
                df_with_indicators = self.btc_indicators.calculate_volatility_indicators(df.copy())
                bb_result = {
                    "upper_band": df_with_indicators["bb_upper"].tolist() if "bb_upper" in df_with_indicators.columns else [],
                    "middle_band": df_with_indicators["bb_middle"].tolist() if "bb_middle" in df_with_indicators.columns else [],
                    "lower_band": df_with_indicators["bb_lower"].tolist() if "bb_lower" in df_with_indicators.columns else []
                }
            else:
                # BTC 지표 클래스를 사용할 수 없는 경우 에러 반환
                logger.error("BTC 기술적 지표 클래스를 사용할 수 없습니다.")
                return {"error": "볼린저 밴드 계산 불가", "success": False}
            
            # 현재 가격의 밴드 내 위치
            current_price = df['close'].iloc[-1] if 'close' in df.columns else df['종가'].iloc[-1]
            upper_band = bb_result.get("upper_band", [current_price])[-1] if bb_result.get("upper_band") else current_price
            lower_band = bb_result.get("lower_band", [current_price])[-1] if bb_result.get("lower_band") else current_price
            middle_band = bb_result.get("middle_band", [current_price])[-1] if bb_result.get("middle_band") else current_price
            
            # 밴드 폭 분석 (변동성)
            band_width = ((upper_band - lower_band) / middle_band) * 100
            
            # 가격 위치 (%)
            if upper_band != lower_band:
                price_position = ((current_price - lower_band) / (upper_band - lower_band)) * 100
            else:
                price_position = 50
            
            korean_analysis = {
                "price_position_pct": price_position,
                "band_width": band_width,
                "volatility_level": "high" if band_width > 10 else ("low" if band_width < 5 else "normal"),
                "squeeze_signal": band_width < 5,  # 밴드 수축 신호
                "breakout_direction": "upper" if price_position > 80 else ("lower" if price_position < 20 else "middle")
            }
            
            return {
                **bb_result,
                "korean_analysis": korean_analysis
            }
            
        except Exception as e:
            logger.error(f"볼린저 밴드 계산 실패: {e}")
            return {}
    
    # ================ 독립 구현 지표들 (BTC 모듈 없을 때 백업) ================
    
    def _calculate_macd_standalone(self, df: pd.DataFrame) -> Dict:
        """MACD 독립 구현"""
        try:
            close_prices = df['close'] if 'close' in df.columns else df['종가']
            
            # EMA 계산
            ema_12 = close_prices.ewm(span=self.macd_config["fast_period"]).mean()
            ema_26 = close_prices.ewm(span=self.macd_config["slow_period"]).mean()
            
            # MACD Line
            macd_line = ema_12 - ema_26
            
            # Signal Line
            signal_line = macd_line.ewm(span=self.macd_config["signal_period"]).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            return {
                "macd": macd_line.tolist(),
                "signal": signal_line.tolist(), 
                "histogram": histogram.tolist()
            }
            
        except Exception as e:
            logger.error(f"MACD 독립 계산 실패: {e}")
            return {}
    
    def _calculate_rsi_standalone(self, df: pd.DataFrame) -> Dict:
        """RSI 독립 구현"""
        try:
            close_prices = df['close'] if 'close' in df.columns else df['종가']
            
            # 가격 변화
            price_diff = close_prices.diff()
            
            # 상승/하락 구분
            gains = price_diff.where(price_diff > 0, 0)
            losses = -price_diff.where(price_diff < 0, 0)
            
            # 평균 구하기
            avg_gains = gains.rolling(window=self.rsi_config["period"]).mean()
            avg_losses = losses.rolling(window=self.rsi_config["period"]).mean()
            
            # RSI 계산
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            return {
                "rsi": rsi.fillna(50).tolist()
            }
            
        except Exception as e:
            logger.error(f"RSI 독립 계산 실패: {e}")
            return {}
    
    # ================ 한국 주식 특화 분석 ================
    
    def analyze_korean_stock_pattern(self, df: pd.DataFrame) -> Dict:
        """한국 주식 특화 패턴 분석"""
        try:
            # 거래량 패턴 분석
            volume_analysis = self._analyze_korean_volume_pattern(df)
            
            # 외국인 매매 영향 추정 (거래량 기반)
            foreign_influence = self._estimate_foreign_influence(df)
            
            # 박스권 vs 돌파 분석
            market_structure = self._analyze_market_structure(df)
            
            # 지지/저항 레벨 (일봉 기준 조정)
            support_resistance = self._find_korean_support_resistance(df)
            
            return {
                "volume_pattern": volume_analysis,
                "foreign_influence": foreign_influence,
                "market_structure": market_structure,
                "support_resistance": support_resistance,
                "pattern_confidence": self._calculate_pattern_confidence([
                    volume_analysis, foreign_influence, market_structure
                ])
            }
            
        except Exception as e:
            logger.error(f"한국 주식 패턴 분석 실패: {e}")
            return {}
    
    def _analyze_korean_volume_pattern(self, df: pd.DataFrame) -> Dict:
        """한국 시장 특화 거래량 분석"""
        try:
            volume_col = 'volume' if 'volume' in df.columns else '거래량'
            volumes = df[volume_col]
            
            # 최근 20일 평균 대비 현재 거래량
            avg_volume_20 = volumes.rolling(20).mean().iloc[-1]
            current_volume = volumes.iloc[-1]
            volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
            
            # 거래량 급증 여부 (한국 시장은 2배 이상을 급증으로 봄)
            volume_surge = volume_ratio > 2.0
            
            # 거래량 추세 (최근 5일)
            recent_volumes = volumes.tail(5)
            volume_trend = "increasing" if recent_volumes.is_monotonic_increasing else (
                "decreasing" if recent_volumes.is_monotonic_decreasing else "mixed"
            )
            
            return {
                "current_volume": current_volume,
                "volume_ratio": volume_ratio,
                "volume_surge": volume_surge,
                "volume_trend": volume_trend,
                "avg_volume_20d": avg_volume_20,
                "interpretation": "관심_증가" if volume_surge else ("관심_감소" if volume_ratio < 0.7 else "보통")
            }
            
        except Exception as e:
            logger.error(f"거래량 패턴 분석 실패: {e}")
            return {}
    
    def _estimate_foreign_influence(self, df: pd.DataFrame) -> Dict:
        """외국인 매매 영향 추정 (거래량 패턴 기반)"""
        try:
            # 대형주는 외국인 영향이 크고, 중소형주는 개인 영향이 큼
            volume_col = 'volume' if 'volume' in df.columns else '거래량'
            price_col = 'close' if 'close' in df.columns else '종가'
            
            volumes = df[volume_col]
            prices = df[price_col]
            
            # 시가총액 추정 (임시)
            current_price = prices.iloc[-1]
            avg_volume = volumes.rolling(20).mean().iloc[-1]
            
            # 거래대금 기준 대형주/중소형주 구분
            trading_value = current_price * avg_volume
            
            if trading_value > 50_000_000_000:  # 500억원 이상
                stock_type = "대형주"
                foreign_influence_weight = 0.7
            elif trading_value > 10_000_000_000:  # 100억원 이상
                stock_type = "중형주"
                foreign_influence_weight = 0.5
            else:
                stock_type = "소형주"
                foreign_influence_weight = 0.3
            
            # 가격-거래량 상관관계로 기관 매매 추정
            recent_corr = prices.tail(10).corr(volumes.tail(10))
            
            institution_signal = "매수세" if recent_corr > 0.5 else (
                "매도세" if recent_corr < -0.5 else "중립"
            )
            
            return {
                "stock_type": stock_type,
                "foreign_influence_weight": foreign_influence_weight,
                "estimated_institution_signal": institution_signal,
                "price_volume_correlation": recent_corr,
                "trading_value_billion": trading_value / 1_000_000_000
            }
            
        except Exception as e:
            logger.error(f"외국인 영향 추정 실패: {e}")
            return {}
    
    def _analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """박스권 vs 돌파 시장 구조 분석"""
        try:
            price_col = 'close' if 'close' in df.columns else '종가'
            prices = df[price_col]
            
            # 최근 30일 가격 범위 분석
            recent_30d = prices.tail(30)
            price_range = recent_30d.max() - recent_30d.min()
            price_center = (recent_30d.max() + recent_30d.min()) / 2
            range_ratio = (price_range / price_center) * 100
            
            # 박스권 판단 (가격 변동폭 10% 이내)
            is_sideways = range_ratio < 10
            
            # 현재 가격 위치
            current_price = prices.iloc[-1]
            position_in_range = ((current_price - recent_30d.min()) / price_range * 100) if price_range > 0 else 50
            
            # 돌파 가능성 (볼린저 밴드 스퀴즈 + 거래량)
            bb_result = self.calculate_korean_bollinger_bands(df)
            bb_squeeze = bb_result.get("korean_analysis", {}).get("squeeze_signal", False)
            
            breakout_probability = 70 if bb_squeeze and is_sideways else (
                30 if is_sideways else 50
            )
            
            return {
                "market_type": "sideways" if is_sideways else "trending",
                "price_range_pct": range_ratio,
                "position_in_range": position_in_range,
                "box_upper": recent_30d.max(),
                "box_lower": recent_30d.min(),
                "breakout_probability": breakout_probability,
                "squeeze_detected": bb_squeeze
            }
            
        except Exception as e:
            logger.error(f"시장 구조 분석 실패: {e}")
            return {}
    
    def _find_korean_support_resistance(self, df: pd.DataFrame) -> Dict:
        """한국 주식 지지/저항선 찾기 (일봉 90일 기준)"""
        try:
            price_col = 'close' if 'close' in df.columns else '종가'
            high_col = 'high' if 'high' in df.columns else '고가'
            low_col = 'low' if 'low' in df.columns else '저가'
            
            # 90일 데이터 사용
            period = min(90, len(df))
            recent_data = df.tail(period)
            
            highs = recent_data[high_col]
            lows = recent_data[low_col]
            closes = recent_data[price_col]
            
            # 지지선: 최근 저점들의 평균
            support_candidates = []
            for i in range(2, len(lows) - 2):
                if (lows.iloc[i] <= lows.iloc[i-1] and lows.iloc[i] <= lows.iloc[i-2] and
                    lows.iloc[i] <= lows.iloc[i+1] and lows.iloc[i] <= lows.iloc[i+2]):
                    support_candidates.append(lows.iloc[i])
            
            # 저항선: 최근 고점들의 평균  
            resistance_candidates = []
            for i in range(2, len(highs) - 2):
                if (highs.iloc[i] >= highs.iloc[i-1] and highs.iloc[i] >= highs.iloc[i-2] and
                    highs.iloc[i] >= highs.iloc[i+1] and highs.iloc[i] >= highs.iloc[i+2]):
                    resistance_candidates.append(highs.iloc[i])
            
            current_price = closes.iloc[-1]
            
            # 유효한 지지/저항선 선택
            valid_supports = [s for s in support_candidates if s < current_price and current_price - s < current_price * 0.15]
            valid_resistances = [r for r in resistance_candidates if r > current_price and r - current_price < current_price * 0.15]
            
            key_support = max(valid_supports) if valid_supports else current_price * 0.95
            key_resistance = min(valid_resistances) if valid_resistances else current_price * 1.05
            
            return {
                "key_support": key_support,
                "key_resistance": key_resistance,
                "support_strength": len(valid_supports),
                "resistance_strength": len(valid_resistances),
                "distance_to_support": ((current_price - key_support) / current_price) * 100,
                "distance_to_resistance": ((key_resistance - current_price) / current_price) * 100
            }
            
        except Exception as e:
            logger.error(f"지지/저항선 분석 실패: {e}")
            return {}
    
    def _calculate_pattern_confidence(self, analysis_results: List[Dict]) -> float:
        """패턴 분석 신뢰도 계산"""
        try:
            confidence_factors = []
            
            for result in analysis_results:
                if isinstance(result, dict):
                    # 각 분석 결과에서 신뢰도 지표 추출
                    if "volume_ratio" in result:
                        # 거래량 비율이 정상 범위 내면 신뢰도 높음
                        vol_conf = min(result["volume_ratio"] * 20, 80) if result["volume_ratio"] > 0.5 else 40
                        confidence_factors.append(vol_conf)
                    
                    if "price_volume_correlation" in result:
                        # 가격-거래량 상관관계가 명확할수록 신뢰도 높음
                        corr_conf = min(abs(result["price_volume_correlation"]) * 100, 90)
                        confidence_factors.append(corr_conf)
            
            # 전체 평균 신뢰도
            return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 50.0
            
        except Exception as e:
            logger.error(f"신뢰도 계산 실패: {e}")
            return 50.0
    
    # ================ 메인 분석 함수 ================
    
    async def analyze_stock(self, ticker: str, analysis_date: datetime = None) -> Dict:
        """개별 종목 종합 기술적 분석"""
        try:
            if analysis_date is None:
                analysis_date = datetime.now(timezone.utc)
            
            # 데이터 조회 (120일치)
            start_date = analysis_date - timedelta(days=self.config["reversal_analysis"]["support_resistance_period"])
            df_list = self.db_manager.get_daily_ohlcv(ticker, start_date, analysis_date)
            
            if not df_list:
                logger.warning(f"종목 {ticker} 데이터 없음")
                return {"success": False, "error": "no_data"}
            
            # DataFrame 변환
            df = pd.DataFrame([{
                "date": item["date"],
                "open": item["ohlcv"]["open"],
                "high": item["ohlcv"]["high"], 
                "low": item["ohlcv"]["low"],
                "close": item["ohlcv"]["close"],
                "volume": item["ohlcv"]["volume"]
            } for item in df_list])
            
            if len(df) < 30:  # 최소 30일 데이터 필요
                return {"success": False, "error": "insufficient_data"}
            
            df = df.set_index('date').sort_index()
            
            # 기술적 지표 계산
            macd_result = self.calculate_korean_macd(df)
            rsi_result = self.calculate_korean_rsi(df)
            bb_result = self.calculate_korean_bollinger_bands(df)
            
            # 한국 특화 패턴 분석
            pattern_result = self.analyze_korean_stock_pattern(df)
            
            # 종합 점수 계산
            technical_score = self._calculate_technical_score({
                "macd": macd_result,
                "rsi": rsi_result,
                "bollinger_bands": bb_result,
                "pattern": pattern_result
            })
            
            # 최종 결과
            analysis_result = {
                "success": True,
                "ticker": ticker,
                "analysis_date": analysis_date.isoformat(),
                "data_period": len(df),
                "indicators": {
                    "macd": macd_result,
                    "rsi": rsi_result,
                    "bollinger_bands": bb_result,
                    "korean_pattern": pattern_result
                },
                "technical_score": technical_score,
                "recommendation": self._generate_recommendation(technical_score, macd_result, rsi_result, pattern_result),
                "confidence": pattern_result.get("pattern_confidence", 50)
            }
            
            logger.debug(f"종목 {ticker} 기술적 분석 완료: 점수 {technical_score}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"종목 {ticker} 기술적 분석 실패: {e}")
            return {"success": False, "error": str(e), "ticker": ticker}
    
    def _calculate_technical_score(self, indicators: Dict) -> float:
        """종합 기술적 점수 계산 (0-100)"""
        try:
            scores = []
            weights = []
            
            # MACD 점수 (가중치 30%)
            if indicators.get("macd", {}).get("korean_analysis"):
                macd_analysis = indicators["macd"]["korean_analysis"]
                if macd_analysis.get("weekly_filter_signal"):
                    macd_score = min(macd_analysis.get("signal_strength", 0), 100)
                    scores.append(macd_score)
                    weights.append(30)
            
            # RSI 점수 (가중치 25%)
            if indicators.get("rsi", {}).get("korean_analysis"):
                rsi_analysis = indicators["rsi"]["korean_analysis"]
                rsi_condition = rsi_analysis.get("market_condition", "중립")
                
                if rsi_condition == "과매도" or rsi_condition == "극도_과매도":
                    rsi_score = 75  # 과매도는 매수 기회
                elif rsi_condition == "과매수" or rsi_condition == "극도_과매수":
                    rsi_score = 25  # 과매수는 매도 기회
                else:
                    rsi_score = 50
                
                scores.append(rsi_score)
                weights.append(25)
            
            # 볼린저 밴드 점수 (가중치 20%)
            if indicators.get("bollinger_bands", {}).get("korean_analysis"):
                bb_analysis = indicators["bollinger_bands"]["korean_analysis"]
                price_position = bb_analysis.get("price_position_pct", 50)
                
                # 하단(매수), 상단(매도) 가중치
                if price_position < 20:
                    bb_score = 80
                elif price_position > 80:
                    bb_score = 20
                else:
                    bb_score = 50
                
                scores.append(bb_score)
                weights.append(20)
            
            # 패턴 점수 (가중치 25%)
            if indicators.get("pattern", {}).get("market_structure"):
                market_structure = indicators["pattern"]["market_structure"]
                volume_pattern = indicators["pattern"].get("volume_pattern", {})
                
                pattern_score = 50  # 기본점수
                
                # 거래량 급증시 가산점
                if volume_pattern.get("volume_surge", False):
                    pattern_score += 15
                
                # 돌파 가능성 반영
                breakout_prob = market_structure.get("breakout_probability", 50)
                pattern_score += (breakout_prob - 50) * 0.3
                
                pattern_score = max(0, min(100, pattern_score))
                scores.append(pattern_score)
                weights.append(25)
            
            # 가중 평균 계산
            if scores and weights:
                weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
                return round(weighted_score, 2)
            else:
                return 50.0  # 기본값
                
        except Exception as e:
            logger.error(f"기술적 점수 계산 실패: {e}")
            return 50.0
    
    def _generate_recommendation(self, technical_score: float, macd_result: Dict, rsi_result: Dict, pattern_result: Dict) -> Dict:
        """기술적 분석 기반 투자 추천"""
        try:
            # 기본 추천 결정
            if technical_score >= 75:
                recommendation = "Strong Buy"
            elif technical_score >= 60:
                recommendation = "Buy" 
            elif technical_score <= 25:
                recommendation = "Strong Sell"
            elif technical_score <= 40:
                recommendation = "Sell"
            else:
                recommendation = "Hold"
            
            # 주요 근거
            reasons = []
            
            # MACD 근거
            macd_analysis = macd_result.get("korean_analysis", {})
            if macd_analysis.get("weekly_filter_signal"):
                reasons.append(f"MACD 반전신호 ({macd_analysis.get('current_phase', '')})")
            
            # RSI 근거  
            rsi_analysis = rsi_result.get("korean_analysis", {})
            rsi_condition = rsi_analysis.get("market_condition", "중립")
            if rsi_condition != "중립":
                reasons.append(f"RSI {rsi_condition} 구간")
            
            # 패턴 근거
            market_structure = pattern_result.get("market_structure", {})
            if market_structure.get("breakout_probability", 0) > 70:
                reasons.append("돌파 임박 신호")
            
            volume_pattern = pattern_result.get("volume_pattern", {})
            if volume_pattern.get("volume_surge", False):
                reasons.append("거래량 급증")
            
            return {
                "signal": recommendation,
                "score": technical_score,
                "reasons": reasons[:3],  # 최대 3개
                "confidence": pattern_result.get("pattern_confidence", 50),
                "risk_level": "High" if technical_score > 80 or technical_score < 20 else "Medium"
            }
            
        except Exception as e:
            logger.error(f"추천 생성 실패: {e}")
            return {
                "signal": "Hold",
                "score": 50,
                "reasons": ["분석 오류"],
                "confidence": 30,
                "risk_level": "High"
            }

# ================ 편의 함수들 ================

async def analyze_korean_stock_technical(ticker: str, analysis_date: datetime = None) -> Dict:
    """한국 주식 기술적 분석 편의 함수"""
    analyzer = KoreanTechnicalAnalyzer()
    return await safe_korean_execution(
        analyzer.analyze_stock,
        ticker,
        analysis_date,
        task_name=f"{ticker}_기술분석"
    )

async def batch_technical_analysis(tickers: List[str], analysis_date: datetime = None) -> Dict[str, Dict]:
    """배치 기술적 분석"""
    analyzer = KoreanTechnicalAnalyzer()
    results = {}
    
    for ticker in tickers:
        try:
            result = await analyzer.analyze_stock(ticker, analysis_date)
            results[ticker] = result
            
            # API 부하 방지를 위한 지연
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"종목 {ticker} 배치 분석 실패: {e}")
            results[ticker] = {"success": False, "error": str(e)}
    
    success_count = sum(1 for r in results.values() if r.get("success", False))
    logger.info(f"배치 기술적 분석 완료: {success_count}/{len(tickers)}")
    
    return results

if __name__ == "__main__":
    async def test_technical_analyzer():
        """기술적 분석기 테스트"""
        analyzer = KoreanTechnicalAnalyzer()
        
        # 테스트용 데이터프레임 생성 (실제 환경에서는 DB에서 가져옴)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        test_df = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(50000, 52000, 100),
            'high': np.random.uniform(52000, 54000, 100),
            'low': np.random.uniform(48000, 50000, 100),
            'close': np.random.uniform(49000, 53000, 100),
            'volume': np.random.uniform(100000, 1000000, 100)
        }).set_index('date')
        
        print("=== 한국 주식 기술적 분석기 테스트 ===")
        
        # MACD 테스트
        macd_result = analyzer.calculate_korean_macd(test_df)
        print(f"MACD 분석: {macd_result.get('korean_analysis', {})}")
        
        # RSI 테스트
        rsi_result = analyzer.calculate_korean_rsi(test_df)
        print(f"RSI 분석: {rsi_result.get('korean_analysis', {})}")
        
        # 패턴 분석 테스트
        pattern_result = analyzer.analyze_korean_stock_pattern(test_df)
        print(f"패턴 분석: {pattern_result}")
    
    # 테스트 실행
    asyncio.run(test_technical_analyzer())