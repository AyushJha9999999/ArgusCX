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
    NEXT_PUBLIC_DEMO_MODE: bool = True

    # ── Auth ──────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OpenAI ────────────────────────────────
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORG_ID: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.2

    # ── Anthropic ─────────────────────────────
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-opus-4-5"

    # ── Azure OpenAI ──────────────────────────
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-small"

    # ── Azure AI Services ─────────────────────
    AZURE_AI_SERVICES_KEY: Optional[str] = None
    AZURE_AI_SERVICES_ENDPOINT: Optional[str] = None
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_RESOURCE_GROUP: str = "arguscx-rg"
    AZURE_AI_PROJECT_NAME: str = "arguscx-ai"

    # ── Azure AI Vision ───────────────────────
    AZURE_VISION_API_KEY: Optional[str] = None
    AZURE_VISION_ENDPOINT: Optional[str] = None

    # ── Ollama (Local LLM) ────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # ── LangSmith ─────────────────────────────
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "arguscx"
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # ── Agent Config ──────────────────────────
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 60
    AGENT_CONFIDENCE_THRESHOLD: float = 0.75
    AGENT_FRAUD_RISK_THRESHOLD: float = 0.65
    AGENT_AUTO_RESOLVE_THRESHOLD: float = 0.85
    ORCHESTRATOR_MODEL: str = "gpt-4o"
    SPECIALIST_MODEL: str = "gpt-4o-mini"

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

    # ── Pinecone ──────────────────────────────
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: str = "gcp-starter"
    PINECONE_INDEX_NAME: str = "arguscx-knowledge"
    PINECONE_DIMENSION: int = 1536

    # ── ChromaDB (Local Vector DB) ────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION: str = "arguscx_knowledge"

    # ── Azure AI Search ───────────────────────
    AZURE_SEARCH_ENDPOINT: Optional[str] = None
    AZURE_SEARCH_API_KEY: Optional[str] = None
    AZURE_SEARCH_INDEX_NAME: str = "arguscx-rag"

    # ── AWS S3 ────────────────────────────────
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-south-1"
    AWS_S3_BUCKET_NAME: str = "arguscx-evidence"
    AWS_S3_ENDPOINT_URL: Optional[str] = None

    # ── MinIO (Local S3) ──────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio_access_key"
    MINIO_SECRET_KEY: str = "minio_secret_key"
    MINIO_BUCKET: str = "arguscx-evidence"
    MINIO_SECURE: bool = False

    # ── Shopify ───────────────────────────────
    SHOPIFY_API_KEY: Optional[str] = None
    SHOPIFY_API_SECRET: Optional[str] = None
    SHOPIFY_ACCESS_TOKEN: Optional[str] = None
    SHOPIFY_SHOP_DOMAIN: Optional[str] = None
    SHOPIFY_API_VERSION: str = "2024-01"

    # ── Stripe ────────────────────────────────
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # ── Razorpay ──────────────────────────────
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None

    # ── Slack ─────────────────────────────────
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_SIGNING_SECRET: Optional[str] = None
    SLACK_CHANNEL_ID: Optional[str] = None
    SLACK_ESCALATION_CHANNEL: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None

    # ── Zendesk ───────────────────────────────
    ZENDESK_SUBDOMAIN: Optional[str] = None
    ZENDESK_API_TOKEN: Optional[str] = None
    ZENDESK_EMAIL: Optional[str] = None

    # ── Twilio ────────────────────────────────
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None

    # ── SendGrid ──────────────────────────────
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "support@arguscx.ai"
    SENDGRID_FROM_NAME: str = "ArgusCX Support"

    # ── Sentry ────────────────────────────────
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ── Grafana ───────────────────────────────
    GRAFANA_URL: str = "http://localhost:3001"
    GRAFANA_API_KEY: Optional[str] = None
    GRAFANA_ADMIN_USER: str = "admin"
    GRAFANA_ADMIN_PASSWORD: str = "arguscx_grafana"

    # ── Prometheus ────────────────────────────
    PROMETHEUS_PORT: int = 9090
    METRICS_ENABLED: bool = True

    # ── Celery ────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Fraud Detection ───────────────────────
    C2PA_VERIFICATION_ENABLED: bool = True
    EXIF_CHECK_ENABLED: bool = True
    AI_ARTIFACT_DETECTION_ENABLED: bool = True
    HIVE_API_KEY: Optional[str] = None
    SIGHTENGINE_API_USER: Optional[str] = None
    SIGHTENGINE_API_SECRET: Optional[str] = None

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
        return self.NEXT_PUBLIC_DEMO_MODE or not self.OPENAI_API_KEY

    @property
    def active_llm_provider(self) -> str:
        if self.AZURE_OPENAI_API_KEY:
            return "azure_openai"
        if self.OPENAI_API_KEY:
            return "openai"
        if self.ANTHROPIC_API_KEY:
            return "anthropic"
        return "ollama"  # Fallback to local

    @property
    def active_vector_store(self) -> str:
        if self.PINECONE_API_KEY:
            return "pinecone"
        if self.AZURE_SEARCH_API_KEY:
            return "azure_search"
        return "chromadb"  # Local fallback


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
