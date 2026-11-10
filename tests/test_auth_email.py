"""Testes de integração do fluxo de verificação de e-mail.

Valida:
- Persistência no banco de dados (email_verificado = True).
- Sincronização com a sessão Flask.
- Exibição/Omissão dinâmica do alerta na navbar.
- Fluxo de verificação via token (produção).
"""

import pytest
from models import Usuario, db
from wissio_app import app as flask_app


@pytest.fixture
def client():
    """Configura app para teste com banco em memória."""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    
    with flask_app.app_context():
        db.create_all()
        with flask_app.test_client() as test_client:
            yield test_client
        db.session.remove()
        db.drop_all()


@pytest.fixture
def usuario_logado(client):
    """Cria um usuário e realiza o login simulado via sessão."""
    with flask_app.app_context():
        u = Usuario(nome='Email Test', email='email@teste.com')
        u.set_senha('senha123')
        db.session.add(u)
        db.session.commit()
        uid = u.id
    
    with client.session_transaction() as sess:
        sess['usuario_id'] = uid
        sess['usuario_nome'] = 'Email Test'
    return uid


def test_navbar_exibe_alerta_quando_nao_verificado(client, usuario_logado):
    """O badge de aviso deve aparecer para usuários não verificados."""
    resp = client.get('/home')
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'Verificar e-mail' in html


def test_verificar_email_post_sincroniza_estado(client, usuario_logado):
    """O clique no botão de verificação deve atualizar banco e sessão."""
    # POST para a rota de verificação (simulando clique no botão)
    resp = client.post('/verificar-email', follow_redirects=True)
    assert resp.status_code == 200
    assert 'E-mail verificado com sucesso' in resp.get_data(as_text=True)

    # Verifica Banco
    with flask_app.app_context():
        u = db.session.get(Usuario, usuario_logado)
        assert u.email_verificado is True

    # Verifica Sessão
    with client.session_transaction() as sess:
        assert sess.get('email_verificado') is True


def test_alerta_navbar_desaparece_apos_verificacao(client, usuario_logado):
    """O badge deve sumir de todas as páginas imediatamente após verificar."""
    # 1. Verifica (POST)
    client.post('/verificar-email')
    
    # 2. Checa múltiplas páginas
    for rota in ['/home', '/textos']:
        resp = client.get(rota)
        html = resp.get_data(as_text=True)
        assert 'Verificar e-mail' not in html, f"Badge persistiu na rota {rota}"


def test_fluxo_token_verificacao_producao(client, usuario_logado):
    """Testa a rota de verificação por link/token (usada em produção)."""
    with flask_app.app_context():
        u = db.session.get(Usuario, usuario_logado)
        u.gerar_token_verificacao()
        token = u.token_verificacao
        db.session.commit()

    # GET para a rota do link de e-mail
    resp = client.get(f'/verificar-email/{token}', follow_redirects=True)
    assert resp.status_code == 200
    assert 'E-mail verificado com sucesso' in resp.get_data(as_text=True)
    
    with flask_app.app_context():
        u = db.session.get(Usuario, usuario_logado)
        assert u.email_verificado is True
        assert u.token_verificacao is None

    with client.session_transaction() as sess:
        assert sess.get('email_verificado') is True


def test_token_invalido_exibe_erro(client, usuario_logado):
    """Link inválido ou expirado deve mostrar erro e não verificar."""
    resp = client.get('/verificar-email/token-falso-123', follow_redirects=True)
    assert 'Link de verificação inválido ou expirado' in resp.get_data(as_text=True)
    
    with flask_app.app_context():
        u = db.session.get(Usuario, usuario_logado)
        assert u.email_verificado is False
