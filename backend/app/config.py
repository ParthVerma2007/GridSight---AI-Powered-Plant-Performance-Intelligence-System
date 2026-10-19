from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./plant_data.db"
    
    # AI Provider Settings
    AI_PROVIDER: str = "fallback"  # 'gemini', 'huggingface', 'fallback'
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    HF_TOKEN: str = ""
    HF_MODEL: str = "meta-llama/Llama-3.2-3B-Instruct"
    
    # Plant Defaults (Helios-50 Solar Farm: 50 MW capacity)
    PLANT_ID: str = "helios-50"
    PLANT_NAME: str = "Helios-50 Solar Farm"
    PLANT_CAPACITY_MW: float = 50.0
    PLANT_DEFAULT_LATITUDE: float = 34.0522
    PLANT_DEFAULT_LONGITUDE: float = -117.2437
    PLANT_TIMEZONE: str = "America/Los_Angeles"
    
    # Weather
    WEATHER_CACHE_TTL_SECONDS: int = 3600
    OPEN_METEO_BASE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
    OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
    
    # Financial Defaults
    DEFAULT_PPA_TARIFF: float = 48.50  # $/MWh
    DEFAULT_OM_HOURLY_RATE: float = 125.0  # $/tech-hour
    DEFAULT_CURTAILMENT_COMPENSATION: float = 40.0  # $/MWh

settings = Settings()
