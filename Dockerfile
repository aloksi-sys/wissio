# Dockerfile for the Wissio Flask application
# ---------------------------------------------------
# Use a lightweight Python base image
FROM python:3.12-slim

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy only requirements first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir psycopg2-binary==2.9.9

# Copy the rest of the application code
COPY . .

# Garante permissão de execução no script de entrada em qualquer circunstância
RUN chmod +x /app/entrypoint.sh

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose the port Flask will run on
EXPOSE 5000

# Use gunicorn as the production WSGI server
ENTRYPOINT ["/app/entrypoint.sh"]
