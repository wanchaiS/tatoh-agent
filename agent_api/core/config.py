from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")

    open_weather_api_key: str | None = Field(default=None, alias="OPEN_WEATHER_API_KEY")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=10, alias="JWT_EXPIRE_MINUTES")

    @property
    def admin_users(self) -> dict[str, str]:
        """Return {username: bcrypt_hash} from ADMIN_USER_* env vars."""
        import os
        prefix = "admin_user_"
        env_vars = {**(self.model_extra or {}), **os.environ}
        return {
            key[len(prefix):].lower(): value
            for key, value in env_vars.items()
            if key.lower().startswith(prefix)
        }

    # Automatically load from .env file, prioritize OS environment variables
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='allow')

settings = Settings()
