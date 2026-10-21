# Dockerfile for the Wissio Flask application - SQLite ONLY
# ---------------------------------------------------
# Use a lightweight Python base image
FROM python:3.12-slim
ARG CACHE_BUST=6

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Cache-bust argument – change its value to force a rebuild of layers below
ARG CACHE_BUST=6
RUN echo "cache bust $CACHE_BUST"

# Install Python dependencies first (cached)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy the rest of the application source code
COPY . .

# Environment variables for Flask - SQLITE ONLY
ENV FLASK_APP=wissio_app
ENV FLASK_RUN_HOST=0.0.0.0
ENV DATABASE_URL=
ENV SQLALCHEMY_DATABASE_URI=sqlite:///wissio.db
ENV PYTHONUNBUFFERED=1

# Expose the port used by Gunicorn
EXPOSE 5000

# Use Gunicorn as the production WSGI server
ENTRYPOINT ["/app/entrypoint.sh"]