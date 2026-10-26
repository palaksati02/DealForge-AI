import os
from decimal import Decimal
from typing import Optional, List
from pydantic import Field
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
    SECRET_KEY: str = "dealforge-super-secret-key-change-in-production"

    # Authentication & Security
    JWT_SECRET: str = "dealforge-jwt-secret-key-2026-secure"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database Configuration (MySQL 8.x Primary)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "palak@123"
    DB_NAME: str = "dealforge_db"
    DB_ECHO: bool = False
    DATABASE_URL_OVERRIDE: Optional[str] = None

    # LLM Providers
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-70b-8192"
    DEMO_MODE: bool = True

    # Google ADK Service & A2A Protocol
    ADK_SERVICE_HOST: str = "127.0.0.1"
    ADK_SERVICE_PORT: int = 8001
    ADK_TIMEOUT_SECONDS: int = 15
    A2A_BASE_URL: str = "http://127.0.0.1:8000/a2a"

    # MCP Server Configuration
    MCP_SERVER_HOST: str = "127.0.0.1"
    MCP_SERVER_PORT: int = 8002

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

    # CORS Allowed Origins
    CORS_ORIGINS: List[str] = ["*"]

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        import urllib.parse
        encoded_pass = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_pass}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def adk_service_url(self) -> str:
        return f"http://{self.ADK_SERVICE_HOST}:{self.ADK_SERVICE_PORT}"


settings = Settings()
