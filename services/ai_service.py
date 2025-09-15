"""
AI analysis service using Google Gemini.
"""
import logging
from typing import List, Optional, Dict, Any
import time

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from schemas import AnalyzedStockData
from prompts import prompt_manager
from config import settings

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """Service for AI-powered stock analysis using Google Gemini."""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini model."""
        try:
            self.model = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=settings.google_api_key,
                temperature=0.3,
                max_tokens=4000
            )
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self.model is not None
    
    async def analyze_stocks(self, 
                           tickers: List[str], 
                           prompt_type: str = "technical_analysis",
                           custom_prompt: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze stocks using AI.
        
        Args:
            tickers: List of stock tickers to analyze
            prompt_type: Type of analysis prompt to use
            custom_prompt: Custom prompt to use instead of template
            context: Additional context for analysis
        
        Returns:
            Analysis result dictionary
        """
        start_time = time.time()
        
        try:
            if not self.is_available():
                raise ValueError("AI service is not available. Check API key configuration.")
            
            # Get stock data
            stocks_data = await self._get_stocks_data(tickers)
            if not stocks_data:
                return {
                    "error": "No stock data found for the provided tickers",
                    "tickers": tickers
                }
            
            # Generate prompt
            if custom_prompt:
                prompt_text = custom_prompt
                system_message = "You are a professional stock market analyst."
            else:
                prompt_info = prompt_manager.generate_analysis_prompt(
                    prompt_type, stocks_data, context
                )
                if not prompt_info:
                    return {
                        "error": f"Unknown prompt type: {prompt_type}",
                        "available_prompts": [p["name"] for p in prompt_manager.list_prompts()]
                    }
                
                prompt_text = prompt_info["prompt"]
                system_message = prompt_info["system_message"]
            
            # Generate analysis
            analysis_result = await self._generate_analysis(prompt_text, system_message)
            
            execution_time = time.time() - start_time
            
            return {
                "analysis_result": analysis_result,
                "analyzed_tickers": [data.ticker for data in stocks_data],
                "prompt_type": prompt_type,
                "execution_time_seconds": execution_time,
                "model_used": "gemini-pro",
                "context": context or {}
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                "error": str(e),
                "tickers": tickers,
                "prompt_type": prompt_type
            }
    
    async def _get_stocks_data(self, tickers: List[str]) -> List[AnalyzedStockData]:
        """Get analyzed stock data for the given tickers."""
        from database import db_manager
        
        stocks_data = []
        
        for ticker in tickers:
            try:
                # Get most recent analyzed data
                analyzed_collection = db_manager.get_collection("stock_analyzed", ticker)
                
                cursor = analyzed_collection.find().sort("date", -1).limit(1)
                documents = list(cursor)
                
                if not documents:
                    logger.warning(f"No analyzed data found for {ticker}")
                    continue
                
                doc = documents[0]
                
                # Parse dates if they are strings
                if isinstance(doc["date"], str):
                    from datetime import date
                    doc["date"] = date.fromisoformat(doc["date"])
                if isinstance(doc["analysis_timestamp"], str):
                    from datetime import datetime
                    doc["analysis_timestamp"] = datetime.fromisoformat(doc["analysis_timestamp"])
                
                # Convert to AnalyzedStockData
                analyzed_stock_data = AnalyzedStockData(**doc)
                stocks_data.append(analyzed_stock_data)
                
            except Exception as e:
                logger.warning(f"Failed to load data for {ticker}: {e}")
                continue
        
        return stocks_data
    
    async def _generate_analysis(self, prompt_text: str, system_message: str) -> str:
        """Generate analysis using the AI model."""
        try:
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=prompt_text)
            ]
            
            # Generate response
            response = self.model.invoke(messages)
            
            # Extract content from response
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Failed to generate AI analysis: {e}")
            raise
    
    def get_available_prompts(self) -> List[Dict[str, Any]]:
        """Get list of available prompt templates."""
        return prompt_manager.list_prompts()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the AI model."""
        return {
            "model_name": "gemini-pro",
            "provider": "Google",
            "is_available": self.is_available(),
            "max_tokens": 4000,
            "temperature": 0.3,
            "available_prompts": len(prompt_manager.list_prompts())
        }


# Global AI service instance
ai_service = AIAnalysisService()