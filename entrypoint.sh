#!/bin/sh
set -e

echo "=== INICIANDO ENTRYPOINT ==="

# Tenta executar as migrações, mas não quebra o deploy se o banco demorar um segundo a mais
echo "Executando migrações do banco de dados..."
flask db upgrade || echo "Aviso: flask db upgrade falhou ou tabelas já existem, continuando..."

PORT_TO_USE="${PORT:-5000}"
echo "Iniciando o Gunicorn na porta ${PORT_TO_USE}..."
exec gunicorn wissio_app:app --bind 0.0.0.0:${PORT_TO_USE}
