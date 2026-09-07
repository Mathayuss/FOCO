from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FOCO API — Ferramenta Operacional de Consolidação de Ocorrências"
    versao_foco: str = "0.3.1"
    ambiente: str = "desenvolvimento"

    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./foco.db"

    cors_origins: str = "http://localhost:5173"
    cors_origin_regex: str = (
        r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|"
        r"192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+|"
        r"100\.\d+\.\d+\.\d+):5173"
    )

    limite_importacao_mb: int = 512

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
