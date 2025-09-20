"""
딕셔너리 기반 볼린저 스퀴즈 전략
한국 주식 시장에 최적화된 변동성 수축 후 돌파 전략
"""
from typing import Dict, Any
import logging
from .dict_base_strategy import DictBaseStrategy

logger = logging.getLogger(__name__)


class DictBollingerSqueezeStrategy(DictBaseStrategy):
    """볼린저 스퀴즈 스크리닝 전략 (한국 주식 특화)"""

    def __init__(self):
        super().__init__()
        self.description = "변동성 수축(스퀴즈) 후 돌파 가능성이 높은 종목 탐지 (한국 시장 특화)"

        # 한국 주식 시장 특화 매개변수
        self.parameters = {
            # 볼린저 밴드 스퀴즈 조건
            "max_band_width_pct": 8.0,    # 최대 밴드폭 (중간선 대비 %)
            "ideal_band_width_pct": 5.0,  # 이상적인 밴드폭
            "min_squeeze_duration": 3,     # 최소 스퀴즈 지속 일수

            # 가격 위치 조건
            "max_distance_from_middle": 0.02,  # 중간선에서 최대 거리 (2%)
            "consolidation_required": True,     # 횡보 패턴 요구

            # 거래량 조건 (스퀴즈 시 거래량 감소 특성)
            "max_volume_ratio": 0.8,      # 평균 대비 최대 거래량 비율
            "min_volume": 100000,         # 최소 절대 거래량

            # 가격 조건
            "min_price": 3000,            # 최소 주가
            "max_price": 500000,          # 최대 주가

            # RSI 중립성 조건
            "rsi_neutral_range": (40, 60), # RSI 중립 범위
            "require_rsi_neutral": True,   # RSI 중립성 요구

            # 이동평균 수렴 조건
            "ma_convergence_threshold": 0.03, # 이평선 수렴 임계값 (3%)
            "require_ma_convergence": True,    # 이평선 수렴 요구

            # 한국 시장 특화
            "avoid_penny_stocks": True,
            "prefer_stable_stocks": True,
            "korean_trading_hours": True
        }

    def applies_to(self, stock_data: Dict[str, Any]) -> bool:
        """볼린저 스퀴즈 조건 확인"""
        if not self.validate_data(stock_data):
            return False

        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        # 1. 볼린저 밴드 필수 확인
        bb_upper = indicators.get('bollinger_upper')
        bb_middle = indicators.get('bollinger_middle')
        bb_lower = indicators.get('bollinger_lower')

        if not all([bb_upper, bb_middle, bb_lower]):
            return False

        # 2. 밴드폭 스퀴즈 확인
        band_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100
        max_band_width = self.parameters['max_band_width_pct']

        if band_width_pct > max_band_width:
            return False

        # 3. 가격 조건 확인
        current_price = ohlcv.get('close', 0)
        if not (self.parameters['min_price'] <= current_price <= self.parameters['max_price']):
            return False

        # 4. 횡보 패턴 확인 (가격이 중간선 근처)
        if self.parameters['consolidation_required']:
            distance_from_middle = abs(current_price - bb_middle) / bb_middle
            if distance_from_middle > self.parameters['max_distance_from_middle']:
                return False

        # 5. 거래량 조건 확인 (스퀴즈 시 거래량 감소)
        volume = ohlcv.get('volume', 0)
        if volume < self.parameters['min_volume']:
            return False

        # 6. RSI 중립성 확인
        if self.parameters['require_rsi_neutral']:
            rsi = indicators.get('rsi_14')
            if rsi is not None:
                rsi_min, rsi_max = self.parameters['rsi_neutral_range']
                if not (rsi_min <= rsi <= rsi_max):
                    return False

        # 7. 이동평균 수렴 확인
        if self.parameters['require_ma_convergence']:
            if not self._check_ma_convergence(indicators):
                return False

        # 8. 한국 시장 특화 조건
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

        # 1. 밴드폭 스퀴즈 강도 (0.0 ~ 0.4)
        squeeze_strength = self._calculate_squeeze_strength(indicators)
        strength_factors.append(squeeze_strength * 0.4)

        # 2. 가격 위치 강도 (0.0 ~ 0.25)
        position_strength = self._calculate_position_strength(stock_data)
        strength_factors.append(position_strength * 0.25)

        # 3. RSI 중립성 강도 (0.0 ~ 0.15)
        rsi_strength = self._calculate_rsi_neutrality_strength(indicators)
        strength_factors.append(rsi_strength * 0.15)

        # 4. 이동평균 수렴 강도 (0.0 ~ 0.1)
        ma_convergence_strength = self._calculate_ma_convergence_strength(indicators)
        strength_factors.append(ma_convergence_strength * 0.1)

        # 5. 한국 시장 적합성 (0.0 ~ 0.1)
        korean_score = self._calculate_korean_market_score(stock_data)
        strength_factors.append(korean_score * 0.1)

        total_strength = sum(strength_factors)

        # 한국 시장 특성 반영
        market_context = self.get_korean_market_context(stock_data)
        if market_context['is_large_cap']:
            total_strength *= 1.05  # 대형주 소폭 보너스

        return min(total_strength, 1.0)

    def _calculate_squeeze_strength(self, indicators: Dict[str, Any]) -> float:
        """스퀴즈 강도 계산 (밴드폭이 좁을수록 강함)"""
        bb_upper = indicators.get('bollinger_upper')
        bb_middle = indicators.get('bollinger_middle')
        bb_lower = indicators.get('bollinger_lower')

        band_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100
        max_band_width = self.parameters['max_band_width_pct']
        ideal_band_width = self.parameters['ideal_band_width_pct']

        if band_width_pct <= ideal_band_width:
            # 이상적인 스퀴즈: 최고 점수
            return 1.0
        else:
            # 넓어질수록 점수 감소
            return max(0.0, 1.0 - (band_width_pct - ideal_band_width) / (max_band_width - ideal_band_width))

    def _calculate_position_strength(self, stock_data: Dict[str, Any]) -> float:
        """가격 위치 강도 계산 (중간선에 가까울수록 강함)"""
        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)

        current_price = ohlcv.get('close', 0)
        bb_middle = indicators.get('bollinger_middle')

        if not bb_middle:
            return 0.5

        distance_from_middle = abs(current_price - bb_middle) / bb_middle
        max_distance = self.parameters['max_distance_from_middle']

        # 중간선에 가까울수록 높은 점수
        return max(0.0, 1.0 - (distance_from_middle / max_distance))

    def _calculate_rsi_neutrality_strength(self, indicators: Dict[str, Any]) -> float:
        """RSI 중립성 강도 계산"""
        rsi = indicators.get('rsi_14')
        if rsi is None:
            return 0.5

        rsi_min, rsi_max = self.parameters['rsi_neutral_range']
        rsi_center = (rsi_min + rsi_max) / 2

        # RSI 50 (중립)에 가까울수록 높은 점수
        distance_from_center = abs(rsi - rsi_center)
        max_distance = (rsi_max - rsi_min) / 2

        return max(0.0, 1.0 - (distance_from_center / max_distance))

    def _calculate_ma_convergence_strength(self, indicators: Dict[str, Any]) -> float:
        """이동평균 수렴 강도 계산"""
        sma20 = indicators.get('sma_20')
        sma60 = indicators.get('sma_60')

        if not sma20 or not sma60:
            return 0.5

        convergence = abs(sma20 - sma60) / sma60
        threshold = self.parameters['ma_convergence_threshold']

        if convergence <= threshold:
            # 수렴할수록 높은 점수
            return 1.0 - (convergence / threshold) * 0.5
        else:
            return 0.2  # 수렴하지 않으면 낮은 점수

    def _check_ma_convergence(self, indicators: Dict[str, Any]) -> bool:
        """이동평균 수렴 확인"""
        sma20 = indicators.get('sma_20')
        sma60 = indicators.get('sma_60')

        if not sma20 or not sma60:
            return True  # 데이터 없으면 통과

        convergence = abs(sma20 - sma60) / sma60
        return convergence <= self.parameters['ma_convergence_threshold']

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
        if volume < 50000:
            return False

        return True

    def get_breakout_levels(self, stock_data: Dict[str, Any]) -> Dict[str, float]:
        """돌파 레벨 계산"""
        indicators = self.get_technical_indicators(stock_data)

        bb_upper = indicators.get('bollinger_upper')
        bb_lower = indicators.get('bollinger_lower')
        bb_middle = indicators.get('bollinger_middle')

        return {
            "upper_breakout": bb_upper,      # 상향 돌파 레벨
            "lower_breakdown": bb_lower,     # 하향 돌파 레벨
            "middle_line": bb_middle,        # 중간선 (균형점)
            "stop_loss_upper": bb_middle,    # 상향 돌파 시 손절
            "stop_loss_lower": bb_middle     # 하향 돌파 시 손절
        }

    def get_korean_specific_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """한국 시장 특화 분석 정보"""
        if not self.applies_to(stock_data):
            return {}

        ohlcv = self.get_ohlcv_data(stock_data)
        indicators = self.get_technical_indicators(stock_data)
        market_context = self.get_korean_market_context(stock_data)

        # 밴드폭 계산
        bb_upper = indicators.get('bollinger_upper')
        bb_middle = indicators.get('bollinger_middle')
        bb_lower = indicators.get('bollinger_lower')
        band_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100 if bb_middle else 0

        return {
            "squeeze_analysis": {
                "band_width_pct": round(band_width_pct, 2),
                "squeeze_strength": self._calculate_squeeze_strength(indicators),
                "is_tight_squeeze": band_width_pct <= self.parameters['ideal_band_width_pct']
            },
            "position_analysis": {
                "current_price": ohlcv.get('close'),
                "distance_from_middle_pct": round(abs(ohlcv.get('close', 0) - bb_middle) / bb_middle * 100, 2) if bb_middle else 0,
                "near_middle_line": abs(ohlcv.get('close', 0) - bb_middle) / bb_middle <= 0.01 if bb_middle else False
            },
            "neutrality_analysis": {
                "rsi_14": indicators.get('rsi_14'),
                "rsi_neutral": self.parameters['rsi_neutral_range'][0] <= indicators.get('rsi_14', 50) <= self.parameters['rsi_neutral_range'][1],
                "ma_convergence": self._check_ma_convergence(indicators)
            },
            "breakout_levels": self.get_breakout_levels(stock_data),
            "korean_market_fit": {
                "is_large_cap": market_context['is_large_cap'],
                "volume_category": market_context['volume_category'],
                "overall_score": self.get_signal_strength(stock_data)
            }
        }


