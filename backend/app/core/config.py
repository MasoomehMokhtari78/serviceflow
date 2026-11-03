from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ServiceFlow"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://serviceflow_user:serviceflow_password@localhost:5432/serviceflow_db"
    
    # Security
    DEV_SECRET_FALLBACK: str = "dev-insecure-secret-key-serviceflow-local-only"
    SECRET_KEY: str = "dev-insecure-secret-key-serviceflow-local-only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # AI Analyst
    GEMINI_API_KEY: str | None = None
    AI_REQUEST_TIMEOUT_SECONDS: float = 6.0
    
    # CORS: Explicit allowed origins, no wildcard with credentials
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:80",
        "http://localhost"
    ]
    
    ENVIRONMENT: str = "development"
    
    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        # Normalize postgres / postgresql URLs to use psycopg2 driver
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        elif self.DATABASE_URL.startswith("postgresql://") and not self.DATABASE_URL.startswith("postgresql+"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

        if self.ENVIRONMENT.lower() == "production":
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == self.DEV_SECRET_FALLBACK
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "FATAL SECURITY CONFIGURATION: Production deployment requires an explicitly configured, strong SECRET_KEY (minimum 32 characters)!"
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
