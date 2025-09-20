"""
딕셔너리 기반 AI 분석 API 라우터
한국 주식 시장 특화 AI 분석 API 제공
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
import logging

from services.dict_ai_service import dict_ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.get("/service-info")
async def get_service_info():
    """AI 서비스 정보 조회"""
    try:
        return dict_ai_service.get_service_info()
    except Exception as e:
        logger.error(f"서비스 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.get("/strategies")
async def list_available_strategies():
    """사용 가능한 전략 목록 조회"""
    try:
        strategies = dict_ai_service.strategy_manager.list_strategies()
        return {
            "success": True,
            "strategies": strategies,
            "total_count": len(strategies),
            "korean_market_optimized": True
        }
    except Exception as e:
        logger.error(f"전략 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.post("/analyze/strategy")
async def analyze_with_strategy(
    strategy_name: str = Body(..., description="사용할 전략 이름"),
    ticker_list: Optional[List[str]] = Body(None, description="분석할 종목 리스트 (None시 전체)"),
    limit: int = Body(10, description="최대 분석 종목 수", ge=1, le=50),
    analysis_type: str = Body("detailed", description="분석 타입")
):
    """
    특정 전략 기반 AI 분석

    Args:
        strategy_name: 전략 이름 (예: dictmacdgoldencrossstrategy)
        ticker_list: 종목 리스트 (예: ["005930", "000660"])
        limit: 최대 종목 수
        analysis_type: detailed, summary, trading_signal 중 선택
    """
    try:
        # 분석 타입 검증
        valid_types = ["detailed", "summary", "trading_signal"]
        if analysis_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 분석 타입: {analysis_type}. 사용 가능: {valid_types}"
            )

        # AI 분석 실행
        result = await dict_ai_service.analyze_with_strategy(
            strategy_name=strategy_name,
            ticker_list=ticker_list,
            limit=limit,
            analysis_type=analysis_type
        )

        if not result.get("success"):
            error_msg = result.get("error", "알 수 없는 오류")
            if "API 키" in error_msg:
                raise HTTPException(status_code=503, detail=error_msg)
            elif "전략" in error_msg and "찾을 수 없습니다" in error_msg:
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=400, detail=error_msg)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전략 기반 AI 분석 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.get("/analyze/strategy")
async def analyze_with_strategy_get(
    strategy_name: str = Query(..., description="사용할 전략 이름"),
    tickers: Optional[str] = Query(None, description="쉼표로 구분된 종목 코드"),
    limit: int = Query(10, description="최대 분석 종목 수", ge=1, le=50),
    analysis_type: str = Query("summary", description="분석 타입")
):
    """GET 방식 전략 기반 AI 분석"""
    try:
        # 종목 파싱
        ticker_list = None
        if tickers:
            ticker_list = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]

        # POST 엔드포인트 로직 재사용
        return await analyze_with_strategy(
            strategy_name=strategy_name,
            ticker_list=ticker_list,
            limit=limit,
            analysis_type=analysis_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET 전략 분석 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.post("/analyze/portfolio")
async def analyze_portfolio(
    ticker_list: List[str] = Body(..., description="포트폴리오 종목 리스트"),
    analysis_focus: str = Body("risk_assessment", description="분석 초점")
):
    """
    포트폴리오 종합 AI 분석

    Args:
        ticker_list: 포트폴리오 종목들 (예: ["005930", "000660", "035420"])
        analysis_focus: risk_assessment, growth_potential, market_timing 중 선택
    """
    try:
        # 종목 수 제한
        if len(ticker_list) > 20:
            raise HTTPException(
                status_code=400,
                detail="포트폴리오 분석은 최대 20개 종목까지 가능합니다"
            )

        if not ticker_list:
            raise HTTPException(status_code=400, detail="최소 1개 종목이 필요합니다")

        # 분석 초점 검증
        valid_focus = ["risk_assessment", "growth_potential", "market_timing"]
        if analysis_focus not in valid_focus:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 분석 초점: {analysis_focus}. 사용 가능: {valid_focus}"
            )

        # 포트폴리오 분석 실행
        result = await dict_ai_service.analyze_portfolio(
            ticker_list=ticker_list,
            analysis_focus=analysis_focus
        )

        if not result.get("success"):
            error_msg = result.get("error", "알 수 없는 오류")
            if "API 키" in error_msg:
                raise HTTPException(status_code=503, detail=error_msg)
            else:
                raise HTTPException(status_code=400, detail=error_msg)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트폴리오 분석 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.post("/analyze/custom")
async def custom_analysis(
    ticker_list: List[str] = Body(..., description="분석할 종목 리스트"),
    analysis_request: str = Body(..., description="분석 요청 내용"),
    context: Optional[Dict[str, Any]] = Body(None, description="추가 컨텍스트")
):
    """
    자유형 AI 분석

    Args:
        ticker_list: 분석할 종목들
        analysis_request: 자연어로 작성된 분석 요청
        context: 추가 정보
    """
    try:
        if not dict_ai_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI 서비스를 사용할 수 없습니다. API 키를 확인해주세요."
            )

        if len(ticker_list) > 10:
            raise HTTPException(status_code=400, detail="최대 10개 종목까지 분석 가능합니다")

        if not analysis_request.strip():
            raise HTTPException(status_code=400, detail="분석 요청 내용을 입력해주세요")

        # 커스텀 프롬프트 생성
        prompt = f"""
