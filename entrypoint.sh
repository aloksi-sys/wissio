#!/bin/sh
set -e

echo "Executando migrações do banco de dados..."
flask db upgrade || echo "Aviso: flask db upgrade falhou ou tabelas já existem."

echo "Iniciando o Gunicorn na porta ${PORT:-5000}..."
exec gunicorn app:app --bind 0.0.0.0:${PORT:-5000}
