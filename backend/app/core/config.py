"""
ArgusCX — Application Configuration
Reads all settings from environment variables (.env)
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App Core ──────────────────────────────
    APP_NAME: str = "ArgusCX"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_SECRET_KEY: str = "change-me-in-production"
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ── Frontend ──────────────────────────────
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_WS_URL: str = "ws://localhost:8000/ws"
    NEXT_PUBLIC_DEMO_MODE: bool = False

    # ── Auth ──────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Groq (Primary LLM — Free Tier) ───────
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── Agent Config ──────────────────────────
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 60
    AGENT_CONFIDENCE_THRESHOLD: float = 0.75
    AGENT_FRAUD_RISK_THRESHOLD: float = 0.65
    AGENT_AUTO_RESOLVE_THRESHOLD: float = 0.85

    # ── ArgusCX Platform ─────────────────────
    ARGUSCX_MASTER_KEY: str = "acx_master_2026_hackathon"
    GUARDRAILS_ENABLED: bool = True
    PREPROCESSOR_ENABLED: bool = True

    # ── External Integrations (Optional) ──────
    SHOPIFY_ACCESS_TOKEN: Optional[str] = None
    SHOPIFY_SHOP_DOMAIN: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None

    # ── PostgreSQL ────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "arguscx"
    POSTGRES_USER: str = "arguscx_user"
    POSTGRES_PASSWORD: str = "arguscx_password"
    DATABASE_URL: str = "postgresql+asyncpg://arguscx_user:arguscx_password@localhost:5432/arguscx"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── MongoDB ───────────────────────────────
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "arguscx_logs"
    MONGO_USER: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_AUTH_SOURCE: str = "admin"
    # ── Redis ─────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Celery ─────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # ── Fraud Detection ───────────────────────
    C2PA_VERIFICATION_ENABLED: bool = True
    EXIF_CHECK_ENABLED: bool = True
    AI_ARTIFACT_DETECTION_ENABLED: bool = True

    # ── Local File Storage ────────────────────
    UPLOAD_DIR: str = "uploads"

    # ── Sentry ────────────────────────────────
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ── Prometheus ────────────────────────────
    METRICS_ENABLED: bool = True

    # ── Logging ───────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/arguscx.log"
    AUDIT_LOG_ENABLED: bool = True

    # ── Feature Flags ─────────────────────────
    FEATURE_MULTIMODAL_ENABLED: bool = True
    FEATURE_VOICE_CHANNEL_ENABLED: bool = False
    FEATURE_ANALYTICS_ENABLED: bool = True
    FEATURE_FRAUD_DETECTION_ENABLED: bool = True
    FEATURE_AUTO_RESOLVE_ENABLED: bool = True
    FEATURE_HUMAN_LOOP_ENABLED: bool = True
    FEATURE_PREDICTIVE_CHURN_ENABLED: bool = False

    @property
    def is_demo_mode(self) -> bool:
        return not self.GROQ_API_KEY

    @property
    def active_llm_provider(self) -> str:
        if self.GROQ_API_KEY:
            return "groq"
        return "none"

    @property
    def active_connectors(self) -> list:
        connectors = []
        if self.SHOPIFY_ACCESS_TOKEN:
            connectors.append("shopify_live")
        else:
            connectors.append("shopify_llm")
        if self.STRIPE_SECRET_KEY:
            connectors.append("stripe_live")
        if self.RAZORPAY_KEY_ID:
            connectors.append("razorpay_live")
        else:
            connectors.append("razorpay_llm")
        return connectors


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
