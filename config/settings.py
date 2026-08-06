from functools import lru_cache
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    database_url: str = Field("sqlite:///./job_hunter.db", env="DATABASE_URL")

    linkedin_email: str = Field("", env="LINKEDIN_EMAIL")
    linkedin_password: str = Field("", env="LINKEDIN_PASSWORD")

    indeed_email: str = Field("", env="INDEED_EMAIL")
    indeed_password: str = Field("", env="INDEED_PASSWORD")

    kariyer_email: str = Field("", env="KARIYER_EMAIL")
    kariyer_password: str = Field("", env="KARIYER_PASSWORD")

    bayt_email: str = Field("", env="BAYT_EMAIL")
    bayt_password: str = Field("", env="BAYT_PASSWORD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)
