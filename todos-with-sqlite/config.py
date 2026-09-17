from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    access_token_expire_minutes: int = 30  # with a default fallback

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Instantiate the settings so it can be imported across your app
settings = Settings()