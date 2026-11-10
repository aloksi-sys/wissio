"""Testes unitários do pipeline de tradução DE -> PT-BR.

Valida que:
- As palavras-alvo (Deutschkurs, Ansprechpartner, breit, Kommunikation, Angebot)
  NUNCA retornam a própria palavra alemã como "tradução".
- As traduções contêm texto em português real (via busca de palavras-chave).
- O sistema degrada graciosamente com as APIs externas fora do ar.
- Caracteres alemães (ä, ö, ü, ß) são tratados corretamente.
- Heurísticas morfológicas (plural/declinação) e quebra de compostos funcionam.
"""

import pytest
import translation
from translation import translate_with_definition


# Palavras-alvo citadas pelo usuário + palavras-chave esperadas na tradução
PALAVRAS_ALVO = {
    'Deutschkurs': 'curso de alemão',
    'Ansprechpartner': 'contato',
    'breit': 'largo',
    'Kommunikation': 'comunicação',
    'Angebot': 'oferta',
}


@pytest.fixture(autouse=True)
def limpar_caches():
    """Garante cache limpo antes de cada teste."""
    translation._CACHE_MEMORIA.clear()
    try:
        from processador import _cache_traducoes
        _cache_traducoes.clear()
    except Exception:
        pass
    yield


@pytest.fixture()
def apis_offline(monkeypatch):
    """Fixture opcional para garantir modo offline total."""
    monkeypatch.setattr(translation, '_traduzir_google', lambda *a, **k: None)
    monkeypatch.setattr(translation, '_traduzir_mymemory', lambda *a, **k: None)


def test_dicionario_local_cobertura_base():
    """Garante que as palavras críticas estão no dicionário local."""
    for palavra in PALAVRAS_ALVO:
        # A busca deve ser em minúsculas
        assert translation._TRADUCOES_LOCAIS_PT.get(palavra.lower()), \
            f"'{palavra}' ausente do dicionário local"


def test_palavras_alvo_traducao_real(apis_offline):
    """Valida que as palavras alvo retornam tradução em português e não o original."""
    for palavra, esperado in PALAVRAS_ALVO.items():
        trad, _ = translate_with_definition(palavra)
        assert trad, f"tradução vazia para '{palavra}'"
        # Não pode ser igual ao original
        assert trad.strip().lower() != palavra.strip().lower(), \
            f"'{palavra}' devolveu o próprio original como tradução"
        # Deve conter a palavra-chave em português
        assert esperado.lower() in trad.lower(), \
            f"'{palavra}': esperava substring '{esperado}', obtive '{trad}'"


def test_heuristica_sufixos_plural_declinacao(apis_offline):
    """Testa se a remoção de sufixos (es, s, en) encontra a base no dicionário."""
    casos = {
        'breites': 'largo',           # breit + es
        'Ansprechpartners': 'contato', # ansprechpartner + s
        'Wohnungen': 'apartamento'    # wohnung + en
    }
    for palavra, esperado in casos.items():
        trad, _ = translate_with_definition(palavra)
        assert esperado.lower() in trad.lower(), f"Falha na heurística para '{palavra}'"


def test_quebra_de_compostos_desconhecidos(apis_offline):
    """Testa a quebra de compostos alemães quando a palavra inteira não está no dict."""
    # 'Sprachangebot' (Sprach + Angebot) -> 'oferta de língua/idioma'
    # 'Sprach' em dict -> ? (provavelmente não, mas 'Sprache' sim)
    # Vamos usar 'Deutsch' + 'Angebot' (ambos no dict)
    trad, _ = translate_with_definition('Deutschangebot')
    assert 'oferta' in trad.lower()
    assert 'alemão' in trad.lower() or 'deutsch' in trad.lower()


def test_fallback_rotulado_offline(apis_offline):
    """Garante que palavras desconhecidas recebem rótulo e nunca string vazia/None."""
    trad, _ = translate_with_definition('PalavraTotalmenteInexistente')
    assert trad == 'PalavraTotalmenteInexistente (termo alemão)'
    
    # Termina em 'eln' (padrão de verbo alemão) -> fallback rotulado como verbo
    trad_v, _ = translate_with_definition('xyzeln')
    assert 'xyzeln' in trad_v
    assert '(verbo)' in trad_v


def test_tratamento_caracteres_especiais(apis_offline):
    """Valida se umlauts e eszett não quebram o pipeline local."""
    casos = {
        'schön': 'bonito',
        'Mutter': 'mãe',
        'Straße': 'rua'
    }
    for palavra, esperado in casos.items():
        trad, _ = translate_with_definition(palavra)
        assert esperado.lower() in trad.lower(), f"Falha com caractere especial em '{palavra}'"


def test_sanity_check_validar_traducao():
    from translation import _validar_traducao
    assert _validar_traducao('Deutschkurs', 'Curso de Alemão') is True
    assert _validar_traducao('Deutschkurs', 'Deutschkurs') is False
    assert _validar_traducao('Online', 'Online') is True # Internacional
    assert _validar_traducao('bus', 'bus') is True # Internacional
