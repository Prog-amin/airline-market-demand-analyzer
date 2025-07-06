"""
Application configuration settings.
"""
import os
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Airline Market Demand Analysis"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # FastAPI backend
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database - Supabase PostgreSQL
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_DB: str = os.getenv("SUPABASE_DB", "postgres")
    SUPABASE_USER: str = os.getenv("SUPABASE_USER", "postgres")
    SUPABASE_PASSWORD: str = os.getenv("SUPABASE_PASSWORD", "")
    SUPABASE_HOST: str = os.getenv("SUPABASE_HOST", "db.xxxxx.supabase.co")
    SUPABASE_PORT: str = os.getenv("SUPABASE_PORT", "5432")
    
    # For backward compatibility
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", SUPABASE_HOST)
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", SUPABASE_USER)
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", SUPABASE_PASSWORD)
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", SUPABASE_DB)
    
    # Connection URL for SQLAlchemy
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @field_validator("DATABASE_URL", mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str) and v:
            return v
        
        values = info.data
        
        # Check for direct Supabase connection URL
        if supabase_url := values.get("SUPABASE_URL"):
            if supabase_url.startswith(("postgres://", "postgresql://")):
                return supabase_url
                
        # Build connection string from individual parameters
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=values.get("SUPABASE_USER") or values.get("POSTGRES_USER"),
                password=values.get("SUPABASE_PASSWORD") or values.get("POSTGRES_PASSWORD"),
                host=values.get("SUPABASE_HOST") or values.get("POSTGRES_SERVER"),
                port=values.get("SUPABASE_PORT", "5432"),
                path=f"/{values.get('SUPABASE_DB') or values.get('POSTGRES_DB', 'postgres')}",
                query={
                    "sslmode": "require" if values.get("ENVIRONMENT") == "production" else "prefer"
                }
            )
        )
    
    # API Keys
    AMADEUS_API_KEY: Optional[str] = os.getenv("AMADEUS_API_KEY")
    AMADEUS_API_SECRET: Optional[str] = os.getenv("AMADEUS_API_SECRET")
    RAPIDAPI_KEY: Optional[str] = os.getenv("RAPIDAPI_KEY")
    AVIATIONSTACK_API_KEY: Optional[str] = os.getenv("AVIATIONSTACK_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Pydantic v2 config
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

# Create settings instance
settings = Settings()
