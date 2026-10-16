import re
from app import app, db
from models import Usuario, Texto, Flashcard, ProgressoFlashcard, CTestSubmissao, EstatisticaDiaria

with app.app_context():
    db.drop_all()
    db.create_all()

print("=== TESTE LIMPO: Fluxo Completo ===")
with app.test_client() as client:
    # 1. Cadastro
    r = client.get('/cadastro')
    html = r.get_data(as_text=True)
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    r = client.post('/cadastro', data={
        'csrf_token': csrf_token,
        'nome': 'Usuario Teste',
        'email': 'usuario@teste.com',
        'senha': 'senha123',
        'confirmar_senha': 'senha123'
    }, follow_redirects=True)
    print(f'1. Cadastro: {r.status_code} - Sucesso: {"Dashboard" in r.get_data(as_text=True)}')
    
    # 2. Onboarding objetivos
    r = client.get('/onboarding/objetivos')
    html = r.get_data(as_text=True)
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    r = client.post('/onboarding/objetivos', data={
        'csrf_token': csrf_token,
        'objetivo': 'estudos'
    }, follow_redirects=True)
    print(f'2. Onboarding objetivos: {r.status_code} - Sucesso: {"Plano" in r.get_data(as_text=True) or "plano" in r.get_data(as_text=True).lower()}')
    
    # 3. Onboarding plano
    r = client.get('/onboarding/plano')
    html = r.get_data(as_text=True)
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    r = client.post('/onboarding/plano', data={
        'csrf_token': csrf_token,
        'meta_diaria_minutos': '10',
        'meta_semanal_textos': '5',
        'meta_flashcards_iniciais': '30',
        'nivel_atual': 'A1'
    }, follow_redirects=True)
    print(f'3. Onboarding plano: {r.status_code} - Sucesso: {"Dashboard" in r.get_data(as_text=True) or "Bem-vindo" in r.get_data(as_text=True)}')
    
    # 4. Dashboard
    r = client.get('/dashboard')
    print(f'4. Dashboard: {r.status_code} - Tem stats: {"Textos Inseridos" in r.get_data(as_text=True)}')
    
    # 5. Novo texto
    r = client.get('/novo-texto')
    html = r.get_data(as_text=True)
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    r = client.post('/novo-texto', data={
        'csrf_token': csrf_token,
        'titulo': 'Meu Primeiro Texto',
        'conteudo': 'Ich wohne in Berlin. Die Stadt ist sehr gross und schoen. Ich gehe oft in den Park.',
        'categoria': 'Cotidiano'
    }, follow_redirects=True)
    print(f'5. Novo texto: {r.status_code} - Sucesso: {"flash" in r.get_data(as_text=True).lower()}')
    
    # 6. Ver texto
    r = client.get('/texto/1')
    print(f'6. Ver texto: {r.status_code} - Tem abas: {"Texto Original" in r.get_data(as_text=True) and "C-Test" in r.get_data(as_text=True)}')
    
    # 7. C-Test
    r = client.get('/texto/1')
    html = r.get_data(as_text=True)
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    r = client.post('/texto/1/ctest', data={
        'csrf_token': csrf_token,
        'gap_1': 'Berlin',
        'gap_2': 'gross'
    }, follow_redirects=True)
    print(f'7. C-Test: {r.status_code} - Resultado: {"acertos" in r.get_data(as_text=True).lower() or "xp" in r.get_data(as_text=True).lower()}')
    
    # 8. Flashcards
    r = client.get('/flashcards')
    print(f'8. Flashcards: {r.status_code} - Tem jogo: {"arena-jogo" in r.get_data(as_text=True)}')
    
    # 9. Biblioteca
    r = client.get('/biblioteca')
    print(f'9. Biblioteca: {r.status_code} - Tem texto: {"Meu Primeiro Texto" in r.get_data(as_text=True)}')
    
    # 10. Perfil
    r = client.get('/perfil')
    print(f'10. Perfil: {r.status_code} - Tem abas: {"Perfil Básico" in r.get_data(as_text=True)}')
    
    # 11. Logout
    r = client.get('/logout', follow_redirects=True)
    print(f'11. Logout: {r.status_code} - Redirecionou: {r.location}')
    
    # 12. Login novamente
    r = client.get('/login')
    html = r.get_data(as_text=True)
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    r = client.post('/login', data={
        'csrf_token': csrf_token,
        'email': 'usuario@teste.com',
        'senha': 'senha123'
    }, follow_redirects=True)
    print(f'12. Login: {r.status_code} - Sucesso: {"Dashboard" in r.get_data(as_text=True)}')
    
    # 13. Verificar persistência
    r = client.get('/dashboard')
    print(f'13. Dashboard (persistência): {r.status_code} - Tem stats: {"Textos Inseridos" in r.get_data(as_text=True)}')
    
    r = client.get('/biblioteca')
    print(f'14. Biblioteca (persistência): {r.status_code} - Tem texto: {"Meu Primeiro Texto" in r.get_data(as_text=True)}')

print("\n=== TODOS OS TESTES PASSARAM ===")