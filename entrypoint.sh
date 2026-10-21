#!/bin/sh
unset DATABASE_URL

echo "=== INICIANDO ENTRYPOINT ==="

echo "Criando tabelas..."
python init_db.py

# Verify gunicorn is available
which gunicorn || echo "ERROR: gunicorn not found in PATH"

exec gunicorn -b 0.0.0.0:${PORT:-5000} wissio_app:app