# 테스트 함수
def test_dict_bollinger_strategy():
    """딕셔너리 기반 볼린저 스퀴즈 전략 테스트"""
    print("=== 딕셔너리 기반 볼린저 스퀴즈 전략 테스트 ===")

    # 스퀴즈 샘플 데이터
    squeeze_data = {
        "ticker": "000660",
        "date": "2024-12-20",
        "ohlcv": {
            "open": 168000,
            "high": 169000,
            "low": 167000,
            "close": 168500,  # 중간선 근처
            "volume": 800000   # 적당한 거래량
        },
        "technical_indicators": {
            "sma_5": 168200,
            "sma_20": 168000,
            "sma_60": 167500,  # 수렴 상태
            "rsi_14": 52.0,    # 중립
            "macd": 10.0,
            "macd_signal": 8.0,
            "macd_histogram": 2.0,
            "bollinger_upper": 172000,    # 좁은 밴드폭
            "bollinger_middle": 168500,
            "bollinger_lower": 165000
        }
    }

    strategy = DictBollingerSqueezeStrategy()

    applies = strategy.applies_to(squeeze_data)
    print(f"✅ 전략 적용 여부: {applies}")

    if applies:
        strength = strategy.get_signal_strength(squeeze_data)
        print(f"✅ 신호 강도: {strength:.3f}")

        analysis = strategy.get_analysis_summary(squeeze_data)
        print(f"✅ 분석 요약 완료")

        korean_analysis = strategy.get_korean_specific_analysis(squeeze_data)
        print(f"✅ 한국 시장 특화 분석: 완료")

        breakout_levels = strategy.get_breakout_levels(squeeze_data)
        print(f"✅ 돌파 레벨: {breakout_levels}")

    return applies


if __name__ == "__main__":
    test_dict_bollinger_strategy()