from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    GOOGLE_API_KEY : str
    SERPER_API_KEY : str
    DATABASE_URL : str
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")

settings = Settings()


os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
os.environ["SERPER_API_KEY"] = settings.SERPER_API_KEY
