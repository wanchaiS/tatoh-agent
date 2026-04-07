from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from pathlib import Path

# Resolves to agent_api/static/ regardless of CWD
STATIC_DIR = Path(__file__).parent.parent / "static"
STATIC_URL_PREFIX = "/static"
class Settings(BaseSettings):
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    database_url: str = Field(alias="DATABASE_URL")
    
    pms_base_url: str = Field(alias="PMS_BASE_URL")
    pms_hotel_code: str = Field(alias="PMS_HOTEL_CODE")
    pms_username: str = Field(alias="PMS_USERNAME")
    pms_password: str = Field(alias="PMS_PASSWORD")
    
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")

    open_weather_api_key: Optional[str] = Field(default=None, alias="OPEN_WEATHER_API_KEY")

    # Automatically load from .env file, prioritize OS environment variables
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

settings = Settings()
