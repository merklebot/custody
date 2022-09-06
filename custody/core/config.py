from pydantic import BaseSettings, Field


class DBSettings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")


class Settings(BaseSettings):
    DB: DBSettings = DBSettings()


settings = Settings()
