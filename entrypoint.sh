#!/bin/sh
set -e

# Remove any external PostgreSQL URL that Render might inject
unset DATABASE_URL

echo "=== INICIANDO ENTRYPOINT (SQLite) ==="

echo "Criando tabelas do banco com Python..."
python3 init_db.py || python init_db.py

echo "Iniciando Gunicorn..."
exec python3 -m gunicorn -b 0.0.0.0:${PORT:-5000} wissio_app:app || python -m gunicorn -b 0.0.0.0:${PORT:-5000} wissio_app:app
