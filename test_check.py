import re
from app import app, db
from models import Usuario, Texto, Flashcard, ProgressoFlashcard

with app.app_context():
    db.drop_all()
    db.create_all()

with app.test_client() as client:
    # Cadastro + login
    r = client.get('/cadastro')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post('/cadastro', data={'csrf_token': csrf, 'nome': 'Teste', 'email': 'teste@teste.com', 'senha': '123456', 'confirmar_senha': '123456'}, follow_redirects=True)
    
    r = client.get('/onboarding/objetivos')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post('/onboarding/objetivos', data={'csrf_token': csrf, 'objetivo': 'estudos'}, follow_redirects=True)
    
    r = client.get('/onboarding/plano')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post('/onboarding/plano', data={'csrf_token': csrf, 'meta_diaria_minutos': '10', 'meta_semanal_textos': '5', 'meta_flashcards_iniciais': '30', 'nivel_atual': 'A1'}, follow_redirects=True)
    
    # Criar texto
    r = client.get('/novo-texto')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post('/novo-texto', data={'csrf_token': csrf, 'titulo': 'Texto Teste', 'conteudo': 'Ich wohne in Berlin. Die Stadt ist gross.', 'categoria': 'Teste'}, follow_redirects=True)
    
    # Testar dicas
    r = client.get('/dicas-alemao')
    html = r.get_data(as_text=True)
    print('Dicas status:', r.status_code)
    print('Tem Artigos:', 'Artigos' in html)
    print('Tem Definidos:', 'Definidos' in html)
    print('Tem Casos:', 'Casos' in html)
    print('Tem Verbo:', 'Verbo' in html or 'verb' in html.lower())
    
    # Verificar navbar no dashboard
    r = client.get('/dashboard')
    html = r.get_data(as_text=True)
    print('Dashboard tem /dicas-alemao:', '/dicas-alemao' in html)
    print('Dashboard tem toggleTema:', 'toggleTema' in html)
    print('Dashboard tem flag-accent:', 'flag-accent' in html)
    print('Dashboard tem wissio-gold:', 'wissio-gold' in html)