"""
딕셔너리 기반 이동평균 교차 전략
한국 주식 시장에 최적화된 골든크로스/데드크로스 전략
"""
from typing import Dict, Any
import logging
from .dict_base_strategy import DictBaseStrategy

logger = logging.getLogger(__name__)


class DictMovingAverageCrossoverStrategy(DictBaseStrategy):
    """이동평균 교차 스크리닝 전략 (한국 주식 특화)"""

    def __init__(self):
        super().__init__()
        self.description = "골든크로스(강세)/데드크로스(약세) 패턴 탐지 (한국 시장 특화)"

        # 한국 주식 시장 특화 매개변수
        self.parameters = {
            # 교차 신호 타입
            "signal_type": "golden_cross",  # "golden_cross", "death_cross", "both"

            # 이동평균 분리 조건
            "min_separation_pct": 1.0,     # 최소 이평선 분리도 (%)
            "max_separation_pct": 8.0,     # 최대 이평선 분리도 (%)

            # 가격 조건
            "min_price": 2000,             # 최소 주가
            "max_price": 1000000,          # 최대 주가

            # 거래량 조건
            "min_volume": 100000,          # 최소 거래량
            "volume_confirmation": True,   # 거래량 확인 요구

            # 추세 확인 조건
            "trend_confirmation": True,    # 추세 확인 요구
            "price_position_weight": 0.3,  # 가격 위치 가중치

            # RSI 확인 조건
            "rsi_filter": True,            # RSI 필터 사용
            "golden_rsi_range": (30, 75),  # 골든크로스 시 RSI 범위
            "death_rsi_range": (25, 70),   # 데드크로스 시 RSI 범위

            # MACD 확인 조건
            "macd_confirmation": True,     # MACD 확인 요구
            "macd_weight": 0.15,          # MACD 가중치

            # 한국 시장 특화
            "avoid_penny_stocks": True,
            "prefer_stable_volume": True,
            "korean_market_hours": True
        }

    def applies_to(self, stock_data: Dict[str, Any]) -> bool:
        """이동평균 교차 조건 확인"""
        if not self.validate_data(stock_data):
            return False

        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        # 1. 이동평균선 필수 확인
        sma20 = indicators.get('sma_20')
        sma60 = indicators.get('sma_60')

        if not sma20 or not sma60:
            return False

        # 2. 가격 조건 확인
        current_price = ohlcv.get('close', 0)
        if not (self.parameters['min_price'] <= current_price <= self.parameters['max_price']):
            return False

        # 3. 이동평균 분리도 확인
        separation_pct = abs(sma20 - sma60) / sma60 * 100
        min_sep = self.parameters['min_separation_pct']
        max_sep = self.parameters['max_separation_pct']

        if not (min_sep <= separation_pct <= max_sep):
            return False

        # 4. 교차 패턴 확인
        signal_type = self.parameters['signal_type']
        has_golden_cross = sma20 > sma60
        has_death_cross = sma20 < sma60

        if signal_type == "golden_cross" and not has_golden_cross:
            return False
        elif signal_type == "death_cross" and not has_death_cross:
            return False
        elif signal_type == "both" and not (has_golden_cross or has_death_cross):
            return False

        # 5. 거래량 확인
        if self.parameters['volume_confirmation']:
            volume = ohlcv.get('volume', 0)
            if volume < self.parameters['min_volume']:
                return False

        # 6. 추세 확인
        if self.parameters['trend_confirmation']:
            if not self._check_trend_confirmation(stock_data, has_golden_cross):
                return False

        # 7. RSI 필터
        if self.parameters['rsi_filter']:
            if not self._check_rsi_filter(indicators, has_golden_cross):
                return False

        # 8. MACD 확인
        if self.parameters['macd_confirmation']:
            if not self._check_macd_confirmation(indicators, has_golden_cross):
                return False

        # 9. 한국 시장 특화 조건
        if self.parameters['avoid_penny_stocks']:
            if not self._is_valid_korean_stock(stock_data):
                return False

        return True

    def get_signal_strength(self, stock_data: Dict[str, Any]) -> float:
        """신호 강도 계산 (0.0 ~ 1.0)"""
        if not self.applies_to(stock_data):
            return 0.0

        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        # 교차 타입 확인
        sma20 = indicators['sma_20']
        sma60 = indicators['sma_60']
        is_golden_cross = sma20 > sma60

        strength_factors = []

        # 1. 이동평균 분리도 강도 (0.0 ~ 0.4)
        separation_strength = self._calculate_separation_strength(indicators)
        strength_factors.append(separation_strength * 0.4)

        # 2. 가격 위치 강도 (0.0 ~ 0.3)
        position_strength = self._calculate_position_strength(stock_data, is_golden_cross)
        strength_factors.append(position_strength * 0.3)

        # 3. RSI 지지 강도 (0.0 ~ 0.15)
        rsi_strength = self._calculate_rsi_strength(indicators, is_golden_cross)
        strength_factors.append(rsi_strength * 0.15)

        # 4. MACD 확인 강도 (0.0 ~ 0.1)
        macd_strength = self._calculate_macd_strength(indicators, is_golden_cross)
        strength_factors.append(macd_strength * 0.1)

        # 5. 한국 시장 적합성 (0.0 ~ 0.05)
        korean_score = self._calculate_korean_market_score(stock_data)
        strength_factors.append(korean_score * 0.05)

        total_strength = sum(strength_factors)

        # 한국 시장 특성 반영
        market_context = self.get_korean_market_context(stock_data)
        if market_context['is_large_cap']:
            total_strength *= 1.1  # 대형주 보너스

        # 거래량 카테고리별 조정
        volume_category = market_context['volume_category']
        if volume_category in ['high', 'very_high']:
            total_strength *= 1.05

        return min(total_strength, 1.0)

    def _calculate_separation_strength(self, indicators: Dict[str, Any]) -> float:
        """이동평균 분리도 강도 계산"""
        sma20 = indicators['sma_20']
        sma60 = indicators['sma_60']

        separation_pct = abs(sma20 - sma60) / sma60 * 100
        min_sep = self.parameters['min_separation_pct']
        max_sep = self.parameters['max_separation_pct']

        # 적당한 분리도일 때 최고점수 (3-5% 범위)
        optimal_min, optimal_max = 3.0, 5.0

        if optimal_min <= separation_pct <= optimal_max:
            return 1.0
        elif min_sep <= separation_pct < optimal_min:
            return 0.6 + (separation_pct - min_sep) / (optimal_min - min_sep) * 0.4
        elif optimal_max < separation_pct <= max_sep:
            return 1.0 - (separation_pct - optimal_max) / (max_sep - optimal_max) * 0.3
        else:
            return 0.3

    def _calculate_position_strength(self, stock_data: Dict[str, Any], is_golden_cross: bool) -> float:
        """가격 위치 강도 계산"""
        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        current_price = ohlcv.get('close', 0)
        sma20 = indicators['sma_20']
        sma60 = indicators['sma_60']

        strength = 0.0

        if is_golden_cross:
            # 골든크로스: 가격이 두 이평선 위에 있을 때 강함
            if current_price > sma20:
                strength += 0.6
            if current_price > sma60:
                strength += 0.4
        else:
            # 데드크로스: 가격이 두 이평선 아래 있을 때 강함
            if current_price < sma20:
                strength += 0.6
            if current_price < sma60:
                strength += 0.4

        return min(strength, 1.0)

    def _calculate_rsi_strength(self, indicators: Dict[str, Any], is_golden_cross: bool) -> float:
        """RSI 지지 강도 계산"""
        rsi = indicators.get('rsi_14')
        if rsi is None:
            return 0.5

        if is_golden_cross:
            rsi_min, rsi_max = self.parameters['golden_rsi_range']
            # 골든크로스에서 RSI 40-70 범위가 최적
            if 40 <= rsi <= 70:
                return 1.0
            elif rsi_min <= rsi < 40:
                return 0.7
            elif 70 < rsi <= rsi_max:
                return 0.6  # 과매수 경계
            else:
                return 0.3
        else:
            rsi_min, rsi_max = self.parameters['death_rsi_range']
            # 데드크로스에서 RSI 30-60 범위가 적합
            if 30 <= rsi <= 60:
                return 1.0
            elif rsi_min <= rsi < 30:
                return 0.6  # 과매도 경계
            elif 60 < rsi <= rsi_max:
                return 0.7
            else:
                return 0.3

    def _calculate_macd_strength(self, indicators: Dict[str, Any], is_golden_cross: bool) -> float:
        """MACD 지지 강도 계산"""
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')

        if not macd or not macd_signal:
            return 0.5

        if is_golden_cross:
            # 골든크로스에서 MACD > Signal이면 강함
            if macd > macd_signal:
                return 1.0
            else:
                return 0.3
        else:
            # 데드크로스에서 MACD < Signal이면 강함
            if macd < macd_signal:
                return 1.0
            else:
                return 0.3

    def _check_trend_confirmation(self, stock_data: Dict[str, Any], is_golden_cross: bool) -> bool:
        """추세 확인"""
        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        current_price = ohlcv.get('close', 0)
        sma20 = indicators.get('sma_20')

        if is_golden_cross:
            # 골든크로스에서는 가격이 단기 이평선 위에 있거나 근처
            return current_price >= sma20 * 0.98
        else:
            # 데드크로스에서는 가격이 단기 이평선 아래 있거나 근처
            return current_price <= sma20 * 1.02

    def _check_rsi_filter(self, indicators: Dict[str, Any], is_golden_cross: bool) -> bool:
        """RSI 필터 확인"""
        rsi = indicators.get('rsi_14')
        if rsi is None:
            return True

        if is_golden_cross:
            rsi_min, rsi_max = self.parameters['golden_rsi_range']
        else:
            rsi_min, rsi_max = self.parameters['death_rsi_range']

        return rsi_min <= rsi <= rsi_max

    def _check_macd_confirmation(self, indicators: Dict[str, Any], is_golden_cross: bool) -> bool:
        """MACD 확인"""
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')

        if not macd or not macd_signal:
            return True  # 데이터 없으면 통과

        if is_golden_cross:
            # 골든크로스에서는 MACD가 너무 음수가 아니면 OK
            return macd > -100
        else:
            # 데드크로스에서는 MACD가 너무 양수가 아니면 OK
            return macd < 100

    def _calculate_korean_market_score(self, stock_data: Dict[str, Any]) -> float:
        """한국 시장 특화 점수 계산"""
        market_context = self.get_korean_market_context(stock_data)
        score = 0.5  # 기본 점수

        # 대형주 보너스
        if market_context['is_large_cap']:
            score += 0.2

        # 적절한 거래량 보너스
        volume_category = market_context['volume_category']
        if volume_category == 'high':
            score += 0.2
        elif volume_category == 'medium':
            score += 0.1

        # 가격대 점수
        price_range = market_context['price_range']
        if price_range in ['medium', 'high']:
            score += 0.1

        return min(score, 1.0)

    def _is_valid_korean_stock(self, stock_data: Dict[str, Any]) -> bool:
        """한국 주식 유효성 검사"""
        ohlcv = self.get_ohlcv_data(stock_data)
        current_price = ohlcv.get('close', 0)
        volume = ohlcv.get('volume', 0)

        # 저가주 제외
        if current_price < 3000:
            return False

        # 거래량 너무 적은 주식 제외
        if volume < 50000:
            return False

        return True

    def get_target_levels(self, stock_data: Dict[str, Any]) -> Dict[str, float]:
        """목표가 및 손절가 계산"""
        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        current_price = ohlcv.get('close', 0)
        sma20 = indicators.get('sma_20')
        sma60 = indicators.get('sma_60')

        is_golden_cross = sma20 > sma60

        if is_golden_cross:
            # 골든크로스: 상승 목표
            return {
                "target_1": current_price * 1.05,  # 5% 상승
                "target_2": current_price * 1.10,  # 10% 상승
                "support": sma20,                  # 20일선 지지
                "stop_loss": sma60                 # 60일선 손절
            }
        else:
            # 데드크로스: 하락 목표
            return {
                "target_1": current_price * 0.95,  # 5% 하락
                "target_2": current_price * 0.90,  # 10% 하락
                "resistance": sma20,               # 20일선 저항
                "stop_loss": sma60                 # 60일선 손절
            }

    def get_korean_specific_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """한국 시장 특화 분석 정보"""
        if not self.applies_to(stock_data):
            return {}

        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)
        market_context = self.get_korean_market_context(stock_data)

        sma20 = indicators.get('sma_20')
        sma60 = indicators.get('sma_60')
        is_golden_cross = sma20 > sma60
        crossover_type = "golden_cross" if is_golden_cross else "death_cross"

        return {
            "crossover_analysis": {
                "type": crossover_type,
                "sma_20": sma20,
                "sma_60": sma60,
                "separation_pct": round(abs(sma20 - sma60) / sma60 * 100, 2),
                "signal_quality": "strong" if self.get_signal_strength(stock_data) > 0.7 else "moderate"
            },
            "price_position": {
                "current_price": ohlcv.get('close'),
                "above_sma20": ohlcv.get('close', 0) > sma20,
                "above_sma60": ohlcv.get('close', 0) > sma60,
                "position_strength": self._calculate_position_strength(stock_data, is_golden_cross)
            },
            "technical_confirmation": {
                "rsi_support": self._check_rsi_filter(indicators, is_golden_cross),
                "macd_confirmation": self._check_macd_confirmation(indicators, is_golden_cross),
                "trend_confirmed": self._check_trend_confirmation(stock_data, is_golden_cross)
            },
            "target_levels": self.get_target_levels(stock_data),
            "korean_market_fit": {
                "is_large_cap": market_context['is_large_cap'],
                "volume_category": market_context['volume_category'],
                "overall_score": self.get_signal_strength(stock_data)
            }
        }


