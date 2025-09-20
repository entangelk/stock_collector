"""
딕셔너리 기반 RSI 과매도 전략
한국 주식 시장에 최적화된 RSI 바닥권 매수 전략
"""
from typing import Dict, Any
import logging
from .dict_base_strategy import DictBaseStrategy

logger = logging.getLogger(__name__)


class DictRSIOversoldStrategy(DictBaseStrategy):
    """RSI 과매도 스크리닝 전략 (한국 주식 특화)"""

    def __init__(self):
        super().__init__()
        self.description = "RSI 기반 과매도 구간에서의 반등 매수 기회 탐지 (한국 시장 특화)"

        # 한국 주식 시장 특화 매개변수
        self.parameters = {
            # RSI 기본 조건 (한국 시장 특화)
            "max_rsi": 35,           # 최대 RSI (한국 시장에서 35 이하를 과매도로 판단)
            "min_rsi": 20,           # 최소 RSI (너무 극단적인 상황 제외)
            "optimal_rsi_range": (25, 35),  # 최적 RSI 범위

            # 가격 조건
            "min_price": 2000,       # 최소 주가 (2,000원 이상)
            "max_price": 800000,     # 최대 주가 (80만원 이하)

            # 거래량 조건
            "min_volume": 50000,     # 최소 거래량 (5만주)
            "volume_spike_ratio": 1.2, # 평균 대비 거래량 증가 비율

            # 추세 확인 (중요)
            "require_uptrend": True, # 장기 상승추세 내에서만 적용
            "sma60_filter": True,    # 60일 이평선 위에 있어야 함

            # 기술적 확인 조건
            "macd_support": True,    # MACD 지지 확인
            "bollinger_support": True, # 볼린저 밴드 하단 근처

            # 한국 시장 특화 조건
            "avoid_penny_stocks": True,
            "prefer_stable_stocks": True,
            "korean_trading_hours": True
        }

    def applies_to(self, stock_data: Dict[str, Any]) -> bool:
        """RSI 과매도 조건 확인"""
        if not self.validate_data(stock_data):
            return False

        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        # 1. RSI 필수 확인
        rsi = indicators.get('rsi_14')
        if rsi is None:
            return False

        max_rsi = self.parameters['max_rsi']
        min_rsi = self.parameters['min_rsi']

        # RSI 과매도 범위 확인
        if not (min_rsi <= rsi <= max_rsi):
            return False

        # 2. 가격 조건 확인
        current_price = ohlcv.get('close', 0)
        if not (self.parameters['min_price'] <= current_price <= self.parameters['max_price']):
            return False

        # 3. 거래량 조건 확인
        volume = ohlcv.get('volume', 0)
        if volume < self.parameters['min_volume']:
            return False

        # 4. 장기 상승추세 확인 (중요)
        if self.parameters['require_uptrend']:
            sma60 = indicators.get('sma_60')
            if sma60 is None or current_price < sma60:
                return False

        # 5. 기술적 지지 확인
        if self.parameters['macd_support']:
            if not self._check_macd_support(indicators):
                return False

        # 6. 볼린저 밴드 지지 확인
        if self.parameters['bollinger_support']:
            if not self._check_bollinger_support(stock_data):
                return False

        # 7. 한국 시장 특화 조건
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

        strength_factors = []

        # 1. RSI 과매도 강도 (0.0 ~ 0.3)
        rsi = indicators['rsi_14']
        rsi_strength = self._calculate_rsi_oversold_strength(rsi)
        strength_factors.append(rsi_strength * 0.3)

        # 2. 이동평균 지지 강도 (0.0 ~ 0.25)
        ma_support_strength = self._calculate_ma_support_strength(stock_data)
        strength_factors.append(ma_support_strength * 0.25)

        # 3. MACD 지지 강도 (0.0 ~ 0.2)
        macd_strength = self._calculate_macd_support_strength(indicators)
        strength_factors.append(macd_strength * 0.2)

        # 4. 볼린저 밴드 위치 강도 (0.0 ~ 0.15)
        bb_strength = self._calculate_bollinger_strength(stock_data)
        strength_factors.append(bb_strength * 0.15)

        # 5. 한국 시장 적합성 점수 (0.0 ~ 0.1)
        korean_score = self._calculate_korean_market_score(stock_data)
        strength_factors.append(korean_score * 0.1)

        # 총 신호 강도
        total_strength = sum(strength_factors)

        # 한국 시장 특성 반영 조정
        market_context = self.get_korean_market_context(stock_data)
        if market_context['is_large_cap']:
            total_strength *= 1.1  # 대형주 보너스

        return min(total_strength, 1.0)

    def _calculate_rsi_oversold_strength(self, rsi: float) -> float:
        """RSI 과매도 강도 계산"""
        max_rsi = self.parameters['max_rsi']
        min_rsi = self.parameters['min_rsi']
        optimal_min, optimal_max = self.parameters['optimal_rsi_range']

        if optimal_min <= rsi <= optimal_max:
            # 최적 과매도 범위: 최고 점수
            return 1.0
        elif min_rsi <= rsi < optimal_min:
            # 극과매도: 감점 (너무 위험)
            return 0.7 + (rsi - min_rsi) / (optimal_min - min_rsi) * 0.3
        elif optimal_max < rsi <= max_rsi:
            # 약한 과매도: 감점
            return 1.0 - (rsi - optimal_max) / (max_rsi - optimal_max) * 0.4
        else:
            return 0.3

    def _calculate_ma_support_strength(self, stock_data: Dict[str, Any]) -> float:
        """이동평균 지지 강도 계산"""
        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        current_price = ohlcv.get('close', 0)
        strength = 0.0

        # SMA 20 근접성 (단기 지지)
        sma20 = indicators.get('sma_20')
        if sma20:
            distance_to_sma20 = abs(current_price - sma20) / sma20
            if distance_to_sma20 <= 0.03:  # 3% 이내
                strength += 0.4
            elif distance_to_sma20 <= 0.05:  # 5% 이내
                strength += 0.2

        # SMA 60 위에 위치 (장기 추세 확인)
        sma60 = indicators.get('sma_60')
        if sma60 and current_price > sma60:
            strength += 0.6

        return min(strength, 1.0)

    def _calculate_macd_support_strength(self, indicators: Dict[str, Any]) -> float:
        """MACD 지지 강도 계산"""
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        macd_histogram = indicators.get('macd_histogram')

        if not all([macd is not None, macd_signal is not None, macd_histogram is not None]):
            return 0.5  # 기본값

        strength = 0.0

        # MACD 히스토그램이 상승 전환 중이면 가점
        if macd_histogram > 0:
            strength += 0.4

        # MACD가 시그널선 위에 있으면 가점
        if macd > macd_signal:
            strength += 0.6

        return min(strength, 1.0)

    def _calculate_bollinger_strength(self, stock_data: Dict[str, Any]) -> float:
        """볼린저 밴드 위치 강도 계산"""
        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        bb_lower = indicators.get('bollinger_lower')
        bb_middle = indicators.get('bollinger_middle')

        if not bb_lower or not bb_middle:
            return 0.5

        current_price = ohlcv.get('close', 0)

        # 하단밴드 근처일수록 높은 점수
        if current_price <= bb_lower * 1.02:  # 하단밴드 2% 이내
            return 1.0
        elif current_price <= bb_lower * 1.05:  # 하단밴드 5% 이내
            return 0.7
        elif current_price <= bb_middle:  # 중간선 아래
            return 0.4
        else:
            return 0.2

    def _check_macd_support(self, indicators: Dict[str, Any]) -> bool:
        """MACD 지지 조건 확인"""
        macd_histogram = indicators.get('macd_histogram')
        if macd_histogram is None:
            return True  # 데이터 없으면 통과

        # 히스토그램이 너무 음수가 아니어야 함
        return macd_histogram > -100

    def _check_bollinger_support(self, stock_data: Dict[str, Any]) -> bool:
        """볼린저 밴드 지지 확인"""
        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        bb_lower = indicators.get('bollinger_lower')
        if bb_lower is None:
            return True

        current_price = ohlcv.get('close', 0)
        # 하단밴드 근처이거나 그 위에 있어야 함
        return current_price >= bb_lower * 0.98

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
        if current_price < 5000:
            return False

        # 거래량 너무 적은 주식 제외
        if volume < 30000:
            return False

        return True

    def get_korean_specific_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """한국 시장 특화 분석 정보"""
        if not self.applies_to(stock_data):
            return {}

        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)
        market_context = self.get_korean_market_context(stock_data)

        return {
            "rsi_analysis": {
                "rsi_14": indicators.get('rsi_14'),
                "oversold_strength": self._calculate_rsi_oversold_strength(indicators.get('rsi_14', 50)),
                "in_optimal_range": self.parameters['optimal_rsi_range'][0] <= indicators.get('rsi_14', 50) <= self.parameters['optimal_rsi_range'][1]
            },
            "trend_analysis": {
                "above_sma60": ohlcv.get('close', 0) > indicators.get('sma_60', 0),
                "sma20_distance": abs(ohlcv.get('close', 0) - indicators.get('sma_20', 0)) / indicators.get('sma_20', 1) if indicators.get('sma_20') else None,
                "trend_strength": "strong" if ohlcv.get('close', 0) > indicators.get('sma_60', 0) else "weak"
            },
            "technical_support": {
                "macd_support": self._check_macd_support(indicators),
                "bollinger_support": self._check_bollinger_support(stock_data),
                "support_score": self.get_signal_strength(stock_data)
            },
            "korean_market_fit": {
                "is_large_cap": market_context['is_large_cap'],
                "volume_category": market_context['volume_category'],
                "price_range": market_context['price_range'],
                "overall_score": self.get_signal_strength(stock_data)
            }
        }


