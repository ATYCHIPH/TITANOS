import os
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Settings:
    """
    TITANOS configuration settings.

    This class intentionally avoids pydantic BaseSettings in the runtime path so
    the backend can be frozen into a standalone desktop executable.
    """

    def __init__(self) -> None:
        self.PROJECT_NAME = os.getenv("TITANOS_PROJECT_NAME", "TITANOS")
        self.VERSION = os.getenv("TITANOS_VERSION", "0.1.0")

        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.DATA_DIR = Path(os.getenv("TITANOS_DATA_DIR", str(self.BASE_DIR / ".titanos")))
        self.MEMORY_PATH = self.DATA_DIR / "memory"
        self.LOG_PATH = self.DATA_DIR / "logs"

        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
        self.TITANOS_MODEL = os.getenv("TITANOS_MODEL", "ollama:llama3")

        self.SANDBOX_MODE = _bool_env("TITANOS_SANDBOX_MODE", True)
        self.QUIET_HOURS_ENABLED = _bool_env("TITANOS_QUIET_HOURS_ENABLED", False)
        self.LOG_LEVEL = os.getenv("TITANOS_LOG_LEVEL", "INFO")
        self.COMMAND_TIMEOUT_SECONDS = _int_env("TITANOS_COMMAND_TIMEOUT_SECONDS", 30)
        self.COMMAND_ALLOWLIST = os.getenv("TITANOS_COMMAND_ALLOWLIST", "")
        self.COMMAND_DENYLIST = os.getenv(
            "TITANOS_COMMAND_DENYLIST",
            "rm,del,erase,rmdir,remove-item,format,shutdown,restart-computer,stop-computer,git reset,git clean",
        )
        self.AUTO_MEMORY_ENABLED = _bool_env("TITANOS_AUTO_MEMORY_ENABLED", True)
        self.MEMORY_MIN_CHARS = _int_env("TITANOS_MEMORY_MIN_CHARS", 12)
        self.MEMORY_MAX_CHARS = _int_env("TITANOS_MEMORY_MAX_CHARS", 500)
        self.SESSION_HISTORY_ENABLED = _bool_env("TITANOS_SESSION_HISTORY_ENABLED", True)

        self.HOST = os.getenv("TITANOS_HOST", "127.0.0.1")
        self.PORT = _int_env("TITANOS_PORT", 8000)
        self.CORS_ALLOW_ORIGINS = os.getenv("TITANOS_CORS_ALLOW_ORIGINS", "*")
        self.JWT_SECRET = os.getenv("TITANOS_JWT_SECRET", "super-secret-dev-key")
        self.ENVIRONMENT = os.getenv("TITANOS_ENVIRONMENT", "development")

        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.MEMORY_PATH.mkdir(parents=True, exist_ok=True)
        self.LOG_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()
