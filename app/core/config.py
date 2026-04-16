from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    intercom_access_token: str = Field(...)
    intercom_api_base: str = "https://api.intercom.io"
    huggingface_api_key: str = Field(...)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    pinecone_api_key: str = Field(...)
    pinecone_index_name: str = "intercom-articles-hf"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    app_env: str = "development"
    log_level: str = "INFO"
    sync_lookback_hours: int = 24
    groq_api_key: str = Field(...)
    groq_model: str = "llama3-8b-8192"
    sync_trigger_hour: int = 17
    sync_trigger_minute: int = 0

settings = Settings()
