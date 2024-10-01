from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    save_dir: str
    save_file: str
    start_url: str
    allowed_domains: str
    max_threads: int

    @property
    def Allowed_domains(self):
        return self.allowed_domains.split(',')

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()