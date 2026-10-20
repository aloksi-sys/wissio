#!/bin/sh
set -ex

echo "=== INICIANDO ENTRYPOINT ==="

# Cria as tabelas no banco se ainda não existirem
echo "Criando tabelas do banco de dados se necessário..."
python init_db.py

PORT_TO_USE="${PORT:-5000}"
echo "Iniciando o Gunicorn na porta ${PORT_TO_USE}..."
exec gunicorn wissio_app:app --bind 0.0.0.0:${PORT_TO_USE}
