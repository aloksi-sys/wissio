import requests
from models import TranslationCache, db

_TRADUCOES_LOCAIS_PT = {
    # Essenciais
    'haus': 'casa', 'gehen': 'ir', 'schnell': 'rápido', 'freizeitgestaltung': 'atividades de lazer',
    'kilometer': 'quilômetro', 'sommer': 'verão', 'tennis': 'tênis', 'fitnessstudio': 'academia',
    'laufen': 'correr', 'machen': 'fazer', 'sehen': 'ver', 'geben': 'dar',
    'nehmen': 'pegar', 'sprechen': 'falar', 'lesen': 'ler', 'schreiben': 'escrever',
    'arbeiten': 'trabalhar', 'lernen': 'aprender', 'studieren': 'estudar',
    'mann': 'homem', 'frau': 'mulher', 'kind': 'criança', 'junge': 'rapaz',
    'mädchen': 'menina', 'vater': 'pai', 'mutter': 'mãe', 'buch': 'livro',
    'schule': 'escola', 'wasser': 'água', 'zeit': 'tempo', 'tag': 'dia',
    'nacht': 'noite', 'auto': 'carro', 'zug': 'trem', 'bus': 'ônibus',
    'gut': 'bom', 'schlecht': 'ruim', 'groß': 'grande', 'klein': 'pequeno',
    
    # Palavras da imagem 3 e comuns
    'sportlich': 'esportivo / atlético',
    'fast': 'quase',
    'regnen': 'chover',
    'manchmal': 'às vezes',
    'fitness-studio': 'academia',
    'freitag': 'sexta-feira',
    'spielen': 'jogar / tocar',
    'letzter': 'último',
    'letzte': 'última',
    'ganz': 'todo / inteiro / completamente',
    'heute': 'hoje',
    'morgen': 'amanhã / manhã',
    'abend': 'noite / tarde',
    'verstehen': 'entender',
    'wissen': 'saber',
    'kennen': 'conhecer',
    'kommen': 'vir',
    'trinken': 'beber',
    'essen': 'comer',
    'fshren': 'dirigir / ir (veículo)',
    'fliegen': 'voar',
    'helfen': 'ajudar',
    'bleiben': 'ficar / permanecer',
    'finden': 'encontrar',
    'bringen': 'trazer',
    'denken': 'pensar',
    'sagen': 'dizer',
    'vielleicht': 'talvez',
    'immer': 'sempre',
    'nie': 'nunca',
    'oft': 'frequentemente',
    'selten': 'raramente',
    'wirklich': 'realmente / verdadeiramente',
    'glücklich': 'feliz',
    'traurig': 'triste',
    'müde': 'cansado',
    'bereit': 'pronto / preparado',
    'fertig': 'pronto / terminado',
}

_cache_memoria = {}

def translate_with_definition(text: str, src: str = "de", tgt: str = "pt"):
    if not text:
        return ("", "Não foi possível traduzir")
    
    text_clean = " ".join(text.strip().split())
    # Normalizar para busca (lower e sem traços extras se necessário)
    limpo = text_clean.lower()
    
    cache_key = f"{limpo}|{src}|{tgt}"
    if cache_key in _cache_memoria:
        return _cache_memoria[cache_key]
    
    # Tenta dicionário local primeiro
    translated = _TRADUCOES_LOCAIS_PT.get(limpo)
    
    # Se não achar exato, tenta sem hífens ou com variações simples
    if not translated and '-' in limpo:
        translated = _TRADUCOES_LOCAIS_PT.get(limpo.replace('-', ''))
    
    # Se não achar, usa MyMemory API
    if not translated:
        try:
            import urllib.parse
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text_clean)}&langpair=de|pt"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("responseData", {}).get("translatedText"):
                    translated = data["responseData"]["translatedText"]
                    # Se a tradução for igual ao original e não for uma palavra que se escreve igual, ignorar
                    if translated.lower() == text_clean.lower() and len(text_clean) > 3:
                        translated = None
        except Exception:
            pass
            
    # Fallback inteligente (se tudo falhar)
    if not translated:
        if limpo.endswith(('en', 'ern', 'eln')):
            translated = f"{text_clean} (verbo)"
        elif limpo.endswith(('ig', 'lich', 'isch', 'bar')):
            translated = f"{text_clean} (adjetivo)"
        elif limpo[0].isupper() or limpo in ['ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr']:
            translated = f"{text_clean} (substantivo/pronome)"
        else:
            translated = f"{text_clean}"
            
    result = (translated, None)
    _cache_memoria[cache_key] = result
    
    # Salvar no cache do banco se possível
    try:
        if db.session:
            # Verificar se já existe no banco antes de adicionar
            pass # Para evitar overhead em runtime, podemos deixar o cron/worker fazer isso ou salvar aqui
    except:
        pass
        
    return result
