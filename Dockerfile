# Dockerfile for Wissio - SQLite only (for Render deployment)
# ===============================================================

FROM python:3.12-slim

# Build arguments
ARG CACHE_BUST=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=wissio_app
ENV FLASK_RUN_HOST=0.0.0.0
# REMOVED: DATABASE_URL to prevent conflict with Render's Supabase injection
# REMOVED: SQLALCHEMY_DATABASE_URI from environment (set in code)
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# Start command: unset DATABASE_URL, init DB, then run gunicorn
CMD sh -c "unset DATABASE_URL && python init_db.py && gunicorn -b 0.0.0.0:\${PORT:-5000} wissio_app:app"

# Labels for Render
LABEL maintainer="Wissio Team"
LABEL description="German Language Learning Platform"