from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # defaults for local dev/tests; override via env in docker-compose/.env
    database_url: str = "postgresql+psycopg://school_billing:school_billing@localhost:5432/school_billing"
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    admin_token_ttl_minutes: int = 60

    admin_username: str = "admin"
    admin_password: str = "change_me"
    service_name: str = "school-billing"


settings = Settings()
