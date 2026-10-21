#!/bin/sh
set -ex

# Remove any PostgreSQL URL that Render might inject (we use SQLite only)
unset DATABASE_URL

echo "=== INICIANDO ENTRYPOINT (SQLite) ==="

echo "Criando tabelas do banco..."
python init_db.py

echo "Iniciando Gunicorn..."
exec python -m gunicorn -b 0.0.0.0:${PORT:-5000} wissio_app:app