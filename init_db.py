#!/usr/bin/env python
"""
Script de inicialização robusto para Render.
Este script é executado antes do Gunicorn.
"""

import sys
import os

# Print startup info
print("=" * 60)
print("WISSIO - Inicialização Render (SQLite)")
print("=" * 60)
sys.stdout.flush()

# CRÍTICO: Remove DATABASE_URL injetado pelo Render antes de qualquer importação
if 'DATABASE_URL' in os.environ:
    db_url = os.environ['DATABASE_URL']
    print(f"DATABASE_URL encontrado: {db_url[:80]}...")
    sys.stdout.flush()
    del os.environ['DATABASE_URL']

os.environ.pop('DATABASE_URL', None)

# Verify DATABASE_URL is gone
db_check = os.environ.get('DATABASE_URL')
if db_check:
    print(f"ERRO: DATABASE_URL ainda existe: {db_check}")
    sys.exit(1)

print("DATABASE_URL removido com sucesso")
sys.stdout.flush()

# Agora importar a aplicação
from wissio_app import app, db

print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"SECRET_KEY configurado: {len(app.config['SECRET_KEY'])} chars")
sys.stdout.flush()

# Inicializar banco
with app.app_context():
    print("Criando tabelas...")
    sys.stdout.flush()
    
    db.create_all()
    print("Tabelas criadas!")
    
    # Verificar tabela de usuarios
    from models import Usuario
    count = Usuario.query.count()
    print(f"Usuarios no banco: {count}")
    
    # Criar admin se não existir
    admin = Usuario.query.filter_by(email='admin@wissio.com').first()
    if not admin:
        print("Criando admin...")
        sys.stdout.flush()
        admin = Usuario(nome='Admin Wissio', email='admin@wissio.com')
        admin.set_senha('admin123')
        db.session.add(admin)
        db.session.commit()
        print(f"Admin criado: ID={admin.id}")
    else:
        print(f"Admin existe: ID={admin.id}")
    
    # Testar verificação de senha
    pwd_ok = admin.check_senha('admin123')
    print(f"Teste senha admin: {pwd_ok}")
    
    if not pwd_ok:
        print("ERRO: Verificação de senha do admin falhou!")
        sys.exit(1)

print("=" * 60)
print("INICIALIZAÇÃO CONCLUÍDA COM SUCESSO")
print("=" * 60)
sys.stdout.flush()