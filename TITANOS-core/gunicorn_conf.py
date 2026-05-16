import os

port = os.getenv("PORT", "8000")
bind = f"0.0.0.0:{port}"

workers_per_core = 1
cores = os.cpu_count()
workers = int(os.getenv("WORKERS", str(cores * workers_per_core)))

timeout = int(os.getenv("TIMEOUT", "120"))
keepalive = int(os.getenv("KEEPALIVE", "5"))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Graceful shutdown
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "120"))
