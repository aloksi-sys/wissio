# Dockerfile for the Wissio Flask application - SQLite ONLY
# ---------------------------------------------------
FROM python:3.12-slim
ARG CACHE_BUST=8

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Cache-bust argument
ARG CACHE_BUST=8
RUN echo "cache bust $CACHE_BUST"

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

# Environment variables
ENV FLASK_APP=wissio_app
ENV FLASK_RUN_HOST=0.0.0.0
ENV DATABASE_URL=""
ENV SQLALCHEMY_DATABASE_URI="sqlite:///wissio.db"
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 5000

# Inicialização direta no shell para evitar erro 128 (CRLF/LF)
CMD sh -c "unset DATABASE_URL && python init_db.py && python -m gunicorn -b 0.0.0.0:${PORT:-5000} wissio_app:app"