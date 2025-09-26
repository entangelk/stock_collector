"""
AI analysis API routers.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging

from services import ai_service
from schemas import AIAnalysisRequest, AIAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/model-info")
async def get_model_info():
    """Get information about the AI model."""
    try:
        return ai_service.get_model_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/prompts")
async def list_available_prompts():
    """List all available AI analysis prompts."""
    try:
        prompts = ai_service.get_available_prompts()
        return {
            "prompts": prompts,
            "total_count": len(prompts)
        }
    except Exception as e:
        logger.error(f"Failed to list prompts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis", response_model=AIAnalysisResponse)
async def analyze_stocks(request: AIAnalysisRequest):
    """Perform AI analysis on selected stocks."""
    try:
        # Validate AI service availability
        if not ai_service.is_available():
            raise HTTPException(
                status_code=503, 
                detail="AI service is not available. Please check API key configuration."
            )
        
        # Validate tickers
        if not request.tickers:
            raise HTTPException(status_code=400, detail="At least one ticker is required")
        
        if len(request.tickers) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 tickers allowed per request")
        
        # Perform analysis
        result = await ai_service.analyze_stocks(
            tickers=request.tickers,
            prompt_type=request.prompt_type,
            custom_prompt=request.custom_prompt,
            context={"request_source": "api"}
        )
        
        # Check for errors in result
        if "error" in result:
            if "No stock data found" in result["error"]:
                raise HTTPException(status_code=404, detail=result["error"])
            elif "Unknown prompt type" in result["error"]:
                raise HTTPException(status_code=400, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])
        
        # Convert to response model
        response = AIAnalysisResponse(
            analysis_result=result["analysis_result"],
            analyzed_tickers=result["analyzed_tickers"],
            model_used=result["model_used"]
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis")
async def analyze_stocks_get(
    tickers: str = Query(..., description="Comma-separated list of tickers"),
    prompt_type: str = Query("technical_analysis", description="Type of analysis prompt"),
    custom_prompt: Optional[str] = Query(None, description="Custom analysis prompt")
):
    """Perform AI analysis using GET method."""
    try:
        # Parse tickers
        ticker_list = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
        
        if not ticker_list:
            raise HTTPException(status_code=400, detail="At least one ticker is required")
        
        if len(ticker_list) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 tickers allowed per request")
        
        # Create request object
        request = AIAnalysisRequest(
            tickers=ticker_list,
            prompt_type=prompt_type,
            custom_prompt=custom_prompt
        )
        
        # Use POST endpoint logic
        return await analyze_stocks(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis (GET) failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/screener-analysis")
async def analyze_screener_results(
    strategy_name: str,
    prompt_type: str = "trading_opportunity",
    limit: int = Query(5, description="Maximum number of tickers to analyze", ge=1, le=10),
    **strategy_parameters
):
    """Analyze stocks selected by screener strategy."""
    try:
        # Import here to avoid circular imports
        from routers.screener import screen_stocks
        from schemas import ScreenerRequest
        
        # Run screener first
        screener_request = ScreenerRequest(
            strategy_name=strategy_name,
            parameters=strategy_parameters if strategy_parameters else None,
            limit=limit
        )
        
        screener_result = await screen_stocks(screener_request)
        
        if not screener_result.matched_tickers:
            return {
                "message": f"No stocks found using {strategy_name} strategy",
                "strategy_used": strategy_name,
                "parameters": strategy_parameters
            }
        
        # Analyze selected tickers
        analysis_result = await ai_service.analyze_stocks(
            tickers=screener_result.matched_tickers,
            prompt_type=prompt_type,
            context={
                "strategy_used": strategy_name,
                "strategy_parameters": strategy_parameters,
                "screener_execution_time": screener_result.execution_time_ms,
                "total_matches": screener_result.total_matches
            }
        )
        
        # Add screener info to response
        analysis_result["screener_info"] = {
            "strategy_name": strategy_name,
            "total_matches": screener_result.total_matches,
            "analyzed_count": len(screener_result.matched_tickers),
            "execution_time_ms": screener_result.execution_time_ms
        }
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screener analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/custom-analysis")
async def custom_analysis(
    tickers: List[str],
    analysis_request: str,
    context: Optional[Dict[str, Any]] = None
):
    """Perform custom AI analysis with free-form request."""
    try:
        if not ai_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI service is not available"
            )
        
        if len(tickers) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 tickers allowed")
        
        # Create custom prompt
        custom_prompt = f"""다음 종목들에 대해 분석해주세요: {', '.join(tickers)}

분석 요청: {analysis_request}

구체적이고 실용적인 분석을 제공해주세요."""
        
        result = await ai_service.analyze_stocks(
            tickers=tickers,
            custom_prompt=custom_prompt,
            context=context or {}
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")