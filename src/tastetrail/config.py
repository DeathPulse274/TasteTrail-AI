"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DATA_PATH = _PROJECT_ROOT / "data" / "processed" / "restaurants.parquet"


class Settings(BaseSettings):
    """Runtime settings for TasteTrail-AI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_path: Path = Field(
        default=_DEFAULT_DATA_PATH,
        validation_alias="DATA_PATH",
    )
    llm_provider: str = Field(default="groq", validation_alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    llm_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias="LLM_BASE_URL",
    )
    llm_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias="LLM_MODEL",
    )
    max_candidates: int = Field(default=20, validation_alias="MAX_CANDIDATES")
    default_top_n: int = Field(default=5, validation_alias="DEFAULT_TOP_N")
    default_min_rating: float = Field(default=3.0, validation_alias="DEFAULT_MIN_RATING")
    llm_temperature: float = Field(default=0.3, validation_alias="LLM_TEMPERATURE")
    llm_timeout_seconds: float = Field(default=30.0, validation_alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=2, validation_alias="LLM_MAX_RETRIES")

    @field_validator("data_path", mode="before")
    @classmethod
    def _coerce_data_path(cls, value: object) -> Path:
        if value is None or (isinstance(value, str) and not value.strip()):
            return _DEFAULT_DATA_PATH
        return Path(value)

    @field_validator("max_candidates", "default_top_n")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be >= 1")
        return value

    @field_validator("default_min_rating")
    @classmethod
    def _valid_min_rating_default(cls, value: float) -> float:
        if value < 0 or value > 5:
            raise ValueError("default_min_rating must be between 0 and 5")
        return value

    @field_validator("llm_temperature")
    @classmethod
    def _valid_temperature(cls, value: float) -> float:
        if value < 0 or value > 2:
            raise ValueError("llm_temperature must be between 0 and 2")
        return value

    @field_validator("llm_timeout_seconds")
    @classmethod
    def _valid_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("llm_timeout_seconds must be positive")
        return value

    @field_validator("llm_max_retries")
    @classmethod
    def _valid_retries(cls, value: int) -> int:
        if value < 0:
            raise ValueError("llm_max_retries must be >= 0")
        return value

    @model_validator(mode="after")
    def _clamp_top_n_to_candidates(self) -> Self:
        if self.default_top_n > self.max_candidates:
            object.__setattr__(self, "default_top_n", self.max_candidates)
        return self

    def require_llm_api_key(self) -> str:
        """Return API key or raise with a clear message (Phase 2+ LLM calls)."""
        if not self.llm_api_key.strip():
            raise ValueError(
                "LLM_API_KEY is not set. Copy .env.example to .env and add your Groq API key "
                "(https://console.groq.com/keys)."
            )
        return self.llm_api_key

    def required_env_vars_for_llm(self) -> list[str]:
        """Environment variables needed before calling the LLM."""
        return ["LLM_API_KEY", "LLM_PROVIDER", "LLM_MODEL"]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
