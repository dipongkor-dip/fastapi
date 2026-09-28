from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    access_token_expire_minutes: int = 30  # with a default fallback

    superadmin_username: str
    superadmin_email: str
    superadmin_firstname: str
    superadmin_lastname: str
    superadmin_password: str

    email_sender: str
    email_password: str

    upstash_redis_rest_url: str
    upstash_redis_rest_token: str

    # SSLCommerz
    sslcommerz_store_id: str
    sslcommerz_store_password: str
    sslcommerz_base_url: str

    # Application
    backend_url: str
    frontend_url: str

    google_client_id: str = ""
    google_client_secret: str = ""
    
    facebook_client_id: str = ""
    facebook_client_secret: str = ""

    # Cloudinary
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
