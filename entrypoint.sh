#!/bin/sh
unset DATABASE_URL

echo "=== INICIANDO ENTRYPOINT ==="

echo "Criando tabelas..."
python init_db.py

exec /usr/local/bin/gunicorn -b 0.0.0.0:${PORT:-5000} wissio_app:app
