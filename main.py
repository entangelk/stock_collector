"""
FastAPI application entry point for Stock Collector.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import sys
from pathlib import Path

from config import settings


# Setup logging
def setup_logging():
    """Configure application logging."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.log_file_path).parent
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(settings.log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger = setup_logging()
    logger.info("Starting Stock Collector API server...")
    
    # Initialize database connections
    from database import db_manager
    try:
        db_manager.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
    
    yield
    
    logger.info("Shutting down Stock Collector API server...")
    # Cleanup resources
    if db_manager._client:
        db_manager.disconnect()


# Create FastAPI application
app = FastAPI(
    title="Stock Collector API",
    description="AI-powered Korean stock analysis pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Stock Collector API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    from datetime import datetime
    from database import db_manager
    from services import ai_service
    
    # Check database health
    db_status = "connected" if db_manager.is_connected() else "disconnected"
    
    # Check AI service health
    ai_status = "available" if ai_service.is_available() else "unavailable"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "ai_service": ai_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# Include routers
from routers import stocks, screener, ai_analysis
from routers import dict_screener, dict_ai_analysis

# 기존 Pydantic 기반 라우터들
app.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
app.include_router(screener.router, prefix="/screener-legacy", tags=["screener-legacy"])
app.include_router(ai_analysis.router, prefix="/ai-legacy", tags=["ai-legacy"])

# 새로운 딕셔너리 기반 라우터들 (메인으로 사용)
app.include_router(dict_screener.router, tags=["screener"])
app.include_router(dict_ai_analysis.router, tags=["ai"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )