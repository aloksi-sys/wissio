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
    
    # Criar texto
    texto = Texto(
        titulo='Teste C-Test',
        conteudo_original='Ich wohne in Berlin. Die Stadt ist gross.',
        nivel='A1',
        ctest_conteudo='Ich wohne ____ Berlin. Die St____ ist gr____.',
        usuario_id=u.id
    )
    db.session.add(texto)
    db.session.commit()
    
    print('Texto ID:', texto.id)
    print('C-Test salvo:', texto.ctest_conteudo)
    
    # Simular submissão
    from processador import processar_texto_alemao
    resultado = processar_texto_alemao(texto.conteudo_original)
    print('\nC-Test reprocessado:', resultado['ctest'])
    
    # Extrair palavras esperadas
    ctest_original = resultado['ctest']
    palavras_originais = texto.conteudo_original.split()
    palavras_ctest = ctest_original.split()
    
    print('\nPalavras originais:', palavras_originais)
    print('Palavras ctest:', palavras_ctest)
    
    palavras_esperadas = []
    for i, (orig, ctest) in enumerate(zip(palavras_originais, palavras_ctest)):
        if '____' in ctest and len(orig) > 3:
            palavras_esperadas.append(orig.lower())
    
    print('\nPalavras esperadas nas lacunas:', palavras_esperadas)
    print('Total lacunas:', len(palavras_esperadas))