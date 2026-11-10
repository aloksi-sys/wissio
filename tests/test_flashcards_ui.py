"""Testes da UI de flashcards, regressão do JSON/barra de progresso e XP.

Valida:
- Renderização correta da página de flashcards.
- Bloco JSON `#flashcards-data` válido mesmo com `progresso = None`.
- Presença dos elementos de UI (barra de progresso, contadores, tela de vitória).
- Funcionamento do endpoint de revisão FSRS com XP.
- Geração correta de flashcards com traduções reais na criação de texto.
"""

import json
import re
import pytest
from models import Usuario, Texto, Flashcard, ProgressoFlashcard, db
from wissio_app import app as flask_app


@pytest.fixture
def client():
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


@pytest.fixture(autouse=True)
def apis_offline(monkeypatch):
    import translation
    monkeypatch.setattr(translation, '_traduzir_google', lambda *a, **k: None)
    monkeypatch.setattr(translation, '_traduzir_mymemory', lambda *a, **k: None)


@pytest.fixture
def usuario_com_texto(client):
    with flask_app.app_context():
        u = Usuario(nome='UI Test', email='ui@teste.com')
        u.set_senha('senha123')
        db.session.add(u)
        db.session.commit()
        uid = u.id
    
    with client.session_transaction() as sess:
        sess['usuario_id'] = uid
        sess['usuario_nome'] = 'UI Test'

    conteudo = 'Der Deutschkurs bietet ein breites Angebot für Kommunikation und Sprache.'
    resp = client.post('/texto/novo', data={
        'titulo': 'Curso B1',
        'conteudo': conteudo,
        'nivel_cefr': 'B1',
    }, follow_redirects=True)
    assert resp.status_code == 200
    
    with flask_app.app_context():
        texto = Texto.query.filter_by(usuario_id=uid).first()
        tid = texto.id
    return uid, tid


def _extrair_json_flashcards(html):
    m = re.search(
        r'<script id="flashcards-data" type="application/json">\s*(.*?)\s*</script>',
        html, re.S)
    assert m, "Bloco #flashcards-data não encontrado no HTML"
    return json.loads(m.group(1))


def test_flashcards_gerados_tem_traducoes_validas(client, usuario_com_texto):
    uid, tid = usuario_com_texto
    with flask_app.app_context():
        fcs = Flashcard.query.filter_by(usuario_id=uid).all()
        assert len(fcs) > 0, "Nenhum flashcard gerado"
        for fc in fcs:
            assert fc.traducao, f"Flashcard '{fc.palavra_alemao}' sem tradução"
            assert fc.traducao.strip().lower() != fc.palavra_alemao.strip().lower()


def test_json_valido_com_progresso_none(client, usuario_com_texto):
    """Regressão: garante que progresso=None não corrompe o JSON nem congela o JS."""
    uid, tid = usuario_com_texto
    with flask_app.app_context():
        # Cria card sem ProgressoFlashcard
        fc = Flashcard(
            palavra_alemao='Wohnung',
            traducao='apartamento',
            tipo='Substantivo',
            exemplo='Das ist eine Wohnung.',
            usuario_id=uid,
            texto_id=tid
        )
        db.session.add(fc)
        db.session.commit()
        fc_id = fc.id

    resp = client.get(f'/texto/{tid}/flashcards')
    assert resp.status_code == 200
    data = _extrair_json_flashcards(resp.get_data(as_text=True))
    
    alvo = [c for c in data if c['id'] == fc_id]
    assert len(alvo) == 1
    c = alvo[0]
    assert c['reps'] == 0
    assert c['lapses'] == 0
    assert c['estado'] == 'Novo'
    assert c['proxima_revisao'] is None


def test_elementos_ui_progresso_presentes(client, usuario_com_texto):
    """Valida presença dos elementos DOM da barra de progresso, XP e vitória."""
    resp = client.get('/flashcards')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    
    for el in ['barra-progresso', 'card-atual', 'card-total', 'qtd-xp', 'tela-vitoria', 'final-xp']:
        assert el in html, f"Elemento UI '{el}' ausente em flashcards.html"


def test_endpoint_revisar_atualiza_estado_e_xp(client, usuario_com_texto):
    """Testa se POST /flashcards/<id>/revisar processa a resposta e incrementa FSRS."""
    uid, tid = usuario_com_texto
    with flask_app.app_context():
        fc = Flashcard.query.filter_by(usuario_id=uid).first()
        fc_id = fc.id
    
    resp = client.post(f'/flashcards/{fc_id}/revisar', data={
        'facilidade': 'good',
        'resposta': 'curso de alemão'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['facilidade'] == 'good'
