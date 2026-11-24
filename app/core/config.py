import os
from decimal import Decimal
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "DealForge AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    SECRET_KEY: str = "dealforge-secret-key-change-in-production"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "debug", "dev", "development")
        return bool(v)

    # Database Configuration (MySQL Primary)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "dealforge_db"
    DB_ECHO: bool = False
    DATABASE_URL_OVERRIDE: Optional[str] = None

    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-70b-8192"
    DEMO_MODE: bool = True

    # Google ADK Service & A2A Protocol
    ADK_SERVICE_HOST: str = "127.0.0.1"
    ADK_SERVICE_PORT: int = 8001
    ADK_TIMEOUT_SECONDS: int = 15
    ADK_SERVICE_URL_OVERRIDE: Optional[str] = None

    # Langfuse Cloud & Deployed Tracing Configuration
    LANGFUSE_PUBLIC_KEY: Optional[str] = "pk-lf-dealforge-enterprise-prod-2026"
    LANGFUSE_SECRET_KEY: Optional[str] = "sk-lf-dealforge-enterprise-prod-2026"
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = True

    # Procurement Engine Business Rules
    AUTO_APPROVAL_THRESHOLD: Decimal = Decimal("1000000.00")  # ₹10,00,000
    OVERRUN_TOLERANCE_PERCENTAGE: Decimal = Decimal("0.0")
    DEFAULT_CURRENCY: str = "INR"

    # Configurable Evaluation Scoring Weights (Sum to 1.0)
    WEIGHT_PRICE: Decimal = Decimal("0.35")
    WEIGHT_DELIVERY: Decimal = Decimal("0.20")
    WEIGHT_WARRANTY: Decimal = Decimal("0.15")
    WEIGHT_COMPLIANCE: Decimal = Decimal("0.15")
    WEIGHT_SPECIFICATION: Decimal = Decimal("0.15")

    @property
    def database_url(self) -> str:
        # Standard cloud PaaS environment variable (Render, Railway, Heroku)
        env_db_url = os.environ.get("DATABASE_URL")
        if env_db_url:
            if env_db_url.startswith("postgres://"):
                env_db_url = env_db_url.replace("postgres://", "postgresql://", 1)
            return env_db_url
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        # URL encode password if needed
        import urllib.parse
        encoded_pass = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_pass}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def adk_service_url(self) -> str:
        if self.ADK_SERVICE_URL_OVERRIDE:
            return self.ADK_SERVICE_URL_OVERRIDE
        return f"http://{self.ADK_SERVICE_HOST}:{self.ADK_SERVICE_PORT}"


settings = Settings()
