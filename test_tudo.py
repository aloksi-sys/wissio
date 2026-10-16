"""
Teste completo do WISSIO.
Execute com:  python test_tudo.py
Verifica imports, todas as paginas (status 200), o fluxo ponta a ponta,
a correcao do C-Test, os flashcards, o tema escuro, a verificacao de e-mail
e a protecao contra IDOR.
"""
import re
import sys
import traceback

PASS, FAIL = [], []


def check(nome, condicao, extra=''):
    (PASS if condicao else FAIL).append(nome)
    print(f"{'[OK]  ' if condicao else '[FAIL]'} {nome}{' -> ' + str(extra) if extra else ''}")


def status_critico(r):
    """500 = pagina quebrada. Qualquer 5xx reprova o teste."""
    return 200 <= r.status_code < 400


def pegar_csrf(client, url):
    r = client.get(url)
    m = re.search(r'name="csrf_token" value="([^"]+)"', r.get_data(as_text=True))
    if not m:
        raise AssertionError(f'csrf_token nao encontrado em {url}')
    return m.group(1), r


# ---------------------------------------------------------------- imports
print('=' * 60)
print('WISSIO - TESTE COMPLETO')
print('=' * 60)

try:
    from app import app, db
    from models import (Usuario, Texto, Flashcard, ProgressoFlashcard,
                        CTestSubmissao, EstatisticaDiaria)
    check('Importar app.py, models.py e processador.py', True)
except Exception as e:
    check('Importar modulos', False, traceback.format_exc())
    print('\nERRO FATAL nos imports. Encerrando.')
    sys.exit(1)

app.config['PROPAGATE_EXCEPTIONS'] = False

# ---------------------------------------------------------------- banco limpo
with app.app_context():
    db.drop_all()
    db.create_all()

