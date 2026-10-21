import sys
from wissio_app import app, db

print("=== INICIALIZANDO BANCO DE DADOS (SQLite) ===")
sys.stdout.flush()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wissio.db'
print("DEBUG: URL do Banco:", app.config.get('SQLALCHEMY_DATABASE_URI'))
sys.stdout.flush()

with app.app_context():
    db.create_all()
    print("DEBUG: Tabelas criadas com sucesso.")
    sys.stdout.flush()
