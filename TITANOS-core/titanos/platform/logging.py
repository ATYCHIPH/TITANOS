import logging
import json
import datetime
import traceback

class JSONFormatter(logging.Formatter):
    """
    A custom structured JSON log formatter.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info:
            log_data["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(log_data)

def setup_logging(json_format: bool = False, level: int = logging.INFO) -> None:
    """
    Configures the root logger.
    Args:
        json_format: Whether to use the structured JSON formatter.
        level: The minimum logging level.
    """
    root_logger = logging.getLogger()
    
    # Remove existing handlers to avoid duplicates during setup
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
        
    root_logger.setLevel(level)
    
    handler = logging.StreamHandler()
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