한국 주식 시장 전문 애널리스트로서 다음 종목들을 분석해주세요:

## 분석 대상 종목: {', '.join(ticker_list)}

## 분석 요청:
{analysis_request}

## 추가 정보:
{context if context else '없음'}

한국 주식 시장의 특성을 고려하여 구체적이고 실용적인 분석을 한국어로 제공해주세요.
"""

        # AI 분석 생성
        response = dict_ai_service.model.generate_content(prompt)

        return {
            "success": True,
            "ticker_list": ticker_list,
            "analysis_request": analysis_request,
            "ai_analysis": response.text,
            "context": context,
            "analysis_type": "custom"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"커스텀 분석 실패: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.get("/health")
async def health_check():
    """AI 서비스 헬스 체크"""
    try:
        service_info = dict_ai_service.get_service_info()

        return {
            "status": "healthy" if service_info["is_available"] else "unavailable",
            "service_info": service_info,
            "timestamp": "2024-12-20T00:00:00Z"
        }

    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": "2024-12-20T00:00:00Z"
        }


@router.get("/examples")
async def get_usage_examples():
    """API 사용 예시 제공"""
    return {
        "strategy_analysis_example": {
            "url": "/ai/analyze/strategy",
            "method": "POST",
            "body": {
                "strategy_name": "dictmacdgoldencrossstrategy",
                "ticker_list": ["005930", "000660"],
                "limit": 5,
                "analysis_type": "detailed"
            }
        },
        "portfolio_analysis_example": {
            "url": "/ai/analyze/portfolio",
            "method": "POST",
            "body": {
                "ticker_list": ["005930", "000660", "035420"],
                "analysis_focus": "risk_assessment"
            }
        },
        "custom_analysis_example": {
            "url": "/ai/analyze/custom",
            "method": "POST",
            "body": {
                "ticker_list": ["005930"],
                "analysis_request": "현재 매수 타이밍이 적절한지 분석해주세요",
                "context": {"investment_horizon": "3개월"}
            }
        },
        "available_strategies": [
            "dictmacdgoldencrossstrategy",
            "dictrsioversoldstrategy",
            "dictbollingersqueezestrategy",
            "dictmovingaveragecrossoverstrategy"
        ],
        "available_analysis_types": ["detailed", "summary", "trading_signal"],
        "available_focus_areas": ["risk_assessment", "growth_potential", "market_timing"]
    }