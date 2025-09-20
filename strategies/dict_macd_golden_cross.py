"""
딕셔너리 기반 MACD Golden Cross 전략
한국 주식 시장에 최적화된 MACD 골든크로스 탐지
"""
from typing import Dict, Any
import logging
from .dict_base_strategy import DictBaseStrategy

logger = logging.getLogger(__name__)


class DictMACDGoldenCrossStrategy(DictBaseStrategy):
    """MACD 골든크로스 스크리닝 전략 (한국 주식 특화)"""

    def __init__(self):
        super().__init__()
        self.description = "MACD 라인이 시그널 라인을 상향 돌파하는 강세 신호 탐지 (한국 시장 특화)"

        # 한국 주식 시장 특화 매개변수
        self.parameters = {
            # MACD 기본 조건
            "min_histogram": 50,      # 최소 MACD 히스토그램 값 (한국 주식 가격대 고려)
            "macd_momentum_threshold": 100,  # MACD 모멘텀 임계값

            # 볼륨 조건 (한국 시장 특화)
            "min_volume": 100000,     # 최소 거래량 (10만주)
            "volume_spike_ratio": 1.5, # 평균 대비 거래량 증가 비율

            # RSI 조건 (과매수 방지)
            "max_rsi": 75,            # 최대 RSI (한국 시장에서 75 이상은 과매수)
            "min_rsi": 30,            # 최소 RSI (너무 약한 신호 제외)

            # 가격 조건
            "min_price": 1000,        # 최소 주가 (1,000원 이상)
            "max_price": 1000000,     # 최대 주가 (100만원 이하, 이상은 제외)

            # 이동평균 조건
            "price_above_sma20": True, # 20일 이동평균 위에 있어야 함
            "sma_trending_up": True,   # 이동평균이 상승 추세여야 함

            # 한국 시장 특화 조건
            "avoid_penny_stocks": True, # 저가주 제외
            "prefer_large_cap": True,   # 대형주 선호
            "korean_trading_hours": True # 한국 거래시간 고려
        }

    def applies_to(self, stock_data: Dict[str, Any]) -> bool:
        """MACD 골든크로스 조건 확인"""
        if not self.validate_data(stock_data):
            return False

        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        # 1. 필수 지표 확인
        required_indicators = ['macd', 'macd_signal', 'macd_histogram', 'rsi_14']
        for indicator in required_indicators:
            if indicators.get(indicator) is None:
                logger.debug(f"Missing indicator {indicator} for {stock_data.get('ticker')}")
                return False

        # 2. 기본 MACD 골든크로스 조건
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        macd_histogram = indicators['macd_histogram']

        # MACD가 시그널 위에 있고, 히스토그램이 양수
        macd_above_signal = macd > macd_signal
        histogram_positive = macd_histogram > self.parameters['min_histogram']

        if not (macd_above_signal and histogram_positive):
            return False

        # 3. 가격 조건 확인
        current_price = ohlcv.get('close', 0)
        min_price = self.parameters['min_price']
        max_price = self.parameters['max_price']

        if not (min_price <= current_price <= max_price):
            return False

        # 4. 거래량 조건 확인
        current_volume = ohlcv.get('volume', 0)
        min_volume = self.parameters['min_volume']

        if current_volume < min_volume:
            return False

        # 5. RSI 조건 확인 (과매수/과매도 제외)
        rsi = indicators['rsi_14']
        min_rsi = self.parameters['min_rsi']
        max_rsi = self.parameters['max_rsi']

        if not (min_rsi <= rsi <= max_rsi):
            return False

        # 6. 이동평균 조건 확인
        if self.parameters['price_above_sma20']:
            sma20 = indicators.get('sma_20')
            if sma20 is None or current_price < sma20:
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

        # 1. MACD 모멘텀 강도 (0.0 ~ 0.3)
        macd_histogram = indicators['macd_histogram']
        macd_momentum_score = min(macd_histogram / self.parameters['macd_momentum_threshold'], 1.0)
        strength_factors.append(macd_momentum_score * 0.3)

        # 2. 거래량 강도 (0.0 ~ 0.2)
        volume = ohlcv.get('volume', 0)
        volume_score = min(volume / (self.parameters['min_volume'] * 3), 1.0)
        strength_factors.append(volume_score * 0.2)

        # 3. RSI 최적 범위 (0.0 ~ 0.2)
        rsi = indicators['rsi_14']
        # 50-65 범위가 최적 (강세이지만 과매수 아님)
        optimal_rsi_score = self._calculate_rsi_score(rsi)
        strength_factors.append(optimal_rsi_score * 0.2)

        # 4. 이동평균 위치 (0.0 ~ 0.15)
        sma_score = self._calculate_sma_position_score(stock_data)
        strength_factors.append(sma_score * 0.15)

        # 5. 한국 시장 특화 점수 (0.0 ~ 0.15)
        korean_market_score = self._calculate_korean_market_score(stock_data)
        strength_factors.append(korean_market_score * 0.15)

        # 총 신호 강도 계산
        total_strength = sum(strength_factors)

        # 최종 조정 (한국 시장 특성 반영)
        market_context = self.get_korean_market_context(stock_data)
        if market_context['is_large_cap']:
            total_strength *= 1.1  # 대형주 보너스

        if market_context['volume_category'] in ['high', 'very_high']:
            total_strength *= 1.05  # 고거래량 보너스

        return min(total_strength, 1.0)

    def _calculate_rsi_score(self, rsi: float) -> float:
        """RSI 점수 계산 (50-65가 최적)"""
        if 50 <= rsi <= 65:
            # 최적 범위: 높은 점수
            return 1.0 - abs(rsi - 57.5) / 7.5
        elif 40 <= rsi < 50:
            # 중립 범위: 중간 점수
            return 0.6 + (rsi - 40) / 10 * 0.4
        elif 65 < rsi <= 75:
            # 과매수 경계: 감점
            return 0.8 - (rsi - 65) / 10 * 0.6
        else:
            # 범위 밖: 낮은 점수
            return 0.2

    def _calculate_sma_position_score(self, stock_data: Dict[str, Any]) -> float:
        """이동평균 위치 점수 계산"""
        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        current_price = ohlcv.get('close', 0)
        score = 0.0

        # SMA 5, 20, 60일 순서대로 배열되어 있으면 좋음
        sma5 = indicators.get('sma_5')
        sma20 = indicators.get('sma_20')
        sma60 = indicators.get('sma_60')

        if all(sma is not None for sma in [sma5, sma20, sma60]):
            # 정배열 확인 (현재가 > SMA5 > SMA20 > SMA60)
            if current_price > sma5 > sma20 > sma60:
                score = 1.0
            elif current_price > sma5 > sma20:
                score = 0.8
            elif current_price > sma20:
                score = 0.6
            else:
                score = 0.3

        return score

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

        # 저가주 제외 (5,000원 미만)
        if self.parameters['avoid_penny_stocks'] and current_price < 5000:
            return False

        # 너무 비싼 주식 제외 (100만원 초과)
        if current_price > 1000000:
            return False

        # 거래량이 너무 적은 주식 제외
        volume = ohlcv.get('volume', 0)
        if volume < 50000:  # 5만주 미만
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
            "macd_analysis": {
                "macd": indicators.get('macd'),
                "signal": indicators.get('macd_signal'),
                "histogram": indicators.get('macd_histogram'),
                "momentum_strength": indicators.get('macd_histogram', 0) / self.parameters['macd_momentum_threshold']
            },
            "volume_analysis": {
                "current_volume": ohlcv.get('volume'),
                "volume_category": market_context['volume_category'],
                "meets_min_volume": ohlcv.get('volume', 0) >= self.parameters['min_volume']
            },
            "price_analysis": {
                "current_price": ohlcv.get('close'),
                "price_range": market_context['price_range'],
                "above_sma20": ohlcv.get('close', 0) > indicators.get('sma_20', 0),
                "is_valid_range": self.parameters['min_price'] <= ohlcv.get('close', 0) <= self.parameters['max_price']
            },
            "rsi_analysis": {
                "rsi": indicators.get('rsi_14'),
                "in_optimal_range": self.parameters['min_rsi'] <= indicators.get('rsi_14', 0) <= self.parameters['max_rsi'],
                "signal_quality": "strong" if 50 <= indicators.get('rsi_14', 0) <= 65 else "moderate"
            },
            "korean_market_fit": {
                "is_large_cap": market_context['is_large_cap'],
                "trading_session": market_context['market_session'],
                "overall_score": self.get_signal_strength(stock_data)
            }
        }


