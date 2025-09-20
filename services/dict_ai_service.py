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
        """전략 분석용 프롬프트 생성"""
        strategy_name = strategy_result.get('strategy_name', 'Unknown')
        matches_found = strategy_result.get('matches_found', 0)
        results = strategy_result.get('results', [])

        prompt = f"""
당신은 한국 주식 시장 전문 애널리스트입니다. 다음 {strategy_name} 전략 분석 결과를 바탕으로 전문적인 투자 분석을 제공해주세요.

## 전략 분석 결과
- 전략명: {strategy_name}
- 조건 만족 종목 수: {matches_found}개
- 분석 대상: {strategy_result.get('total_analyzed', 0)}개 종목

## 발견된 종목들:
"""

        for i, result in enumerate(results[:5], 1):  # 상위 5개만 분석
            prompt += f"""
{i}. {result.get('ticker', 'N/A')}
   - 신호 강도: {result.get('signal_strength', 0):.3f}
   - 현재가: {result.get('current_price', 0):,}원
   - 분석일: {result.get('date', 'N/A')}
"""

        if analysis_type == "detailed":
            prompt += """
## 요청 분석 내용:
1. 각 종목의 투자 매력도 및 리스크 분석
2. 전략별 시장 상황 해석
3. 진입 시점 및 목표가 제시
4. 한국 시장 특성을 고려한 투자 방향성
5. 포트폴리오 구성 시 고려사항

한국어로 구체적이고 실용적인 분석을 제공해주세요.
"""
        elif analysis_type == "summary":
            prompt += """
## 요청 분석 내용:
간결하게 핵심 투자 포인트와 주요 종목 추천 이유를 한국어로 설명해주세요.
"""
        else:  # trading_signal
            prompt += """
## 요청 분석 내용:
매매 신호 관점에서 각 종목의 진입/청산 타이밍을 한국어로 제시해주세요.
"""

        return prompt

    def _create_portfolio_prompt(self,
                               multi_result: Dict[str, Any],
                               ticker_list: List[str],
                               analysis_focus: str) -> str:
        """포트폴리오 분석용 프롬프트 생성"""
        prompt = f"""
당신은 한국 주식 시장 전문 포트폴리오 매니저입니다. 다음 종목들에 대한 다중 전략 분석 결과를 바탕으로 포트폴리오 관점의 전문 분석을 제공해주세요.

## 분석 대상 종목: {', '.join(ticker_list)}

## 다중 전략 분석 결과:
- 분석된 전략 수: {multi_result.get('strategies_analyzed', 0)}개
- 성공한 전략 수: {multi_result.get('successful_strategies', 0)}개
- 총 발견된 매치: {multi_result.get('total_matches_found', 0)}개

## 전략별 결과:
"""

        for strategy_name, result in multi_result.get('results_by_strategy', {}).items():
            if result.get('success'):
                prompt += f"""
### {strategy_name}
- 조건 만족 종목: {result.get('matches_found', 0)}개
- 상위 종목: {', '.join([r.get('ticker', '') for r in result.get('results', [])[:3]])}
"""

        if analysis_focus == "risk_assessment":
            prompt += """
## 요청 분석 내용 (리스크 중심):
1. 포트폴리오 전체 리스크 프로필 분석
2. 종목간 상관관계 및 분산투자 효과
3. 시장 변동성 대응 방안
4. 손절 및 리스크 관리 전략
"""
        elif analysis_focus == "growth_potential":
            prompt += """
## 요청 분석 내용 (성장성 중심):
1. 각 종목의 성장 잠재력 평가
2. 업종별/테마별 성장성 분석
3. 중장기 투자 관점의 포트폴리오 구성
4. 성장주 vs 가치주 비중 조절 방안
"""
        else:  # market_timing
            prompt += """
## 요청 분석 내용 (타이밍 중심):
1. 현재 시장 상황에서의 진입 타이밍
2. 종목별 매수/매도 시점 제안
3. 시장 사이클 관점의 포트폴리오 조정
4. 단기/중기 투자 전략 구분
"""

        prompt += "\n한국 주식 시장의 특성을 고려하여 한국어로 구체적이고 실용적인 포트폴리오 분석을 제공해주세요."

        return prompt

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