from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения с валидацией URL."""
    
    BINANCE_URL: AnyHttpUrl
    COINBASE_URL: AnyHttpUrl
    KRAKEN_URL: AnyHttpUrl
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Игнорируем лишние переменные в .env
    )


# Создаём экземпляр настроек
settings = Settings() # type: ignore