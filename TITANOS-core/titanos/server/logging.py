import logging
import sys

def setup_logging():
    # Remove all existing handlers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()
            
    # Setup structured JSON logging if you prefer, or basic formatting
    formatter = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    
    # Suppress verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

if __name__ == "__main__":
    setup_logging()
    logging.info("Logging configured.")
