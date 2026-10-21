import requests
import sys
import json
from datetime import datetime
from models import TranslationCache, db

# Endpoints públicos gratuitos (sem chave)
LIBRETRANSLATE_URL = "https://libretranslate.de/translate"
DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

def _normalize(text: str) -> str:
    """Remove espaços excessivos e normaliza quebras de linha."""
    return " ".join(text.strip().split())

def _fetch_translation(text: str, src: str = "pt", tgt: str = "en") -> str:
    try:
        payload = {
            "q": text,
            "source": src,
            "target": tgt,
            "format": "text"
        }
        resp = requests.post(LIBRETRANSLATE_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("translatedText", "")
    except Exception as e:
        print(f"DEBUG TRANSLATE: Erro no LibreTranslate: {e}")
        sys.stdout.flush()
        return ""  # Fallback: retornar vazio se falhar

def _fetch_definition(word: str) -> str | None:
    resp = requests.get(f"{DICTIONARY_API_URL}{word.lower()}", timeout=10)
    if resp.status_code != 200:
        return None
    try:
        result = resp.json()
        return result[0]["meanings"][0]["definitions"][0]["definition"]
    except Exception:
        return None

def translate_with_definition(text: str, src: str = "pt", tgt: str = "en"):
    """Tradução + definição (quando a tradução for uma palavra única).
    Usa cache interno para evitar chamadas repetidas.
    """
    text = _normalize(text)
    # Verifica cache
    cached = (
        TranslationCache.query
        .filter_by(src_text=text, src_lang=src, tgt_lang=tgt)
        .first()
    )
    if cached:
        return cached.translated, cached.definition

    # 1) Tradução
    translated = _fetch_translation(text, src, tgt)

    # 2) Definição – só tenta se a tradução for uma única palavra
    definition = None
    if " " not in translated.strip():
        definition = _fetch_definition(translated.strip())

    # 3) Persiste no cache (somente se traduziu algo diferente)
    if translated != text:
        cache_entry = TranslationCache(
            src_text=text,
            src_lang=src,
            tgt_lang=tgt,
            translated=translated,
            definition=definition,
        )
        db.session.add(cache_entry)
        db.session.commit()
    return translated, definition
