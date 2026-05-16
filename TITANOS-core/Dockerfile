FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
# If there is a requirements.txt, you can copy it here, but we will use pip with pyproject.toml
RUN pip install --no-cache-dir gunicorn uvicorn[standard] && \
    pip install --no-cache-dir .

# Copy application source code
COPY . /app/

# Expose the port
EXPOSE 8000

# Run with Gunicorn using Uvicorn worker for production performance
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_conf.py", "titanos.server.app:app"]
