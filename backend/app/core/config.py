"""
ArgusCX — Application Configuration
Reads all settings from environment variables (.env)
"""
from functools import lru_cache
from typing import List, Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Local development can inherit the repository environment while a
        # backend-specific .env file overrides it. Neither file is committed.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App Core ──────────────────────────────
    APP_NAME: str = "ArgusCX"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_SECRET_KEY: SecretStr = SecretStr("")
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    ALLOWED_ORIGINS: List[str] = []

    # ── Frontend ──────────────────────────────
    DASHBOARD_BASE_URL: Optional[str] = None

    # ── Auth ──────────────────────────────────
    JWT_SECRET_KEY: SecretStr = SecretStr("")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: SecretStr = SecretStr("")

    # Firebase Admin SDK verification. Set these in production.
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None

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
    ARGUSCX_MASTER_KEY: Optional[SecretStr] = None
    GUARDRAILS_ENABLED: bool = True
    PREPROCESSOR_ENABLED: bool = True

    # ── External Integrations (Optional) ──────
    SHOPIFY_ACCESS_TOKEN: Optional[str] = None
    SHOPIFY_SHOP_DOMAIN: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None

    # Human-support handoff notifications. Supply values from your mail and
    # support providers; no delivery credential is stored in source control.
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_SECURE: bool = False
    SMTP_USERNAME: Optional[str] = None
    SMTP_USER: Optional[str] = None          # alias used in .env
    SMTP_PASSWORD: Optional[SecretStr] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    EMAIL_FROM: Optional[str] = None          # alias used in .env
    SMTP_FROM_NAME: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SUPPORT_HANDOFF_EMAIL: Optional[str] = None
    HUMAN_HANDOFF_WEBHOOK_URL: Optional[str] = None
    HUMAN_HANDOFF_WEBHOOK_SECRET: Optional[SecretStr] = None

    # S3-compatible evidence storage. Configure all fields together; the
    # platform refuses to emit invented upload URLs when storage is absent.
    OBJECT_STORAGE_ENDPOINT: Optional[str] = None
    OBJECT_STORAGE_ACCESS_KEY: Optional[SecretStr] = None
    OBJECT_STORAGE_SECRET_KEY: Optional[SecretStr] = None
    OBJECT_STORAGE_BUCKET: Optional[str] = None
    OBJECT_STORAGE_REGION: str = "ap-southeast-1"
    OBJECT_STORAGE_SECURE: bool = True

    # ── PostgreSQL ────────────────────────────
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[SecretStr] = None
    DATABASE_URL: Optional[SecretStr] = None
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── MongoDB ───────────────────────────────
    MONGO_URI: str = ""
    MONGO_DB: str = "arguscx_logs"
    MONGO_USER: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_AUTH_SOURCE: str = "admin"
    # ── Redis ─────────────────────────────────
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_URL: Optional[SecretStr] = None

    # ── Celery ─────────────────────────────────
    CELERY_BROKER_URL: Optional[SecretStr] = None
    CELERY_RESULT_BACKEND: Optional[SecretStr] = None

    # ── Fraud Detection ───────────────────────
    C2PA_VERIFICATION_ENABLED: bool = True
    EXIF_CHECK_ENABLED: bool = True
    AI_ARTIFACT_DETECTION_ENABLED: bool = True

    # ── Object Storage (S3 / R2) ─────────────
    OBJECT_STORAGE_ENDPOINT: Optional[str] = None
    OBJECT_STORAGE_REGION: str = "us-east-1"
    OBJECT_STORAGE_BUCKET: Optional[str] = None
    OBJECT_STORAGE_ACCESS_KEY: Optional[SecretStr] = None
    OBJECT_STORAGE_SECRET_KEY: Optional[SecretStr] = None

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
    def llm_enabled(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def active_llm_provider(self) -> str:
        if self.llm_enabled:
            return "groq"
        return "none"

    @property
    def active_connectors(self) -> list:
        connectors = []
        if self.SHOPIFY_ACCESS_TOKEN and self.SHOPIFY_SHOP_DOMAIN:
            connectors.append("shopify")
        if self.STRIPE_SECRET_KEY:
            connectors.append("stripe")
        if self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET:
            connectors.append("razorpay")
        return connectors

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_FROM_EMAIL and self.SUPPORT_HANDOFF_EMAIL)

    @property
    def human_handoff_webhook_configured(self) -> bool:
        return bool(self.HUMAN_HANDOFF_WEBHOOK_URL and self.HUMAN_HANDOFF_WEBHOOK_SECRET)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
