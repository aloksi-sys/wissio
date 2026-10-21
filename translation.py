import requests
import sys
import json
from datetime import datetime
from models import TranslationCache, db

# Endpoints públicos gratuitos (sem chave) - tentar múltiplos endpoints
LIBRETRANSLATE_ENDPOINTS = [
    "https://libretranslate.de/translate",
    "https://libretranslate.com/translate",
    "https://translate.limemultitrans.com/translate",
]
DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

# Dicionário local de fallback - palavras comuns em alemão para português
_TRADUCOES_LOCAIS_PT = {
    'haus': 'casa', 'stadt': 'cidade', 'straße': 'rua', 'land': 'país',
    'mann': 'homem', 'frau': 'mulher', 'kind': 'criança', 'tag': 'dia',
    'jahr': 'ano', 'zeit': 'tempo', 'woche': 'semana', 'monat': 'mês',
    'auto': 'carro', 'buch': 'livro', 'tür': 'porta', 'tisch': 'mesa',
    'schule': 'escola', 'universität': 'universidade', 'arbeit': 'trabalho',
    'beruf': 'profissão', 'essen': 'comida', 'wasser': 'água', 'brot': 'pão',
    'kaffee': 'café', 'freund': 'amigo', 'familie': 'família', 'liebe': 'amor',
    'sprache': 'língua', 'wort': 'palavra', 'name': 'nome', 'welt': 'mundo',
    'leben': 'vida', 'hand': 'mão', 'kopf': 'cabeça', 'auge': 'olho',
    'gehen': 'ir', 'kommen': 'vir', 'machen': 'fazer', 'sagen': 'dizer',
    'sehen': 'ver', 'geben': 'dar', 'nehmen': 'pegar', 'wissen': 'saber',
    'wohnen': 'morar', 'reisen': 'viajar', 'lernen': 'aprender', 'sprechen': 'falar',
    'berlin': 'Berlim', 'deutschland': 'Alemanha', 'österreich': 'Áustria',
    'schweiz': 'Suíça', 'wien': 'Viena', 'münchen': 'Munique',
    'gut': 'bom', 'groß': 'grande', 'klein': 'pequeno', 'neu': 'novo',
    'schön': 'bonito', 'schnell': 'rápido', 'langsam': 'devagar',
}

# Dicionário local - anglicismo para português (usado quando tradução não está disponível)
_TRADUCOES_LOCAIS_EN = {
    'house': 'casa', 'city': 'cidade', 'street': 'rua', 'country': 'país',
    'man': 'homem', 'woman': 'mulher', 'child': 'criança', 'day': 'dia',
    'year': 'ano', 'time': 'tempo', 'week': 'semana', 'month': 'mês',
    'car': 'carro', 'book': 'livro', 'door': 'porta', 'table': 'mesa',
    'school': 'escola', 'university': 'universidade', 'work': 'trabalho',
    'profession': 'profissão', 'food': 'comida', 'water': 'água', 'bread': 'pão',
    'coffee': 'café', 'friend': 'amigo', 'family': 'família', 'love': 'amor',
    'language': 'língua', 'word': 'palavra', 'name': 'nome', 'world': 'mundo',
    'life': 'vida', 'hand': 'mão', 'head': 'cabeça', 'eye': 'olho',
    'go': 'ir', 'come': 'vir', 'do/make': 'fazer', 'say': 'dizer',
    'see': 'ver', 'give': 'dar', 'take': 'pegar', 'know': 'saber',
    'live': 'morar', 'travel': 'viajar', 'learn': 'aprender', 'speak': 'falar',
    'Berlin': 'Berlim', 'Germany': 'Alemanha', 'Austria': 'Áustria',
    'Switzerland': 'Suíça', 'Vienna': 'Viena', 'Munich': 'Munique',
    'good': 'bom', 'big': 'grande', 'small': 'pequeno', 'new': 'novo',
    'beautiful': 'bonito', 'fast': 'rápido', 'slow': 'devagar',
}

# Cache de memória para evitar chamadas repetidas
_cache_memoria = {}

def _normalize(text: str) -> str:
    """Remove espaços excessivos e normaliza quebras de linha."""
    return " ".join(text.strip().split())

