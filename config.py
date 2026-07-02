from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    BINANCE_URL: str
    COINBASE_URL: str
    KRAKEN_URL: str
    DATABASE_URL: str 
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    @field_validator("BINANCE_URL", "COINBASE_URL", "KRAKEN_URL")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL должен начинаться с http:// или https://")
        return v


settings = Settings()  # type: ignore