# 테스트 함수
def test_dict_ma_crossover_strategy():
    """딕셔너리 기반 이동평균 교차 전략 테스트"""
    print("=== 딕셔너리 기반 이동평균 교차 전략 테스트 ===")

    # 골든크로스 샘플 데이터
    golden_cross_data = {
        "ticker": "005930",
        "date": "2024-12-20",
        "ohlcv": {
            "open": 53000,
            "high": 53500,
            "low": 52500,
            "close": 53200,
            "volume": 20000000
        },
        "technical_indicators": {
            "sma_5": 53300,
            "sma_20": 52800,   # 단기선이 위
            "sma_60": 51500,   # 장기선이 아래 (골든크로스)
            "rsi_14": 62.0,    # 적정 RSI
            "macd": 120.0,
            "macd_signal": 100.0,
            "macd_histogram": 20.0
        }
    }

    strategy = DictMovingAverageCrossoverStrategy()

    applies = strategy.applies_to(golden_cross_data)
    print(f"✅ 전략 적용 여부: {applies}")

    if applies:
        strength = strategy.get_signal_strength(golden_cross_data)
        print(f"✅ 신호 강도: {strength:.3f}")

        analysis = strategy.get_analysis_summary(golden_cross_data)
        print(f"✅ 분석 요약 완료")

        korean_analysis = strategy.get_korean_specific_analysis(golden_cross_data)
        print(f"✅ 한국 시장 특화 분석: 완료")

        target_levels = strategy.get_target_levels(golden_cross_data)
        print(f"✅ 목표 레벨: {target_levels}")

    return applies


if __name__ == "__main__":
    test_dict_ma_crossover_strategy()