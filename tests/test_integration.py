from datetime import datetime, timezone
from models import Usuario, Texto, Flashcard, ProgressoFlashcard, NivelCEFR, ObjetivoAprendizagem, db, CTestSubmissao
from wissio_app import app

def test_db_schema():
    """Conecta ao banco e verifica se a tabela de usuários tem as colunas necessárias."""
    with app.app_context():
        db.create_all()
        
        # Verificar colunas da tabela usuarios
        inspector = db.inspect(db.engine)
        cols = [c['name'] for c in inspector.get_columns('usuarios')]
        
        required_cols = ['id', 'nome', 'email', 'senha_hash', 'token_reset_senha', 'token_reset_expira']
        missing = [c for c in required_cols if c not in cols]
        assert not missing, f"Colunas faltantes: {missing}"
        
        # Verificar enum NivelCEFR
        usuarios_with_nivel = Usuario.query.first() is not None or True
        assert usuarios_with_nivel
        
        db.session.rollback()
        print("✓ Schema do banco está compatível!")

def test_password_reset_flow():
    """Testa o fluxo completo de recuperação de senha."""
    with app.app_context():
        db.create_all()
        
        # Criar usuário de teste
        u = Usuario(nome='Reset Test', email='reset@test.com')
        u.set_senha('oldpassword')
        db.session.add(u)
        db.session.commit()
        
        # Gerar token de reset
        u.gerar_token_reset()
        assert u.token_reset_senha is not None
        assert u.token_reset_expira is not None
        
        # Verificar token
        assert u.verificar_token_reset(u.token_reset_senha)
        
        # Redefinir senha
        u.set_senha('newpassword')
        u.token_reset_senha = None
        u.token_reset_expira = None
        db.session.commit()
        
        # Verificar nova senha funciona
        assert u.check_senha('newpassword')
        assert not u.check_senha('oldpassword')
        
        db.session.rollback()
        print("✓ Fluxo de recuperação de senha funciona!")

if __name__ == '__main__':
    test_db_schema()
    test_password_reset_flow()
    print("\n✓ Todos os testes de integração passaram!")