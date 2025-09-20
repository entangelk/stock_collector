"""
딕셔너리 기반 주식 스크리너 API 라우터
한국 주식 시장 특화 전략 스크리닝 API 제공
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
import logging

from strategies.dict_base_strategy import DictStrategyManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/screener", tags=["Stock Screener"])

# 전역 전략 관리자
strategy_manager = DictStrategyManager()


@router.get("/strategies")
async def list_strategies():
    """사용 가능한 스크리닝 전략 목록 조회"""
    try:
        strategies = strategy_manager.list_strategies()
        return {
            "success": True,
            "strategies": strategies,
            "total_count": len(strategies),
            "korean_market_optimized": True
        }
    except Exception as e:
        logger.error(f"전략 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.post("/screen")
async def screen_stocks(
    strategy_name: str = Body(..., description="사용할 전략 이름"),
    ticker_list: Optional[List[str]] = Body(None, description="특정 종목만 스크리닝 (None시 전체)"),
    parameters: Optional[Dict[str, Any]] = Body(None, description="전략 매개변수 오버라이드"),
    limit: int = Body(50, description="최대 결과 수", ge=1, le=100)
):
    """
    주식 스크리닝 실행

    Args:
        strategy_name: 전략 이름
        ticker_list: 특정 종목들만 스크리닝 (None시 DB의 모든 종목)
        parameters: 전략 매개변수 커스터마이징
        limit: 최대 결과 개수
    """
    try:
        # 주식 데이터 수집
        stock_data_list = await _get_stock_data_list(ticker_list, limit * 2)  # 여유분 확보

        if not stock_data_list:
            return {
                "success": False,
                "error": "스크리닝할 주식 데이터를 찾을 수 없습니다",
                "ticker_list": ticker_list
            }

        # 스크리닝 실행
        result = strategy_manager.screen_stocks(
            strategy_name=strategy_name,
            stock_data_list=stock_data_list,
            parameters=parameters,
            limit=limit
        )

        if not result["success"]:
            raise HTTPException(
                status_code=404 if "찾을 수 없습니다" in result["error"] else 400,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스크리닝 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.get("/screen")
async def screen_stocks_get(
    strategy_name: str = Query(..., description="사용할 전략 이름"),
    tickers: Optional[str] = Query(None, description="쉼표로 구분된 종목 코드"),
    limit: int = Query(20, description="최대 결과 수", ge=1, le=100)
):
    """GET 방식 주식 스크리닝"""
    try:
        # 종목 파싱
        ticker_list = None
        if tickers:
            ticker_list = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]

        # POST 엔드포인트 로직 재사용
        return await screen_stocks(
            strategy_name=strategy_name,
            ticker_list=ticker_list,
            parameters=None,
            limit=limit
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET 스크리닝 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.post("/multi-strategy")
async def multi_strategy_screen(
    strategy_names: List[str] = Body(..., description="사용할 전략 이름들"),
    ticker_list: Optional[List[str]] = Body(None, description="특정 종목만 스크리닝"),
    limit_per_strategy: int = Body(20, description="전략당 최대 결과 수", ge=1, le=50)
):
    """
    다중 전략 동시 스크리닝

    Args:
        strategy_names: 동시에 실행할 전략들
        ticker_list: 특정 종목들만 분석
        limit_per_strategy: 각 전략당 최대 결과 수
    """
    try:
        if not strategy_names:
            raise HTTPException(status_code=400, detail="최소 1개 전략이 필요합니다")

        if len(strategy_names) > 5:
            raise HTTPException(status_code=400, detail="최대 5개 전략까지 동시 실행 가능합니다")

        # 주식 데이터 수집
        stock_data_list = await _get_stock_data_list(ticker_list, limit_per_strategy * 3)

        if not stock_data_list:
            return {
                "success": False,
                "error": "스크리닝할 주식 데이터를 찾을 수 없습니다"
            }

        # 다중 전략 분석 실행
        result = strategy_manager.get_multi_strategy_analysis(
            stock_data_list=stock_data_list,
            strategy_names=strategy_names,
            limit_per_strategy=limit_per_strategy
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"다중 전략 스크리닝 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.get("/strategy/{strategy_name}")
async def get_strategy_info(strategy_name: str):
    """특정 전략의 상세 정보 조회"""
    try:
        strategy = strategy_manager.get_strategy(strategy_name)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"전략 '{strategy_name}'을 찾을 수 없습니다"
            )

        return {
            "success": True,
            "strategy_info": {
                "name": strategy.name,
                "description": strategy.get_description(),
                "parameters": strategy.get_parameters(),
                "korean_market_optimized": strategy.korean_market_optimized
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전략 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.post("/strategy/{strategy_name}/test")
async def test_strategy(
    strategy_name: str,
    test_data: Dict[str, Any] = Body(..., description="테스트용 주식 데이터")
):
    """
    특정 전략을 테스트 데이터로 테스트

    Args:
        strategy_name: 테스트할 전략 이름
        test_data: 테스트용 주식 데이터 (ticker, date, ohlcv, technical_indicators 포함)
    """
    try:
        strategy = strategy_manager.get_strategy(strategy_name)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"전략 '{strategy_name}'을 찾을 수 없습니다"
            )

        # 데이터 검증
        required_fields = ["ticker", "date", "ohlcv", "technical_indicators"]
        missing_fields = [field for field in required_fields if field not in test_data]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"누락된 필드: {missing_fields}"
            )

        # 전략 테스트
        applies = strategy.applies_to(test_data)
        signal_strength = strategy.get_signal_strength(test_data) if applies else 0.0

        result = {
            "success": True,
            "strategy_name": strategy_name,
            "test_ticker": test_data.get("ticker"),
            "applies": applies,
            "signal_strength": signal_strength,
            "analysis_summary": strategy.get_analysis_summary(test_data) if applies else None
        }

        # 한국 시장 특화 분석 추가
        if applies and hasattr(strategy, 'get_korean_specific_analysis'):
            result["korean_analysis"] = strategy.get_korean_specific_analysis(test_data)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전략 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.get("/examples")
async def get_usage_examples():
    """스크리너 API 사용 예시 제공"""
    return {
        "single_strategy_example": {
            "url": "/screener/screen",
            "method": "POST",
            "body": {
                "strategy_name": "dictmacdgoldencrossstrategy",
                "ticker_list": ["005930", "000660", "035420"],
                "limit": 10
            }
        },
        "multi_strategy_example": {
            "url": "/screener/multi-strategy",
            "method": "POST",
            "body": {
                "strategy_names": [
                    "dictmacdgoldencrossstrategy",
                    "dictrsioversoldstrategy"
                ],
                "limit_per_strategy": 5
            }
        },
        "strategy_test_example": {
            "url": "/screener/strategy/dictmacdgoldencrossstrategy/test",
            "method": "POST",
            "body": {
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
                    "sma_20": 52500,
                    "sma_60": 51000,
                    "macd": 200,
                    "macd_signal": 150,
                    "macd_histogram": 120,
                    "rsi_14": 58
                }
            }
        },
        "available_strategies": [
            "dictmacdgoldencrossstrategy",
            "dictrsioversoldstrategy",
            "dictbollingersqueezestrategy",
            "dictmovingaveragecrossoverstrategy"
        ]
    }


async def _get_stock_data_list(ticker_list: Optional[List[str]] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """MongoDB에서 주식 데이터 수집 (내부 함수)"""
    try:
        from models.dict_models import get_mongodb_client

        client = get_mongodb_client()
        db = client.stock_analyzed

        stock_data_list = []

        if ticker_list:
            # 지정된 종목들만 조회
            for ticker in ticker_list:
                try:
                    collection = db[ticker]
                    # 최신 데이터 1개 조회
                    doc = collection.find_one(sort=[("date", -1)])
                    if doc:
                        # MongoDB ObjectId 제거
                        if "_id" in doc:
                            del doc["_id"]
                        stock_data_list.append(doc)
                except Exception as e:
                    logger.warning(f"종목 {ticker} 데이터 조회 실패: {e}")
                    continue
        else:
            # 시가총액 상위 종목들 조회
            system_db = client.system_info
            target_tickers = system_db.target_tickers

            # 활성 종목 조회 (시가총액 순)
            active_tickers = target_tickers.find(
                {"is_active": True}
            ).sort("market_cap", -1).limit(limit)

            for ticker_doc in active_tickers:
                ticker = ticker_doc["ticker"]
                try:
                    collection = db[ticker]
                    doc = collection.find_one(sort=[("date", -1)])
                    if doc:
                        if "_id" in doc:
                            del doc["_id"]
                        stock_data_list.append(doc)
                except Exception as e:
                    logger.warning(f"종목 {ticker} 데이터 조회 실패: {e}")
                    continue

        return stock_data_list

    except Exception as e:
        logger.error(f"주식 데이터 수집 실패: {e}")
        return []