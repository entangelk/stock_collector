"""
딕셔너리 기반 전략 클래스
Pydantic 우회를 위한 새로운 전략 시스템
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DictBaseStrategy(ABC):
    """딕셔너리 기반 스크리닝 전략 기본 클래스"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = ""
        self.parameters = {}
        self.korean_market_optimized = True  # 한국 시장 특화 표시

    @abstractmethod
    def applies_to(self, stock_data: Dict[str, Any]) -> bool:
        """주어진 주식 데이터에 이 전략이 적용되는지 확인"""
        pass

    @abstractmethod
    def get_signal_strength(self, stock_data: Dict[str, Any]) -> float:
        """신호 강도 계산 (0.0 ~ 1.0, 1.0이 가장 강한 신호)"""
        pass

    def get_description(self) -> str:
        """전략 설명 반환"""
        return self.description or f"{self.name} 스크리닝 전략"

    def get_parameters(self) -> Dict[str, Any]:
        """전략 매개변수 반환"""
        return self.parameters.copy()

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """전략 매개변수 설정"""
        self.parameters.update(parameters)

    def validate_data(self, stock_data: Dict[str, Any]) -> bool:
        """주식 데이터가 필요한 지표를 가지고 있는지 검증"""
        # 필수 필드 확인
        required_fields = ['ticker', 'date', 'ohlcv', 'technical_indicators']

        for field in required_fields:
            if field not in stock_data:
                logger.warning(f"Missing required field: {field}")
                return False

        # OHLCV 데이터 확인
        ohlcv = stock_data.get('ohlcv', {})
        required_ohlcv = ['open', 'high', 'low', 'close', 'volume']

        for field in required_ohlcv:
            if field not in ohlcv:
                logger.warning(f"Missing OHLCV field: {field}")
                return False

        # 기술적 지표 확인 (최소한의 지표)
        indicators = stock_data.get('technical_indicators', {})
        if not indicators:
            logger.warning("Missing technical indicators")
            return False

        return True

    def get_ohlcv_data(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """OHLCV 데이터 추출"""
        return stock_data.get('ohlcv', {})

    def get_technical_indicators(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """기술적 지표 데이터 추출"""
        return stock_data.get('technical_indicators', {})

    def get_korean_market_context(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """한국 시장 특화 컨텍스트 정보"""
        ohlcv = self.get_ohlcv_data(stock_data)

        return {
            "market_session": self._get_market_session(),
            "is_large_cap": self._is_large_cap_stock(stock_data),
            "volume_category": self._categorize_volume(ohlcv.get('volume', 0)),
            "price_range": self._categorize_price_range(ohlcv.get('close', 0))
        }

    def _get_market_session(self) -> str:
        """현재 시장 세션 판단"""
        now = datetime.now()
        hour = now.hour

        if 9 <= hour < 15:
            return "trading"
        elif 15 <= hour < 18:
            return "after_hours"
        else:
            return "closed"

    def _is_large_cap_stock(self, stock_data: Dict[str, Any]) -> bool:
        """대형주 여부 판단 (1조원 이상)"""
        # 실제로는 market_cap 데이터가 필요하지만, 여기서는 추정
        volume = self.get_ohlcv_data(stock_data).get('volume', 0)
        return volume > 1000000  # 100만주 이상 거래량으로 추정

    def _categorize_volume(self, volume: int) -> str:
        """거래량 카테고리 분류"""
        if volume > 10000000:
            return "very_high"
        elif volume > 5000000:
            return "high"
        elif volume > 1000000:
            return "medium"
        elif volume > 100000:
            return "low"
        else:
            return "very_low"

    def _categorize_price_range(self, price: float) -> str:
        """가격대 카테고리 분류"""
        if price > 500000:
            return "premium"  # 50만원 이상
        elif price > 100000:
            return "high"     # 10만원 이상
        elif price > 50000:
            return "medium"   # 5만원 이상
        elif price > 10000:
            return "low"      # 1만원 이상
        else:
            return "penny"    # 1만원 미만

    def get_analysis_summary(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """분석 요약 정보 생성"""
        if not self.applies_to(stock_data):
            return {
                "strategy": self.name,
                "applies": False,
                "signal_strength": 0.0,
                "korean_optimized": self.korean_market_optimized
            }

        signal_strength = self.get_signal_strength(stock_data)
        ohlcv = self.get_ohlcv_data(stock_data)
        market_context = self.get_korean_market_context(stock_data)

        return {
            "strategy": self.name,
            "applies": True,
            "signal_strength": signal_strength,
            "ticker": stock_data.get('ticker'),
            "date": stock_data.get('date'),
            "current_price": ohlcv.get('close'),
            "volume": ohlcv.get('volume'),
            "parameters": self.get_parameters(),
            "korean_optimized": self.korean_market_optimized,
            "market_context": market_context
        }


class DictStrategyManager:
    """딕셔너리 기반 전략 관리자"""

    def __init__(self):
        self.strategies: Dict[str, DictBaseStrategy] = {}
        self._register_default_strategies()

    def register_strategy(self, strategy: DictBaseStrategy) -> None:
        """새로운 전략 등록"""
        self.strategies[strategy.name.lower()] = strategy
        logger.info(f"전략 등록됨: {strategy.name}")

    def get_strategy(self, strategy_name: str) -> Optional[DictBaseStrategy]:
        """이름으로 전략 가져오기"""
        return self.strategies.get(strategy_name.lower())

    def list_strategies(self) -> List[Dict[str, Any]]:
        """사용 가능한 모든 전략 목록 반환"""
        return [
            {
                "name": name,
                "description": strategy.get_description(),
                "parameters": strategy.get_parameters(),
                "korean_optimized": strategy.korean_market_optimized
            }
            for name, strategy in self.strategies.items()
        ]

    def screen_stocks(self, strategy_name: str,
                     stock_data_list: List[Dict[str, Any]],
                     parameters: Optional[Dict[str, Any]] = None,
                     limit: int = 50) -> Dict[str, Any]:
        """지정된 전략으로 주식 스크리닝"""
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return {
                "success": False,
                "error": f"전략 '{strategy_name}'을 찾을 수 없습니다",
                "available_strategies": list(self.strategies.keys())
            }

        # 매개변수 설정
        if parameters:
            strategy.set_parameters(parameters)

        results = []
        errors = []

        for stock_data in stock_data_list:
            try:
                if not strategy.validate_data(stock_data):
                    errors.append(f"{stock_data.get('ticker', 'Unknown')}: 데이터 검증 실패")
                    continue

                if strategy.applies_to(stock_data):
                    analysis = strategy.get_analysis_summary(stock_data)
                    results.append(analysis)

            except Exception as e:
                error_msg = f"{stock_data.get('ticker', 'Unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"스크리닝 오류 - {error_msg}")
                continue

        # 신호 강도로 정렬 (내림차순)
        results.sort(key=lambda x: x["signal_strength"], reverse=True)

        # 결과 제한
        limited_results = results[:limit]

        return {
            "success": True,
            "strategy_name": strategy_name,
            "total_analyzed": len(stock_data_list),
            "matches_found": len(results),
            "results_returned": len(limited_results),
            "results": limited_results,
            "errors": errors[:10],  # 최대 10개 오류만 반환
            "parameters_used": strategy.get_parameters(),
            "korean_market_optimized": strategy.korean_market_optimized
        }

    def get_multi_strategy_analysis(self, stock_data_list: List[Dict[str, Any]],
                                  strategy_names: List[str],
                                  limit_per_strategy: int = 20) -> Dict[str, Any]:
        """여러 전략으로 동시 분석"""
        results = {}

        for strategy_name in strategy_names:
            strategy_result = self.screen_stocks(
                strategy_name,
                stock_data_list,
                limit=limit_per_strategy
            )
            results[strategy_name] = strategy_result

        # 전체 요약
        total_matches = sum(r.get('matches_found', 0) for r in results.values())
        successful_strategies = sum(1 for r in results.values() if r.get('success', False))

        return {
            "success": True,
            "strategies_analyzed": len(strategy_names),
            "successful_strategies": successful_strategies,
            "total_matches_found": total_matches,
            "results_by_strategy": results
        }

    def _register_default_strategies(self) -> None:
        """기본 전략들 등록"""
        # 이후에 구현할 새로운 딕셔너리 기반 전략들
        logger.info("딕셔너리 기반 전략 관리자 초기화 완료")


# 전역 전략 관리자 인스턴스
dict_strategy_manager = DictStrategyManager()


# 유틸리티 함수들
def create_stock_data_dict(ticker: str, date: datetime, ohlcv: Dict[str, Any],
                          technical_indicators: Dict[str, Any],
                          additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """주식 데이터 딕셔너리 생성"""
    stock_data = {
        "ticker": ticker,
        "date": date,
        "ohlcv": ohlcv,
        "technical_indicators": technical_indicators
    }

    if additional_data:
        stock_data.update(additional_data)

    return stock_data


def validate_stock_data_list(stock_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """주식 데이터 리스트 검증"""
    valid_count = 0
    invalid_items = []

    for i, stock_data in enumerate(stock_data_list):
        required_fields = ['ticker', 'date', 'ohlcv', 'technical_indicators']
        missing_fields = [field for field in required_fields if field not in stock_data]

        if missing_fields:
            invalid_items.append({
                "index": i,
                "ticker": stock_data.get('ticker', 'Unknown'),
                "missing_fields": missing_fields
            })
        else:
            valid_count += 1

    return {
        "total_items": len(stock_data_list),
        "valid_items": valid_count,
        "invalid_items": len(invalid_items),
        "invalid_details": invalid_items[:5],  # 처음 5개만
        "validation_rate": valid_count / len(stock_data_list) if stock_data_list else 0
    }