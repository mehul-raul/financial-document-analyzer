from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    GOOGLE_API_KEY : str
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")

settings = Settings()


os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