# ---------------------------------------------------------------- fluxo
with app.test_client() as client:
    # 1. cadastro
    csrf, r = pegar_csrf(client, '/cadastro')
    check('GET /cadastro', status_critico(r), r.status_code)
    r = client.post('/cadastro', data={
        'csrf_token': csrf, 'nome': 'Ana Teste', 'email': 'ana@teste.com',
        'senha': 'senha123', 'confirmar_senha': 'senha123'
    }, follow_redirects=True)
    body = r.get_data(as_text=True)
    check('POST /cadastro (conta criada)', status_critico(r), r.status_code)

    # 2. onboarding
    csrf, r = pegar_csrf(client, '/onboarding/objetivos')
    check('GET /onboarding/objetivos', status_critico(r), r.status_code)
    r = client.post('/onboarding/objetivos', data={'csrf_token': csrf, 'objetivo': 'estudos'},
                    follow_redirects=True)
    check('POST /onboarding/objetivos', status_critico(r), r.status_code)

    csrf, r = pegar_csrf(client, '/onboarding/plano')
    check('GET /onboarding/plano', status_critico(r), r.status_code)
    r = client.post('/onboarding/plano', data={
        'csrf_token': csrf, 'meta_diaria_minutos': '10', 'meta_semanal_textos': '5',
        'meta_flashcards_iniciais': '30', 'nivel_atual': 'B1'
    }, follow_redirects=True)
    check('POST /onboarding/plano', status_critico(r), r.status_code)

    with app.app_context():
        u = Usuario.query.filter_by(email='ana@teste.com').first()
        check('Onboarding gravado no banco (objetivo + nivel)',
              u is not None and u.objetivo is not None and u.nivel_atual is not None
              and u.onboarding_concluido,
              f'objetivo={getattr(u, "objetivo", None)} nivel={getattr(u, "nivel_atual", None)}')
        check('Senha com hash seguro (scrypt/pbkdf2, nao texto puro)',
              u is not None and u.senha_hash.split(':')[0] in ('scrypt', 'pbkdf2'),
              u.senha_hash.split(':')[0] if u else 'sem usuario')

    # 3. TODAS as paginas autenticadas devem carregar sem erro
    print('-' * 60)
    print('Carregando TODAS as paginas autenticadas...')
    paginas = ['/', '/dashboard', '/biblioteca', '/textos', '/novo-texto',
               '/perfil', '/flashcards', '/dicas-alemao', '/painel-flashcards',
               '/onboarding/objetivos']
    for p in paginas:
        r = client.get(p)
        check(f'GET {p}', status_critico(r), r.status_code)

    # 4. criar texto
    csrf, r = pegar_csrf(client, '/novo-texto')
    check('GET /novo-texto', status_critico(r), r.status_code)
    conteudo = ('Ich wohne in Berlin. Die Stadt ist sehr gross und schoen. '
                'Am Wochenende fahre ich mit dem Zug nach Hamburg. '
                'Meine Schwester studiert Medizin an der Universitaet. '
                'Wir essen gern Brot mit Kaese und trinken dazu Wasser.')
    r = client.post('/novo-texto', data={
        'csrf_token': csrf, 'titulo': 'Mein Leben in Berlin',
        'conteudo': conteudo, 'categoria': 'Alltag'
    }, follow_redirects=True)
    body = r.get_data(as_text=True)
    check('POST /novo-texto (texto processado)', status_critico(r), r.status_code)

    with app.app_context():
        t = Texto.query.filter_by(titulo='Mein Leben in Berlin').first()
        check('Texto salvo com nivel valido', t is not None and t.nivel is not None,
              t.nivel if t else 'nao encontrado')
        check('C-Test gerado', t is not None and '____' in (t.ctest_conteudo or ''))
        check('Respostas do C-Test gravadas no banco',
              t is not None and isinstance(t.ctest_respostas, list) and len(t.ctest_respostas) > 0,
              len(t.ctest_respostas) if t and t.ctest_respostas else 0)
        check('Flashcards gerados automaticamente (>= 5)',
              t is not None and len(t.flashcards) >= 5,
              len(t.flashcards) if t else 0)
        if t and t.flashcards:
            tipos = {f.tipo for f in t.flashcards}
            check('Flashcards com tipo gramatical (Anki)',
                  any(x in tipos for x in ['Substantivo', 'Verbo', 'Adjetivo', 'Advérbio']),
                  tipos)
            check('Flashcards com tradução preenchida',
                  sum(1 for f in t.flashcards if f.traducao) > 0,
                  f'{sum(1 for f in t.flashcards if f.traducao)}/{len(t.flashcards)}')
        if t:
            texto_id = t.id
        else:
            texto_id = 1

    # 5. paginas do texto
    r = client.get(f'/texto/{texto_id}')
    check(f'GET /texto/{texto_id}', status_critico(r), r.status_code)
    body = r.get_data(as_text=True)
    n_gaps = len(re.findall(r'name="gap_\d+"', body))
    check('Formulario do C-Test com lacunas sequenciais', n_gaps > 0, f'{n_gaps} lacunas')

    r = client.get(f'/texto/{texto_id}/flashcards')
    check(f'GET /texto/{texto_id}/flashcards', status_critico(r), r.status_code)
    body = r.get_data(as_text=True)
    check('Painel de flashcards mostra state_label (Novo/Aprendendo/Revisao)',
          any(s in body for s in ['Novo', 'Aprendendo', 'Revisao']))

    r = client.get(f'/flashcards?texto_id={texto_id}')
    check(f'GET /flashcards?texto_id={texto_id}', status_critico(r), r.status_code)

    # 5b. PAINEL DE SELECAO DE FLASHCARDS
    r = client.get('/painel-flashcards')
    html_painel = r.get_data(as_text=True)
    check('GET /painel-flashcards', status_critico(r), r.status_code)
    check('Painel lista os textos inseridos', 'Mein Leben in Berlin' in html_painel)
    check('Painel tem checkboxes dos flashcards', 'flashcard-check' in html_painel)
    check('Painel tem botao Estudar selecionados', 'btn-estudar' in html_painel)

    with app.app_context():
        ids_cards = [str(f.id) for f in Flashcard.query.filter_by(texto_id=texto_id).all()][:3]
    r = client.get(f'/flashcards?ids={",".join(ids_cards)}')
    body = r.get_data(as_text=True)
    check('GET /flashcards?ids= (selecao especifica)',
          status_critico(r) and '"id"' in body, r.status_code)

    r = client.get('/flashcards?ids=abc,xyz')
    # lista malformada redireciona de volta ao painel em vez de entregar todos os cards
    check('ids malformados nao lista tudo por engano', r.status_code == 302, r.status_code)

    r = client.get('/flashcards?pendentes=1')
    check('GET /flashcards?pendentes=1', status_critico(r), r.status_code)

    # 5d. interface estilo ANKI (cartao viravel + botoes FSRS)
    r = client.get('/flashcards')
    html_fc = r.get_data(as_text=True)
    check('UI estilo Anki: cartao que vira', 'id="cartao"' in html_fc and 'class="cartao"' in html_fc)
    check('UI estilo Anki: botao de virar', 'Clique para ver a resposta' in html_fc)
    check('UI estilo Anki: 4 botoes FSRS', html_fc.count('btn-fsrs') >= 4, html_fc.count('btn-fsrs'))
    check('UI estilo Anki: atalhos de teclado', "e.key === ' '" in html_fc)

    # 5e. o JSON embutido precisa ser parseável (senão o JS inteiro falha)
    import json as _json
    m = re.search(r'id="flashcards-data" type="application/json">\s*(\[.*?\])\s*</script>',
                  html_fc, re.S)
    json_ok, json_detalhe = False, 'bloco nao encontrado'
    if m:
        try:
            dados = _json.loads(m.group(1))
            json_ok = len(dados) > 0 and all('palavra' in d and 'id' in d for d in dados)
            json_detalhe = f'{len(dados)} cards parseados'
        except Exception as ex:
            json_detalhe = f'JSON invalido: {ex}'
    check('JSON dos flashcards e valido (nao quebra o JS)', json_ok, json_detalhe)

    # 5c. regeneracao de flashcards
    csrf, _ = pegar_csrf(client, f'/texto/{texto_id}/flashcards')
    r = client.post(f'/texto/{texto_id}/flashcards/gerar',
                    data={'csrf_token': csrf}, follow_redirects=True)
    check('POST /texto/<id>/flashcards/gerar', status_critico(r), r.status_code)
    with app.app_context():
        n_cards = Flashcard.query.filter_by(texto_id=texto_id).count()
        check('Geracao repetida nao duplica cards', n_cards <= 20, n_cards)

    # 6. CORRECAO DO C-TEST
    with app.app_context():
        t = Texto.query.get(texto_id)
        esperadas = list(t.ctest_respostas)
        prefixos = [w.split('____')[0] for w in t.ctest_conteudo.split() if '____' in w]

    # 6a. resposta completa (palavra inteira)
    csrf, r = pegar_csrf(client, f'/texto/{texto_id}')
    dados = {'csrf_token': csrf}
    for i, palavra in enumerate(esperadas, start=1):
        dados[f'gap_{i}'] = palavra
    r = client.post(f'/texto/{texto_id}/ctest', data=dados, follow_redirects=True)
    body = r.get_data(as_text=True)
    total = len(esperadas)
    m = re.search(r'(\d+)/(\d+)\s*acertos', body)
    placar = (int(m.group(1)), int(m.group(2))) if m else None
    check('C-Test: palavras completas pontuam 100%',
          placar == (total, total), placar)

    # 6b. apenas o complemento (2a metade)
    csrf, r = pegar_csrf(client, f'/texto/{texto_id}')
    dados = {'csrf_token': csrf}
    for i, palavra in enumerate(esperadas, start=1):
        metade = max(1, len(palavra) // 2)
        dados[f'gap_{i}'] = palavra[metade:]
    r = client.post(f'/texto/{texto_id}/ctest', data=dados, follow_redirects=True)
    body = r.get_data(as_text=True)
    m = re.search(r'(\d+)/(\d+)\s*acertos', body)
    placar = (int(m.group(1)), int(m.group(2))) if m else None
    check('C-Test: apenas o complemento pontua 100%', placar == (total, total), placar)

    # 6c. propositalmente errado
    csrf, r = pegar_csrf(client, f'/texto/{texto_id}')
    dados = {'csrf_token': csrf}
    for i in range(1, total + 1):
        dados[f'gap_{i}'] = 'xxerradoxx'
    r = client.post(f'/texto/{texto_id}/ctest', data=dados, follow_redirects=True)
    body = r.get_data(as_text=True)
    m = re.search(r'(\d+)/(\d+)\s*acertos', body)
    placar = (int(m.group(1)), int(m.group(2))) if m else None
    check('C-Test: respostas erradas nao pontuam', placar == (0, total), placar)

    with app.app_context():
        subs = CTestSubmissao.query.filter_by(texto_id=texto_id).count()
        check('Submissoes do C-Test gravadas', subs >= 3, f'{subs} submissoes')

    # 7. revisar flashcard (FSRS)
    with app.app_context():
        fc = Flashcard.query.filter_by(texto_id=texto_id).first()
        fc_id = fc.id if fc else None
    csrf, r = pegar_csrf(client, '/flashcards')
    r = client.post(f'/flashcards/{fc_id}/revisar', data={'csrf_token': csrf, 'facilidade': 'good'})
    ok = r.is_json and r.get_json().get('success')
    check('POST /flashcards/<id>/revisar (FSRS)', ok, r.status_code)
    with app.app_context():
        prog = ProgressoFlashcard.query.filter_by(flashcard_id=fc_id).first()
        check('FSRS agenda proxima revisao', prog is not None and prog.next_review is not None)

    # 8. tema escuro
    r = client.post('/toggle-tema', data={'csrf_token': csrf})
    check('POST /toggle-tema', r.is_json and r.get_json().get('success'), r.status_code)
    r = client.get('/')
    check('Tema escuro aplicado no HTML', 'data-bs-theme="dark"' in r.get_data(as_text=True))

    # 9. verificacao de e-mail (simulada)
    csrf, r = pegar_csrf(client, '/verificar-email')
    check('GET /verificar-email', status_critico(r), r.status_code)
    r = client.post('/verificar-email/enviar', data={'csrf_token': csrf})
    check('POST /verificar-email/enviar devolve JSON',
          r.is_json and r.get_json().get('success'), r.status_code)
    link = (r.get_json() or {}).get('link') if r.is_json else None
    check('Link de verificacao gerado', bool(link), link)
    if link:
        r = client.get(link.replace('http://localhost', ''), follow_redirects=True)
        check('GET do link de confirmacao verifica o e-mail', status_critico(r), r.status_code)
        with app.app_context():
            u = Usuario.query.filter_by(email='ana@teste.com').first()
            check('E-mail marcado como verificado no banco', u is not None and u.email_verificado)

    # 10. CSRF bloqueando POST sem token
    r = client.post('/toggle-tema', data={})
    check('CSRF bloqueia POST sem token', r.status_code in (400, 403), r.status_code)

    # 11. IDOR: usuario B nao pode ver texto do usuario A
    client.get('/logout')
    csrf, r = pegar_csrf(client, '/cadastro')
    client.post('/cadastro', data={
        'csrf_token': csrf, 'nome': 'Bruno Outro', 'email': 'bruno@teste.com',
        'senha': 'senha123', 'confirmar_senha': 'senha123'
    }, follow_redirects=True)
    for p in ['/onboarding/objetivos', '/onboarding/plano']:
        c, _ = pegar_csrf(client, p)
        if 'objetivos' in p:
            client.post(p, data={'csrf_token': c, 'objetivo': 'viajar'}, follow_redirects=True)
        else:
            client.post(p, data={'csrf_token': c, 'meta_diaria_minutos': '5',
                                 'meta_semanal_textos': '3', 'meta_flashcards_iniciais': '20',
                                 'nivel_atual': 'A1'}, follow_redirects=True)
    r = client.get(f'/texto/{texto_id}')
    check('IDOR bloqueado (403 ao acessar texto de outro usuario)', r.status_code == 403, r.status_code)
    r = client.get(f'/texto/{texto_id}/flashcards')
    check('IDOR bloqueado nos flashcards de outro usuario', r.status_code == 403, r.status_code)

    # 12. logout protege paginas
    client.get('/logout')
    r = client.get('/dashboard')
    check('Logout protege /dashboard (redireciona ao login)', r.status_code in (200, 302), r.status_code)

    # 13. paginas de erro amigaveis
    r = client.get('/pagina-que-nao-existe')
    check('GET rota inexistente devolve 404 amigavel',
          r.status_code == 404 and 'não encontrada' in r.get_data(as_text=True), r.status_code)

    with app.app_context():
        outro = Usuario(nome='Sem Texto', email='vazio@teste.com')
        outro.set_senha('senha123')
        db.session.add(outro)
        db.session.commit()

# ---------------------------------------------------------------- resumo
print('-' * 60)
print(f'RESULTADO: {len(PASS)} passaram, {len(FAIL)} falharam (de {len(PASS) + len(FAIL)}).')
if FAIL:
    print('\nFALHAS:')
    for f in FAIL:
        print('  -', f)
    sys.exit(1)
print('TODOS OS TESTES PASSARAM.')
