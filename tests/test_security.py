"""Testes de segurança: CSRF, proteção do endpoint de debug e filtro de IDs."""

import pytest
from models import Usuario, Texto, Flashcard, ProgressoFlashcard, NivelCEFR, db
from wissio_app import app as flask_app


@pytest.fixture
def client():
    """Configura app para teste com banco em memória."""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'

    with flask_app.app_context():
        db.create_all()
        with flask_app.test_client() as test_client:
            yield test_client
        db.session.remove()
        db.drop_all()


@pytest.fixture
def usuario_logado(client):
    """Cria um usuário e realiza o login (com token CSRF válido)."""
    with flask_app.app_context():
        u = Usuario(nome='Sec Test', email='sec@test.com')
        u.set_senha('senha123')
        db.session.add(u)
        db.session.commit()
        uid = u.id

    # Login precisa de token CSRF válido
    with client.session_transaction() as sess:
        sess['usuario_id'] = uid
        sess['usuario_nome'] = 'Sec Test'
    return uid


def _csrf_token(client):
    """Extrai um token CSRF válido da página de login."""
    resp = client.get('/login')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    marker = 'name="csrf_token" value="'
    start = html.find(marker) + len(marker)
    end = html.find('"', start)
    return html[start:end]


def test_debug_info_requires_login(client):
    """Endpoint de debug não deve ser acessível sem autenticação."""
    resp = client.get('/debug-info', follow_redirects=False)
    # login_required redireciona para /login em vez de expor dados
    assert resp.status_code == 302
    assert '/login' in resp.headers.get('Location', '')


def test_debug_info_hidden_in_production(client, usuario_logado):
    """Mesmo autenticado, o debug deve retornar 404 fora do modo debug."""
    resp = client.get('/debug-info')
    assert resp.status_code == 404


def test_csrf_blocks_post_without_token(client):
    """POSTs sem token CSRF devem ser rejeitados (400)."""
    resp = client.post('/login', data={'email': 'a@a.com', 'senha': 'x'})
    assert resp.status_code == 400


def test_csrf_blocks_invalid_token(client):
    """POSTs com token CSRF inválido devem ser rejeitados (400)."""
    resp = client.post(
        '/login',
        data={'email': 'a@a.com', 'senha': 'x', 'csrf_token': 'token-falso'},
    )
    assert resp.status_code == 400


def test_csrf_accepts_valid_token(client):
    """POSTs com token CSRF válido passam pela validação."""
    token = _csrf_token(client)
    resp = client.post(
        '/login',
        data={'email': 'inexistente@test.com', 'senha': 'x', 'csrf_token': token},
        follow_redirects=False,
    )
    # Token válido: o handler de login roda e redireciona (flash de erro)
    assert resp.status_code == 302


def test_flashcards_ids_filter(client, usuario_logado):
    """A rota /flashcards?ids= deve carregar apenas os cartões listados."""
    with flask_app.app_context():
        u = db.session.get(Usuario, usuario_logado)
        t1 = Texto(titulo='T1', conteudo_original='abc', nivel=NivelCEFR.A1, usuario_id=u.id)
        db.session.add(t1)
        db.session.flush()

        fc_ids = []
        for i in range(4):
            fc = Flashcard(palavra_alemao=f'Wort{i}', traducao=f'p{i}', usuario_id=u.id, texto_id=t1.id)
            db.session.add(fc)
            db.session.flush()
            prog = ProgressoFlashcard(usuario_id=u.id, flashcard_id=fc.id)
            db.session.add(prog)
            fc_ids.append(fc.id)
        db.session.commit()

        # Seleciona apenas 2 IDs
        alvo = f'{fc_ids[0]},{fc_ids[2]}'
        resp = client.get(f'/flashcards?ids={alvo}')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        assert 'Wort0' in html and 'Wort2' in html
        assert 'Wort1' not in html and 'Wort3' not in html


def test_flashcards_revisar_requires_csrf(client, usuario_logado):
    """AJAX de revisão sem token CSRF deve falhar com 400."""
    with flask_app.app_context():
        u = db.session.get(Usuario, usuario_logado)
        fc = Flashcard(palavra_alemao='Haus', traducao='casa', usuario_id=u.id)
        db.session.add(fc)
        db.session.flush()
        fc_id = fc.id
        db.session.commit()

    resp = client.post(f'/flashcards/{fc_id}/revisar', data={'facilidade': 'good'})
    assert resp.status_code == 400


def test_flashcards_revisar_with_csrf(client, usuario_logado):
    """AJAX de revisão com cabeçalho X-CSRFToken válido deve funcionar."""
    token = _csrf_token(client)
    with flask_app.app_context():
        u = db.session.get(Usuario, usuario_logado)
        fc = Flashcard(palavra_alemao='Haus', traducao='casa', usuario_id=u.id)
        db.session.add(fc)
        db.session.flush()
        fc_id = fc.id
        db.session.add(ProgressoFlashcard(usuario_id=u.id, flashcard_id=fc.id))
        db.session.commit()

    resp = client.post(
        f'/flashcards/{fc_id}/revisar',
        data={'facilidade': 'good', 'resposta': 'casa'},
        headers={'X-CSRFToken': token},
    )
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
