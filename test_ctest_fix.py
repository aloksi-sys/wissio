import re
from app import app, db
from models import Usuario, Texto, CTestSubmissao

with app.app_context():
    db.drop_all()
    db.create_all()
    
    u = Usuario(nome='Teste', email='teste@teste.com')
    u.set_senha('123456')
    db.session.add(u)
    db.session.commit()
    
    from processador import processar_texto_alemao
    conteudo = 'Ich wohne in Berlin. Die Stadt ist gross und schoen.'
    resultado = processar_texto_alemao(conteudo)
    
    texto = Texto(
        titulo='Teste C-Test',
        conteudo_original=conteudo,
        nivel=resultado['nivel'],
        ctest_conteudo=resultado['ctest'],
        usuario_id=u.id
    )
    db.session.add(texto)
    db.session.commit()
    
    print('C-Test salvo:', texto.ctest_conteudo)
    
    # Simular template - extrair gaps sequencialmente
    ctest_words = texto.ctest_conteudo.split()
    gaps_template = []
    for word in ctest_words:
        if '____' in word:
            gaps_template.append(word.split('____')[0])
    
    print('Gaps no template (sequencial):', gaps_template)
    print('Total gaps template:', len(gaps_template))
    
    # Simular submissão com respostas corretas
    respostas = {1: 'Berlin', 2: 'gross'}
    
    # Testar lógica do backend corrigida
    ctest_salvo = texto.ctest_conteudo
    gaps_info = []
    palavras_ctest = ctest_salvo.split()
    
    for idx, word in enumerate(palavras_ctest):
        if '____' in word:
            match = re.match(r'^(.+?)_+', word)
            if match:
                prefixo = match.group(1)
                gaps_info.append({
                    'indice_template': idx + 1,
                    'prefixo': prefixo,
                    'palavra_completa_original': None
                })
    
    palavras_originais = texto.conteudo_original.split()
    palavras_ctest_salvo = ctest_salvo.split()
    
    gap_idx = 0
    for i, (orig, ctest) in enumerate(zip(palavras_originais, palavras_ctest_salvo)):
        if '____' in ctest and gap_idx < len(gaps_info):
            gaps_info[gap_idx]['palavra_completa_original'] = orig.lower().rstrip('.,!?;:')
            gap_idx += 1
    
    print('\nGaps info (backend):')
    for g in gaps_info:
        print(f"  template_pos={g['indice_template']}, prefixo='{g['prefixo']}', esperada='{g['palavra_completa_original']}'")
    
    # Corrigir
    print('\nCorreção:')
    for pos, resp in respostas.items():
        gap_idx = pos - 1
        if 0 <= gap_idx < len(gaps_info):
            gap = gaps_info[gap_idx]
            esperada = gap['palavra_completa_original'] or ''
            resp_norm = resp.lower().strip().rstrip('.,!?;:')
            correta = (resp_norm == esperada or esperada.startswith(resp_norm) or resp_norm.startswith(esperada))
            print(f"  gap_{pos}: usuário='{resp}', esperada='{esperada}', correta={correta}")

print('\n=== TESTE VIA CLIENT ===')
from app import app
with app.test_client() as client:
    # Login
    r = client.get('/login')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post('/login', data={'csrf_token': csrf, 'email': 'teste@teste.com', 'senha': '123456'}, follow_redirects=True)
    
    # Acessar texto
    r = client.get('/texto/1')
    print('Ver texto:', r.status_code)
    
    # Submeter C-Test
    r = client.get('/texto/1')
    html = r.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    
    r = client.post('/texto/1/ctest', data={
        'csrf_token': csrf,
        'gap_1': 'Berlin',
        'gap_2': 'gross'
    }, follow_redirects=True)
    print('C-Test submit:', r.status_code)
    html = r.get_data(as_text=True)
    print('Resultado:', 'acertos' in html.lower() or 'xp' in html.lower())
    if 'acertos' in html.lower():
        import re as regex
        match = regex.search(r'(\d+)/(\d+) acertos.*?(\d+\.?\d*)%.*?\+(\d+)', html)
        if match:
            print(f'  {match.group(1)}/{match.group(2)} acertos ({match.group(3)}%) +{match.group(4)} XP')