# 테스트 함수
def test_dict_rsi_strategy():
    """딕셔너리 기반 RSI 과매도 전략 테스트"""
    print("=== 딕셔너리 기반 RSI 과매도 전략 테스트 ===")

    # 과매도 샘플 데이터
    oversold_data = {
        "ticker": "005930",
        "date": "2024-12-20",
        "ohlcv": {
            "open": 51000,
            "high": 51500,
            "low": 50500,
            "close": 51000,
            "volume": 15000000
        },
        "technical_indicators": {
            "sma_5": 51500,
            "sma_20": 52000,
            "sma_60": 49000,   # 장기 상승추세
            "rsi_14": 28.5,    # 과매도
            "macd": -50.0,
            "macd_signal": -80.0,
            "macd_histogram": 30.0,  # 상승 전환
            "bollinger_upper": 55000,
            "bollinger_middle": 52000,
            "bollinger_lower": 49000
        }
    }

    strategy = DictRSIOversoldStrategy()

    applies = strategy.applies_to(oversold_data)
    print(f"✅ 전략 적용 여부: {applies}")

    if applies:
        strength = strategy.get_signal_strength(oversold_data)
        print(f"✅ 신호 강도: {strength:.3f}")

        analysis = strategy.get_analysis_summary(oversold_data)
        print(f"✅ 분석 요약 완료")

        korean_analysis = strategy.get_korean_specific_analysis(oversold_data)
        print(f"✅ 한국 시장 특화 분석: 완료")

    return applies


if __name__ == "__main__":
    test_dict_rsi_strategy()