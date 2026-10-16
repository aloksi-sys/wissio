import re
from app import app, db
from models import Usuario, Texto, CTestSubmissao

with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Criar usuário
    u = Usuario(nome='Teste', email='teste@teste.com')
    u.set_senha('123456')
    db.session.add(u)
    db.session.commit()
    
    # Criar texto via processador (como faz a app real)
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
    
    print('=== TEXTO CRIADO ===')
    print('ID:', texto.id)
    print('Original:', texto.conteudo_original)
    print('C-Test salvo:', texto.ctest_conteudo)
    print()
    
    # Simular o que o template faz - split e procura gaps
    ctest_words = texto.ctest_conteudo.split()
    print('Palavras do C-Test salvo:')
    for i, w in enumerate(ctest_words):
        if '____' in w:
            print(f'  gap_{i+1}: {w}')
    
    print()
    
    # Simular submissão com respostas
    respostas_teste = {
        1: 'Berlin',
        2: 'Stadt', 
        3: 'gross'
    }
    
    # Agora o que o backend faz - reprocessa
    resultado_proc = processar_texto_alemao(texto.conteudo_original)
    ctest_reprocessado = resultado_proc['ctest']
    print('C-Test reprocessado:', ctest_reprocessado)
    print()
    
    # Extração de palavras esperadas (código atual do app.py)
    palavras_originais = texto.conteudo_original.split()
    palavras_ctest_reproc = ctest_reprocessado.split()
    
    print('Palavras originais:', palavras_originais)
    print('Palavras ctest reproc:', palavras_ctest_reproc)
    
    palavras_esperadas = []
    for i, (orig, ctest) in enumerate(zip(palavras_originais, palavras_ctest_reproc)):
        if '____' in ctest and len(orig) > 3:
            palavras_esperadas.append(orig.lower())
    
    print('\nPalavras esperadas (backend):', palavras_esperadas)
    print('Respostas do usuário:', respostas_teste)
    
    # O problema: índices não batem!
    # Template usa gap_1, gap_2, gap_3 baseado no C-Test SALVO
    # Backend espera posições 0, 1, 2 baseado no C-Test REPROCESSADO
    print('\n=== PROBLEMA IDENTIFICADO ===')
    print('Template gaps (baseado no salvo): 1, 2, 3')
    print('Backend espera índices: 0, 1 (apenas 2 lacunas no reprocessado)')