import logging
import json
import sys
from datetime import datetime
from ..config.settings import settings

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno
        }
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logging():
    """
    Sets up logging for TITANOS.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    if getattr(root_logger, "_titanos_configured", False):
        return
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    root_logger.addHandler(console_handler)
    
    # File handler (structured JSON)
    log_file = settings.LOG_PATH / f"titanos_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)
    
    # Error log
    error_log = settings.LOG_PATH / "error.log"
    error_handler = logging.FileHandler(error_log, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    root_logger._titanos_configured = True

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Initialize on import
setup_logging()
logger = get_logger("TITANOS")
