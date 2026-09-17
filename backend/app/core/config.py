from functools import lru_cache

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str
    app_env: str
    database_url: str
    pgvector_enabled: bool
    jwt_secret: SecretStr = Field(default=SecretStr("development-only-change-me"))
    object_storage_endpoint: str
    object_storage_bucket: str
    embedding_model: str
    llm_provider: str
    llm_api_key: SecretStr | None = None
    llm_model: str
    llm_base_url: str
    cors_origins: list[str]
    otel_endpoint: str | None = None
    log_level: str

    @field_validator("app_env")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.lower().strip()

    def validate_production(self) -> None:
        if self.app_env not in {"production", "staging"}:
            return

        missing: list[str] = []
        if (
            self.jwt_secret.get_secret_value() == "development-only-change-me"
            or len(self.jwt_secret.get_secret_value()) < 32
        ):
            missing.append("JWT_SECRET")
        if self.database_url.startswith("postgresql+psycopg://hr_tool:hr_tool@localhost"):
            missing.append("DATABASE_URL")
        if self.llm_provider in {"openai", "azure_openai"} and self.llm_api_key is None:
            missing.append("LLM_API_KEY")
        if missing:
            raise ValueError(
                "Missing or unsafe production settings: " + ", ".join(missing)
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings


def load_settings() -> Settings:
    try:
        return get_settings()
    except (ValidationError, ValueError):
        get_settings.cache_clear()
        raise
