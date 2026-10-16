"""
Remove o banco local (SQLite) para recriar tudo com o schema correto.
Uso: python reset_db.py
"""
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))
ALVOS = ['wissio.db', os.path.join('instance', 'wissio.db')]

print('Removendo bancos locais...')
alguma = False
for path in ALVOS:
    if os.path.exists(path):
        try:
            os.remove(path)
            print('  Removido:', path)
            alguma = True
        except OSError as e:
            print(f'  Nao foi possivel remover {path}: {e}')
        # SQLite pode deixar arquivos auxiliares
        for sufixo in ('-journal', '-wal', '-shm'):
            extra = path + sufixo
            if os.path.exists(extra):
                try:
                    os.remove(extra)
                    print('  Removido:', extra)
                except OSError:
                    pass

if not alguma:
    print('  Nenhum banco encontrado (nada a remover).')
print('OK - agora rode: python test_tudo.py')
