from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    save_dir: Path
    mirror_dir: Path
    start_url: str
    allowed_domains: list[str]
    max_threads: int

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()