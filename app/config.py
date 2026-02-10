from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://leads:leads@localhost:5432/leads"
    SECRET_KEY: str = "change-me-to-a-random-secret"
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin"
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@example.com"
    ATTORNEY_EMAIL: str = "attorney@example.com"
    UPLOAD_DIR: str = "uploads/resumes"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
