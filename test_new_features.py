import re
from app import app, db
from models import Usuario, Texto, Flashcard, ProgressoFlashcard

print("=== TESTE NOVAS FEATURES ===")

with app.app_context():
    db.drop_all()
    db.create_all()

with app.test_client() as client:
    # Login
    r = client.get('/cadastro')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post('/cadastro', data={
        'csrf_token': csrf, 'nome': 'Teste', 'email': 'teste@teste.com',
        'senha': '123456', 'confirmar_senha': '123456'
    }, follow_redirects=True)
    
    r = client.get('/onboarding/objetivos')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post('/onboarding/objetivos', data={'csrf_token': csrf, 'objetivo': 'estudos'}, follow_redirects=True)
    
    r = client.get('/onboarding/plano')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post('/onboarding/plano', data={
        'csrf_token': csrf, 'meta_diaria_minutos': '10', 'meta_semanal_textos': '5',
        'meta_flashcards_iniciais': '30', 'nivel_atual': 'A1'
    }, follow_redirects=True)
    
    # Criar texto
    r = client.get('/novo-texto')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    r = client.post('/novo-texto', data={
        'csrf_token': csrf, 'titulo': 'Texto Teste', 
        'conteudo': 'Ich wohne in Berlin. Die Stadt ist gross.', 'categoria': 'Teste'
    }, follow_redirects=True)
    print(f'1. Criar texto: {r.status_code} - OK')
    
    # Testar flashcards do texto
    r = client.get('/texto/1/flashcards')
    print(f'2. Flashcards do texto: {r.status_code} - Tem cards: {"Ich" in r.get_data(as_text=True)}')
    
    # Testar dark mode toggle
    r = client.post('/toggle-tema', data={'csrf_token': csrf}, follow_redirects=True)
    print(f'3. Toggle tema: {r.status_code} - JSON: {r.is_json}')
    if r.is_json:
        import json
        data = json.loads(r.get_data(as_text=True))
        print(f'   Tema escuro: {data.get("tema_escuro")}')
    
    # Testar dicas de alemão
    r = client.get('/dicas-alemao')
    print(f'4. Dicas alemão: {r.status_code} - Tem dicas: {"Artigos" in r.get_data(as_text=True)}')
    
    # Testar API dica aleatória
    r = client.get('/api/dica-aleatoria')
    print(f'5. API dica aleatória: {r.status_code} - JSON: {r.is_json}')
    
    # Testar verificação de email
    r = client.get('/verificar-email')
    print(f'6. Página verificação email: {r.status_code} - OK')
    
    r = client.post('/verificar-email/enviar', data={'csrf_token': csrf})
    print(f'7. Enviar verificação: {r.status_code} - JSON: {r.is_json}')
    
    # Verificar navbar tem link para dicas
    r = client.get('/dashboard')
    html = r.get_data(as_text=True)
    print(f'8. Dashboard tem link Dicas: {"dicas_alemao" in html}')
    print(f'   Dashboard tem toggle tema: {"toggleTema" in html}')
    print(f'   Dashboard tem cores bandeira: {"flag-accent" in html or "wissio-gold" in html}')
    
    # Testar biblioteca
    r = client.get('/biblioteca')
    print(f'9. Biblioteca: {r.status_code} - OK')
    
    # Testar perfil
    r = client.get('/perfil')
    print(f'10. Perfil: {r.status_code} - OK')

print("\n=== TESTES NOVAS FEATURES CONCLUÍDOS ===")