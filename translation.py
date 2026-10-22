import requests
from models import TranslationCache, db

_TRADUCOES_LOCAIS_PT = {
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
}

_cache_memoria = {}

def translate_with_definition(text: str, src: str = "de", tgt: str = "pt"):
    if not text:
        return ("", "Não foi possível traduzir")
    
    text_clean = " ".join(text.strip().split())
    limpo = text_clean.lower()
    
    cache_key = f"{limpo}|{src}|{tgt}"
    if cache_key in _cache_memoria:
        return _cache_memoria[cache_key]
    
    # Tenta dicionário local
    translated = _TRADUCOES_LOCAIS_PT.get(limpo)
    
    # Se não achar, usa MyMemory API ou fallback inteligente
    if not translated:
        try:
            import urllib.parse
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text_clean)}&langpair=de|pt"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("responseData", {}).get("translatedText"):
                    translated = data["responseData"]["translatedText"]
        except Exception:
            pass
            
    if not translated:
        if limpo.endswith(('en', 'ern', 'eln')):
            translated = f"{text_clean} (verbo)"
        elif limpo.endswith(('ig', 'lich', 'isch', 'bar')):
            translated = f"{text_clean} (adjetivo)"
        else:
            translated = f"{text_clean} (substantivo)"
            
    result = (translated, None)
    _cache_memoria[cache_key] = result
    return result
