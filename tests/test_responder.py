import json
import pytest
from app import app, db
from models import Usuario, Texto, Flashcard, RespostaFlashcard

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            # Reset DB for isolated test
            db.drop_all()
            db.create_all()
        yield client

def test_responder_flashcard(client):
    """Verifica que a rota /flashcards/<id>/responder grava o registro na tabela RespostaFlashcard"""
    # Cria usuário e dados de teste dentro do contexto da aplicação
    from app import app
    with app.app_context():
        u = Usuario(nome='Teste', email='test@example.com')
        u.set_senha('senha123')
        db.session.add(u)
        db.session.flush()
        user_id = u.id

        # Cria texto e flashcard
        texto = Texto(titulo='Teste', conteudo_original='Hallo', nivel='A1', usuario_id=user_id)
        db.session.add(texto)
        db.session.flush()
        text_id = texto.id

        fc = Flashcard(palavra_alemao='Haus', traducao='casa', tipo='substantivo',
                      exemplo='Das Haus ist schön.', usuario_id=user_id,
                      texto_id=text_id)
        db.session.add(fc)
        db.session.commit()
        flashcard_id = fc.id

    # Simula login
    with client.session_transaction() as sess:
        sess['usuario_id'] = user_id

    # Envia resposta correta
    resp = client.post(f'/flashcards/{flashcard_id}/responder', data={'resposta': 'casa'})
    data = json.loads(resp.data)
    assert data['correta'] is True

    # Verifica registro na tabela RespostaFlashcard
    registro = RespostaFlashcard.query.filter_by(usuario_id=user_id, flashcard_id=flashcard_id).first()
    assert registro is not None
    assert registro.resposta_texto == 'casa'
    assert registro.correta is True
