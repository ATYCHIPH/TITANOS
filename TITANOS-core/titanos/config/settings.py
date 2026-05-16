import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    TITANOS configuration settings.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project Info
    PROJECT_NAME: str = "TITANOS"
    VERSION: str = "0.1.0"
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / ".titanos"
    MEMORY_PATH: Path = DATA_DIR / "memory"
    LOG_PATH: Path = DATA_DIR / "logs"
    
    # AI Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_API_KEY: Optional[str] = None
    TITANOS_MODEL: str = "ollama:llama3"
    
    # Runtime Options
    SANDBOX_MODE: bool = True
    QUIET_HOURS_ENABLED: bool = False
    LOG_LEVEL: str = "INFO"
    COMMAND_TIMEOUT_SECONDS: int = 30
    COMMAND_ALLOWLIST: str = ""
    COMMAND_DENYLIST: str = "rm,del,erase,rmdir,remove-item,format,shutdown,restart-computer,stop-computer,git reset,git clean"
    AUTO_MEMORY_ENABLED: bool = True
    MEMORY_MIN_CHARS: int = 12
    MEMORY_MAX_CHARS: int = 500
    SESSION_HISTORY_ENABLED: bool = True
    
    # Server Options
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ALLOW_ORIGINS: str = "*"
    JWT_SECRET: str = "super-secret-dev-key"
    ENVIRONMENT: str = "development"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.MEMORY_PATH.mkdir(parents=True, exist_ok=True)
        self.LOG_PATH.mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()