# 테스트 함수
def test_dict_macd_strategy():
    """딕셔너리 기반 MACD 전략 테스트"""
    print("=== 딕셔너리 기반 MACD Golden Cross 전략 테스트 ===")

    # 샘플 주식 데이터
    sample_data = {
        "ticker": "005930",
        "date": "2024-12-20",
        "ohlcv": {
            "open": 52700,
            "high": 53100,
            "low": 51900,
            "close": 53000,
            "volume": 24674774
        },
        "technical_indicators": {
            "sma_5": 54160,
            "sma_20": 54725,
            "sma_60": 55200,
            "macd": 150.5,      # 양수 (상승 신호)
            "macd_signal": 120.3, # MACD > Signal
            "macd_histogram": 85.2, # 양수 히스토그램
            "rsi_14": 58.7      # 적정 RSI
        }
    }

    strategy = DictMACDGoldenCrossStrategy()

    # 전략 적용 테스트
    applies = strategy.applies_to(sample_data)
    print(f"✅ 전략 적용 여부: {applies}")

    if applies:
        strength = strategy.get_signal_strength(sample_data)
        print(f"✅ 신호 강도: {strength:.3f}")

        analysis = strategy.get_analysis_summary(sample_data)
        print(f"✅ 분석 요약:")
        print(f"   - 전략: {analysis['strategy']}")
        print(f"   - 현재가: {analysis['current_price']:,}원")
        print(f"   - 거래량: {analysis['volume']:,}주")
        print(f"   - 한국 시장 최적화: {analysis['korean_optimized']}")

        korean_analysis = strategy.get_korean_specific_analysis(sample_data)
        print(f"✅ 한국 시장 특화 분석: 완료")

    return applies


if __name__ == "__main__":
    test_dict_macd_strategy()