import pytest
from datetime import datetime, timezone
from models import Usuario, Texto, Flashcard, ProgressoFlashcard, NivelCEFR, ObjetivoAprendizagem, db, CTestSubmissao
from wissio_app import app as flask_app

@pytest.fixture
def client():
    """Configura app para teste com banco em memória."""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    with flask_app.app_context():
        db.create_all()
        with flask_app.test_client() as test_client:
            yield test_client
        db.session.remove()
        db.drop_all()

def test_auth_flow(client):
    """Testa o cadastro e login de usuário."""
    # Testar registro
    response = client.post('/cadastro', data={
        'nome': 'Teste User',
        'email': 'teste@wissio.com',
        'senha': 'password123',
        'confirmar_senha': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Testar login
    response = client.post('/login', data={
        'email': 'teste@wissio.com',
        'senha': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_nlp_processor():
    """Testa o processador de texto e C-Test."""
    from processador import processar_texto_alemao
    texto = "Das ist ein einfacher Text für den Test."
    resultado = processar_texto_alemao(texto)
    assert 'flashcards' in resultado
    assert 'ctest' in resultado
    assert len(resultado['flashcards']) > 0

def test_fsrs_logic(client):
    """Testa a lógica de repetição espaçada."""
    u = Usuario(nome='FSRS', email='fsrs@wissio.com')
    u.set_senha('123456')
    db.session.add(u)
    db.session.commit()
    
    fc = Flashcard(palavra_alemao='Haus', traducao='casa', usuario_id=u.id)
    db.session.add(fc)
    db.session.commit()
    
    prog = ProgressoFlashcard(usuario_id=u.id, flashcard_id=fc.id)
    db.session.add(prog)
    db.session.commit()
    
    assert prog.state_label == 'Novo'
    assert prog.pendente is True

def test_password_reset_flow(client):
    """Testa o fluxo completo de recuperação de senha."""
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
    db.session.commit()
    
    # Verificar nova senha funciona
    assert u.check_senha('newpassword')
    assert not u.check_senha('oldpassword')

def test_ctest_submission(client):
    """Testa a submissão de C-Test."""
    # Criar usuário
    u = Usuario(nome='CTest User', email='ctest@test.com')
    u.set_senha('123456')
    db.session.add(u)
    db.session.commit()
    
    # Criar texto com C-Test
    texto = Texto(
        titulo='Test Text',
        conteudo_original='Das ist ein einfacher Text für den Test.',
        nivel=NivelCEFR.A1,
        usuario_id=u.id,
        ctest_conteudo='Das ist ein __ ____ für den __.',
        ctest_respostas=['einfach', 'Test']
    )
    db.session.add(texto)
    db.session.commit()
    
    # Login
    with client.session_transaction() as sess:
        sess['usuario_id'] = u.id
        sess['usuario_nome'] = u.nome
    
    # Submeter C-Test
    response = client.post('/submeter_ctest', data={
        'id': texto.id,
        'gap_1': 'einfach',
        'gap_2': 'Test'
    }, follow_redirects=True)
    
    assert response.status_code == 200

def test_flashcard_review(client):
    """Testa a revisão de flashcards."""
    # Criar usuário
    u = Usuario(nome='Flash User', email='flash@test.com')
    u.set_senha('123456')
    db.session.add(u)
    db.session.commit()
    
    # Criar texto e flashcard
    texto = Texto(
        titulo='Test Text',
        conteudo_original='Das ist ein einfacher Text.',
        nivel=NivelCEFR.A1,
        usuario_id=u.id
    )
    db.session.add(texto)
    db.session.flush()
    
    fc = Flashcard(
        palavra_alemao='Haus',
        traducao='casa',
        tipo='Substantivo',
        exemplo='Das Haus ist groß.',
        alternativas='["casa", "livro", "porta", "água"]',
        usuario_id=u.id,
        texto_id=texto.id
    )
    db.session.add(fc)
    db.session.flush()
    
    prog = ProgressoFlashcard(
        usuario_id=u.id,
        flashcard_id=fc.id,
        stability=1.0,
        difficulty=5.0,
        next_review=datetime.now(timezone.utc)
    )
    db.session.add(prog)
    db.session.commit()
    
    # Login
    with client.session_transaction() as sess:
        sess['usuario_id'] = u.id
        sess['usuario_nome'] = u.nome
    
    # Revisar flashcard
    response = client.post(f'/flashcards/{fc.id}/responder', data={
        'resposta': 'casa',
        'correta': 'true'
    }, follow_redirects=True)
    
    assert response.status_code == 200