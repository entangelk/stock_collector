"""
Configuration management for Stock Collector application.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import pytz


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_system_db: str = Field(default="system_info", env="MONGODB_SYSTEM_DB")
    mongodb_stock_data_db: str = Field(default="stock_data", env="MONGODB_STOCK_DATA_DB")
    mongodb_analyzed_db: str = Field(default="stock_analyzed", env="MONGODB_ANALYZED_DB")
    
    # Google Gemini API Configuration
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    
    # Server Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file_path: str = Field(default="./logs/app.log", env="LOG_FILE_PATH")
    
    # Stock Analysis Configuration
    min_market_cap: int = Field(default=100_000_000_000, env="MIN_MARKET_CAP")  # 1000억원
    max_analysis_per_hour: int = Field(default=50, env="MAX_ANALYSIS_PER_HOUR")
    analysis_time_limit_minutes: int = Field(default=50, env="ANALYSIS_TIME_LIMIT_MINUTES")
    
    # Timezone Configuration
    timezone: str = Field(default="Asia/Seoul", env="TIMEZONE")
    
    # Cron Job Configuration
    daily_update_time: str = Field(default="19:00", env="DAILY_UPDATE_TIME")
    analysis_start_time: str = Field(default="19:10", env="ANALYSIS_START_TIME")
    analysis_end_time: str = Field(default="08:10", env="ANALYSIS_END_TIME")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def kst_timezone(self):
        """Get Korean Standard Time timezone object."""
        return pytz.timezone(self.timezone)
    
    def get_database_names(self) -> dict:
        """Get all database names as a dictionary."""
        return {
            "system_info": self.mongodb_system_db,
            "stock_data": self.mongodb_stock_data_db,
            "stock_analyzed": self.mongodb_analyzed_db
        }


# Global settings instance
settings = Settings()