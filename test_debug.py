from app import app
from processador import processar_texto_alemao

with app.app_context():
    # Testar processador com texto alemão real
    texto = """Ich wohne seit zwei Jahren in Berlin. Die Stadt ist sehr gross und es gibt viele interessante Museen. Am Wochenende gehe ich oft im Park spazieren oder trinke einen Kaffee mit meinen Freunden."""
    
    resultado = processar_texto_alemao(texto)
    print('=== RESULTADO PROCESSADOR ===')
    print('Nivel:', resultado['nivel'])
    print('Flashcards ({}):'.format(len(resultado['flashcards'])))
    for fc in resultado['flashcards']:
        print('  - {}: {}...'.format(fc['palavra'], fc['exemplo'][:60]))
    print()
    print('C-Test (primeiros 300 chars):')
    print(resultado['ctest'][:300])
    print('...')
    
    # Verificar estrutura do C-Test
    print('\n=== ANÁLISE C-TEST ===')
    palavras = resultado['ctest'].split()
    gaps = [p for p in palavras if '____' in p]
    print('Total palavras:', len(palavras))
    print('Lacunas encontradas:', len(gaps))
    print('Exemplos de lacunas:', gaps[:10])