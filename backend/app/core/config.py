"""
Application Configuration
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_URL: str = "http://localhost:8000"
    WEB_URL: str = "http://localhost:3000"

    # CORS
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Get CORS origins"""
        return [
            self.WEB_URL,
            "http://localhost:3000",
            "http://localhost:3001",
        ]

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-west1-gcp"
    PINECONE_INDEX_NAME: str = "unifydata-embeddings"

    # OpenAI
    OPENAI_API_KEY: str

    # Anthropic
    ANTHROPIC_API_KEY: str

    # AWS S3 / Cloudflare R2
    S3_BUCKET_NAME: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    S3_REGION: str = "auto"

    # Email
    SENDGRID_API_KEY: str
    FROM_EMAIL: str = "noreply@unifydata.ai"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Monitoring
    SENTRY_DSN: str | None = None

    # OAuth - Salesforce
    SALESFORCE_CLIENT_ID: str | None = None
    SALESFORCE_CLIENT_SECRET: str | None = None
    SALESFORCE_REDIRECT_URI: str | None = None

    # OAuth - Google
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    # OAuth - Slack
    SLACK_CLIENT_ID: str | None = None
    SLACK_CLIENT_SECRET: str | None = None
    SLACK_REDIRECT_URI: str | None = None

    # OAuth - Notion
    NOTION_CLIENT_ID: str | None = None
    NOTION_CLIENT_SECRET: str | None = None
    NOTION_REDIRECT_URI: str | None = None


# Create settings instance
settings = Settings()