def _fetch_translation_api(text: str, src: str = "de", tgt: str = "pt") -> str:
    """Tenta tradução via múltiplos endpoints LibreTranslate, retorna vazio se falhar."""
    for endpoint in LIBRETRANSLATE_ENDPOINTS:
        try:
            payload = {
                "q": text,
                "source": src,
                "target": tgt,
                "format": "text"
            }
            resp = requests.post(endpoint, json=payload, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "translatedText" in data:
                return data["translatedText"]
            elif isinstance(data, str):
                # Alguns endpoints retornam a string diretamente
                return data
        except Exception as e:
            print(f"DEBUG TRANSLATE: Erro no {endpoint}: {e}")
            sys.stdout.flush()
            continue
    return ""

def _fetch_definition(word: str) -> str | None:
    """Obtém definição via DictionaryAPI (para palavras em inglês)."""
    if not word:
        return None
    try:
        resp = requests.get(f"{DICTIONARY_API_URL}{word.lower()}", timeout=5)
        if resp.status_code != 200:
            return None
        result = resp.json()
        if result and "meanings" in result[0] and result[0]["meanings"]:
            definitions = result[0]["meanings"][0].get("definitions", [])
            if definitions:
                return definitions[0].get("definition")
    except Exception:
        pass
    return None

def traduzir_palavra_local_de(texto: str) -> str | None:
    """Traduz usando o dicionário local alemão->português (fallback)."""
    if not texto:
        return None
    return _TRADUCOES_LOCAIS_PT.get(texto.lower())

def traduzir_palavra_local_en(texto: str) -> str | None:
    """Traduz usando o dicionário local inglês->português (fallback)."""
    if not texto:
        return None
    return _TRADUCOES_LOCAIS_EN.get(texto.lower())

def translate_with_definition(text: str, src: str = "de", tgt: str = "pt"):
    """
    Tradução + definição (quando a tradução for uma palavra única).
    Usa cache interno e fallback com dicionário local.
    
    Args:
        text: Texto a ser traduzido
        src: Língua de origem (default: 'de' - alemão)
        tgt: Língua de destino (default: 'pt' - português)
    """
    text = _normalize(text)
    
    # Cache de memória
    cache_key = f"{text}|{src}|{tgt}"
    if cache_key in _cache_memoria:
        return _cache_memoria[cache_key]
    
    # Verifica cache no banco
    try:
        cached = (
            TranslationCache.query
            .filter_by(src_text=text, src_lang=src, tgt_lang=tgt)
            .first()
        )
        if cached:
            result = (cached.translated, cached.definition)
            _cache_memoria[cache_key] = result
            return result
    except Exception:
        pass  # Ignorar erros de DB no cache
    
    # 1) Tradução via API LibreTranslate
    translated = _fetch_translation_api(text, src, tgt)
    
    # 2) Se falhar, usar tradução local
    if not translated:
        translated = traduzir_palavra_local_de(text)
        if not translated and src == 'en':
            translated = traduzir_palavra_local_en(text)
        
        if translated:
            # Buscar definição no dicionário em inglês se traduzimos de inglês
            definition = None
            if tgt == 'pt':
                definition = _fetch_definition(translated)
                if not definition:
                    definition = "Definição não encontrada"
            
            try:
                cache_entry = TranslationCache(
                    src_text=text,
                    src_lang=src,
                    tgt_lang=tgt,
                    translated=translated,
                    definition=definition,
                )
                db.session.add(cache_entry)
                db.session.commit()
            except Exception:
                pass
            result = (translated, definition)
            _cache_memoria[cache_key] = result
            return result
    
    # 3) Definição – só tenta se a tradução for uma única palavra
    definition = None
    if translated and " " not in translated.strip():
        definition = _fetch_definition(translated.strip())
    
    # 4) Persiste no cache
    if translated and translated != text:
        try:
            cache_entry = TranslationCache(
                src_text=text,
                src_lang=src,
                tgt_lang=tgt,
                translated=translated,
                definition=definition,
            )
            db.session.add(cache_entry)
            db.session.commit()
        except Exception:
            pass
    
    result = (translated, definition)
    _cache_memoria[cache_key] = result
    return result