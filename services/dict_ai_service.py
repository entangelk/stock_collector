"""
딕셔너리 기반 AI 분석 서비스 (Google Gemini)
한국 주식 시장 특화 분석을 위한 AI 서비스
"""
import os
import logging
from typing import List, Optional, Dict, Any
import time
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv

from strategies.dict_base_strategy import DictStrategyManager
from models.dict_models import get_mongodb_client
from prompts.technical_analysis_prompt import create_technical_analysis_prompt
from prompts.market_overview_prompt import create_market_overview_prompt
from prompts.trading_opportunity_prompt import create_trading_opportunity_prompt
from prompts.risk_assessment_prompt import create_risk_assessment_prompt

# 환경변수 로딩
load_dotenv()

logger = logging.getLogger(__name__)


class DictAIAnalysisService:
    """딕셔너리 기반 AI 주식 분석 서비스"""

    def __init__(self):
        self.model = None
        self.strategy_manager = DictStrategyManager()
        self._initialize_model()

    def _initialize_model(self):
        """Gemini 모델 초기화"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key or api_key == "your_gemini_api_key_here":
                logger.warning("Google API key not configured. AI analysis will be unavailable.")
                return

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("✅ Gemini 모델 초기화 성공")

        except Exception as e:
            logger.error(f"❌ Gemini 모델 초기화 실패: {e}")
            self.model = None

    def is_available(self) -> bool:
        """AI 서비스 사용 가능 여부 확인"""
        return self.model is not None

    async def analyze_with_strategy(self,
                                  strategy_name: str,
                                  ticker_list: Optional[List[str]] = None,
                                  limit: int = 10,
                                  analysis_type: str = "detailed") -> Dict[str, Any]:
        """
        전략 기반 주식 분석

        Args:
            strategy_name: 사용할 전략 이름
            ticker_list: 분석할 종목 리스트 (None시 모든 종목)
            limit: 최대 분석 종목 수
            analysis_type: 분석 타입 (detailed, summary, trading_signal)
        """
        start_time = time.time()

        try:
            if not self.is_available():
                return {
                    "success": False,
                    "error": "AI 서비스를 사용할 수 없습니다. API 키를 확인해주세요.",
                    "suggestion": "GOOGLE_API_KEY를 .env 파일에 설정해주세요."
                }

            # 주식 데이터 수집
            stock_data_list = await self._get_stock_data_list(ticker_list, limit)
            if not stock_data_list:
                return {
                    "success": False,
                    "error": "분석할 주식 데이터를 찾을 수 없습니다.",
                    "ticker_list": ticker_list
                }

            # 전략 스크리닝 실행
            strategy_result = self.strategy_manager.screen_stocks(
                strategy_name=strategy_name,
                stock_data_list=stock_data_list,
                limit=limit
            )

            if not strategy_result['success']:
                return {
                    "success": False,
                    "error": f"전략 실행 실패: {strategy_result.get('error')}",
                    "available_strategies": list(self.strategy_manager.strategies.keys())
                }

            # 매치된 종목이 없는 경우
            if strategy_result['matches_found'] == 0:
                return {
                    "success": True,
                    "strategy_result": strategy_result,
                    "ai_analysis": "현재 설정된 조건을 만족하는 종목이 없습니다. 전략 매개변수를 조정하거나 다른 전략을 시도해보세요.",
                    "execution_time": time.time() - start_time
                }

            # AI 분석 실행
            ai_analysis = await self._generate_strategy_analysis(
                strategy_result, analysis_type
            )

            execution_time = time.time() - start_time

            return {
                "success": True,
                "strategy_name": strategy_name,
                "strategy_result": strategy_result,
                "ai_analysis": ai_analysis,
                "analysis_type": analysis_type,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"AI 전략 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "strategy_name": strategy_name,
                "execution_time": time.time() - start_time
            }

    async def analyze_portfolio(self,
                              ticker_list: List[str],
                              analysis_focus: str = "risk_assessment") -> Dict[str, Any]:
        """
        포트폴리오 종합 분석

        Args:
            ticker_list: 분석할 종목 리스트
            analysis_focus: 분석 초점 (risk_assessment, growth_potential, market_timing)
        """
        start_time = time.time()

        try:
            if not self.is_available():
                return self._get_unavailable_response()

            # 모든 전략으로 다중 분석
            strategy_names = list(self.strategy_manager.strategies.keys())
            multi_result = self.strategy_manager.get_multi_strategy_analysis(
                stock_data_list=await self._get_stock_data_list(ticker_list),
                strategy_names=strategy_names,
                limit_per_strategy=20
            )

            # 포트폴리오 AI 분석 생성
            ai_analysis = await self._generate_portfolio_analysis(
                multi_result, ticker_list, analysis_focus
            )

            return {
                "success": True,
                "portfolio_tickers": ticker_list,
                "multi_strategy_result": multi_result,
                "ai_analysis": ai_analysis,
                "analysis_focus": analysis_focus,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"포트폴리오 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "ticker_list": ticker_list
            }

    async def _get_stock_data_list(self,
                                 ticker_list: Optional[List[str]] = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """MongoDB에서 주식 데이터 수집"""
        try:
            client = get_mongodb_client()
            db = client.stock_analyzed

            stock_data_list = []

            if ticker_list:
                # 지정된 종목들만 조회
                for ticker in ticker_list:
                    collection = db[ticker]
                    # 최신 데이터 1개 조회
                    doc = collection.find_one(sort=[("date", -1)])
                    if doc:
                        # MongoDB ObjectId 제거
                        if "_id" in doc:
                            del doc["_id"]
                        stock_data_list.append(doc)
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
                    collection = db[ticker]
                    doc = collection.find_one(sort=[("date", -1)])
                    if doc:
                        if "_id" in doc:
                            del doc["_id"]
                        stock_data_list.append(doc)

            return stock_data_list

        except Exception as e:
            logger.error(f"주식 데이터 수집 실패: {e}")
            return []

    async def _generate_strategy_analysis(self,
                                        strategy_result: Dict[str, Any],
                                        analysis_type: str) -> str:
        """전략 결과 기반 AI 분석 생성"""
        try:
            # 프롬프트 생성
            prompt = self._create_strategy_prompt(strategy_result, analysis_type)

            # AI 분석 생성
            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"AI 분석 생성 실패: {e}")
            return f"AI 분석 생성 중 오류가 발생했습니다: {str(e)}"

    async def _generate_portfolio_analysis(self,
                                         multi_result: Dict[str, Any],
                                         ticker_list: List[str],
                                         analysis_focus: str) -> str:
        """포트폴리오 종합 분석 생성"""
        try:
            prompt = self._create_portfolio_prompt(multi_result, ticker_list, analysis_focus)
            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"포트폴리오 분석 생성 실패: {e}")
            return f"포트폴리오 분석 생성 중 오류가 발생했습니다: {str(e)}"

    def _create_strategy_prompt(self,
                              strategy_result: Dict[str, Any],
                              analysis_type: str) -> str:
        """한국 시장 특화 전략 분석용 프롬프트 생성"""
        # 분석 타입에 따라 적절한 프롬프트 선택
        if analysis_type == "trading_signal":
            return create_trading_opportunity_prompt(strategy_result, "trading_opportunity")
        else:
            return create_technical_analysis_prompt(strategy_result, analysis_type)

    def _create_portfolio_prompt(self,
                               multi_result: Dict[str, Any],
                               ticker_list: List[str],
                               analysis_focus: str) -> str:
        """한국 시장 특화 포트폴리오 분석용 프롬프트 생성"""
        # 분석 초점에 따라 적절한 프롬프트 선택
        if analysis_focus == "risk_assessment":
            return create_risk_assessment_prompt(multi_result, ticker_list, "risk_assessment")
        elif analysis_focus == "market_timing":
            return create_market_overview_prompt(multi_result, ticker_list, "market_timing")
        else:  # growth_potential 또는 기본값
            return create_market_overview_prompt(multi_result, ticker_list, "market_overview")

    def _get_unavailable_response(self) -> Dict[str, Any]:
        """AI 서비스 사용 불가 시 응답"""
        return {
            "success": False,
            "error": "AI 서비스를 사용할 수 없습니다.",
            "suggestion": "GOOGLE_API_KEY를 .env 파일에 설정해주세요.",
            "help_url": "https://makersuite.google.com/app/apikey"
        }

    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 조회"""
        return {
            "service_name": "DictAIAnalysisService",
            "model": "gemini-pro",
            "provider": "Google",
            "is_available": self.is_available(),
            "supported_analysis_types": ["detailed", "summary", "trading_signal"],
            "supported_focus_areas": ["risk_assessment", "growth_potential", "market_timing"],
            "available_strategies": list(self.strategy_manager.strategies.keys()),
            "korean_market_optimized": True
        }


# 전역 AI 서비스 인스턴스
dict_ai_service = DictAIAnalysisService()