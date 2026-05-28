from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_anon_key: str = ""

    # Database — uses SQLite by default for dev, set DATABASE_URL for Postgres
    database_url: str = "sqlite:///./rowing_proj.db"

    # Strava OAuth
    strava_base_url: str = "https://www.strava.com"
    strava_api_base_url: str = "https://www.strava.com/api/v3"
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8000/api/integrations/strava/callback"
    strava_token_encryption_key: str = ""
    strava_approval_prompt: str = "auto"

    # Auth
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Concept2 OAuth
    concept2_client_id: str = ""
    concept2_client_secret: str = ""
    concept2_redirect_uri: str = "http://localhost:8000/api/integrations/concept2/callback"
    concept2_token_encryption_key: str = ""
    concept2_base_url: str = "https://log.concept2.com"

    # App
    environment: str = "development"
    debug: bool = True
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = ""

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


settings = Settings()
