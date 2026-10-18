import json
import random
import re



import spacy

try:
    nlp = spacy.load('de_core_news_sm')
except Exception:
    nlp = None

# Palavras funcionais que não valem um flashcard (artigos, preposições,
# conjunções, pronomes, verbos auxiliares). Usadas no plano B, sem spaCy.
_STOPWORDS_ALEMAO = {
    'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'mich', 'dich', 'sich',
    'uns', 'euch', 'mir', 'dir', 'ihm', 'ihn', 'man', 'etwas', 'nichts',
    'und', 'oder', 'aber', 'denn', 'weil', 'dass', 'wenn', 'als', 'wie',
    'auch', 'noch', 'schon', 'nur', 'sehr', 'ganz', 'hier', 'dort', 'dann',
    'nicht', 'kein', 'keine', 'keinen', 'jetzt', 'immer', 'wieder', 'mehr',
    'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem',
    'einer', 'eines', 'zu', 'zum', 'zur', 'im', 'ins', 'am', 'ans', 'vom',
    'bei', 'mit', 'von', 'zu', 'auf', 'aus', 'nach', 'vor', 'über',
    'unter', 'durch', 'für', 'gegen', 'ohne', 'um', 'an', 'in',
    'ist', 'sind', 'war', 'waren', 'bin', 'bist', 'sei', 'seid',
    'hat', 'habe', 'haben', 'hast', 'hatte', 'hatten', 'wird', 'werden',
    'wurde', 'wurden', 'kann', 'kannst', 'können', 'konnte', 'könnte',
    'muss', 'musst', 'müssen', 'musste', 'darf', 'dürfen', 'will', 'willst',
    'wollen', 'wollte', 'soll', 'sollen', 'sollte', 'mag', 'mögen',
    'tue', 'tun', 'tust', 'macht', 'machen', 'mache', 'geht', 'gehen',
    'gehe', 'kommt', 'kommen', 'komme', 'gibt', 'geben', 'gebe',
    'sieht', 'sehen', 'sehe', 'weiß', 'wissen', 'steht', 'stehen',
    # pronomes, adjetivos funcionais e advérbios comuns
    'mein', 'meine', 'meinem', 'meiner', 'meines', 'dein', 'deine',
    'sein', 'seine', 'seiner', 'seines', 'ihrer', 'ihr', 'ihre',
    'unser', 'unsere', 'unserer', 'euer', 'eure', 'meins', 'deins',
    'dieser', 'diese', 'dieses', 'diesem', 'dieser', 'jener', 'jene',
    'welcher', 'welche', 'welches', 'keiner', 'keines',
    'alle', 'allen', 'alles', 'andere', 'anderen', 'viel', 'viele',
    'beide', 'gern', 'gerne', 'mal', 'doch', 'also', 'ja', 'nein',
    'seit', 'wegen', 'bis', 'ab', 'etwa', 'wiederum', 'wenig',
    'the', 'and', 'for', 'with', 'this', 'that',
}


def _frases_do_texto(texto):
    """Quebra o texto em frases (usado como exemplo dos flashcards)."""
    bruto = re.split(r'(?<=[.!?])\s+', texto or '')
    frases = [f.strip() for f in bruto if f and f.strip()]
    return frases or ([texto.strip()] if texto and texto.strip() else [])


def _extrair_flashcards_simples(texto, limite=15):
    """
    Extrai palavras candidatas a flashcard sem depender do spaCy.
    Prioridade 1: substantivos (em alemão começam com maiúscula).
    Prioridade 2: palavras longas (verbos/adjetivos), só se faltar volume.
    """
    frases = _frases_do_texto(texto)

    def exemplo_da(palavra):
        for f in frases:
            if palavra[:6].lower() in f.lower():
                return f
        return ''

    tokens = [t for t in (texto or '').split() if t]

    vistos, cards = set(), []

    def tentar(token, min_len):
        limpa = ''.join(c for c in token if c.isalpha())
        if len(limpa) < min_len:
            return False
        chave = limpa.lower()
        if chave in vistos or chave in _STOPWORDS_ALEMAO:
            return False
        vistos.add(chave)
        cards.append({
            'palavra': limpa,
            'exemplo': exemplo_da(token),
            'tipo': 'Substantivo' if token[:1].isupper() else 'Vocabulário',
        })
        return True

    # 1) substantivos (maiúscula), os mais longos primeiro
    for token in sorted([t for t in tokens if t[:1].isupper()], key=lambda t: -len(t)):
        if len(cards) >= limite:
            return cards
        tentar(token, 4)

    # 2) completar com verbos/adjetivos longos se ainda faltar volume
    restantes = [t for t in tokens if not t[:1].isupper()]
    for token in sorted(restantes, key=lambda t: -len(t)):
        if len(cards) >= limite:
            break
        tentar(token, 5)

    return cards

# Traduções de fallback usadas quando a API online não está disponível
# (offline, limite de requisições, etc.) — palavras muito comuns em textos A1-B1.
_TRADUCOES_LOCAIS = {
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

# Duração máxima de cada chamada à API (segundos)
_TIMEOUT_API = 3

_cache_traducoes = {}


def traduzir_lote(palavras, destino='pt', max_workers=5, budget=8.0):
    """
    Pré-popula o cache com a tradução de várias palavras ao mesmo tempo.
    Usa threads para não pagar a latência de cada chamada sequencialmente.
    `budget` é o tempo total máximo (em segundos) gasto no lote inteiro.
    """
    if not palavras:
        return
    pendentes = [p for p in palavras if p and p.strip().lower() not in _cache_traducoes]
    if not pendentes:
        return

    from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutTimeout

    ex = ThreadPoolExecutor(max_workers=max_workers)
    try:
        futuros = {ex.submit(traduzir_palavra, p, destino): p for p in pendentes}
        try:
            for f in as_completed(futuros, timeout=budget):
                pass
        except FutTimeout:
            pass
        for f, p in futuros.items():
            if f.done():
                try:
                    f.result()
                except Exception:
                    pass
    finally:
        ex.shutdown(wait=False)


def _normalizar_palavra(word):
    """Remove pontuação e converte para minúsculas."""
    return ''.join(c for c in word if c.isalnum()).lower()


def traduzir_palavra(palavra, destino='pt'):
    """
    Traduz uma palavra usando a API gratuita MyMemory (sem chave).
    Faz cache em memória para evitar chamadas repetidas.
    Se a API falhar, usa um dicionário local de palavras comuns.
    Retorna None se não conseguir traduzir.
    """
    if not palavra or not palavra.strip():
        return None

    chave = palavra.strip().lower()
    if chave in _cache_traducoes:
        return _cache_traducoes[chave]

    resultado = _TRADUCOES_LOCAIS.get(chave)

    # API externa removida. Utilizamos apenas o dicionário local.
    # Se a palavra não existir no dicionário, o resultado permanecerá None.
    # O cache ainda será atualizado (com None quando não houver tradução).
    # Não há chamada externa a serviços de terceiros.
    # (A lógica original foi substituída para garantir operação offline e sem limites.)

    # Nunca devolve a própria palavra como "tradução"
    if resultado and resultado.strip().lower() == chave:
        resultado = None

    _cache_traducoes[chave] = resultado
    return resultado


def processar_texto_alemao(texto):
    # Se o modelo do spaCy carregou com sucesso
    if nlp:
        doc = nlp(texto)
        palavras = [token.text for token in doc if token.is_alpha]
        tamanho_medio = sum(len(p) for p in palavras) / len(palavras) if palavras else 0
        
        # Nova heurística de nível (CEFR aproximado) que combina:
        #   • tamanho médio das palavras
        #   • % de palavras longas (>7 caracteres)
        #   • % de palavras que já constam no dicionário local (indicador de vocabulário simples)
        palavras = [token.text for token in doc if token.is_alpha]
        tamanho_medio = sum(len(p) for p in palavras) / len(palavras) if palavras else 0
        longas = [p for p in palavras if len(p) > 7]
        pct_longas = len(longas) / len(palavras) if palavras else 0
        conhecidas = sum(1 for p in palavras if p.lower() in _TRADUCOES_LOCAIS)
        pct_conhecidas = conhecidas / len(palavras) if palavras else 0

        if tamanho_medio < 5:
            nivel = 'A1'
        elif tamanho_medio < 6.5 and pct_longas < 0.1:
            nivel = 'A2'
        elif tamanho_medio < 8 and pct_longas < 0.2:
            nivel = 'B1'
        elif tamanho_medio < 9.5 or pct_longas >= 0.2:
            nivel = 'B2'
        elif tamanho_medio < 11 or pct_conhecidas < 0.4:
            nivel = 'C1'
        else:
            nivel = 'C2'

        flashcards_extraidos = []
        vistas = set()
        limite = 15

        # Rótulos do tipo de palavra (aparecem no verso do cartão estilo Anki)
        tipos = {
            'NOUN': 'Substantivo', 'PROPN': 'Substantivo próprio',
            'VERB': 'Verbo', 'ADJ': 'Adjetivo', 'ADV': 'Advérbio',
        }

        for token in doc:
            if len(flashcards_extraidos) >= limite:
                break
            if token.pos_ not in tipos:
                continue
            lemma = token.lemma_ or token.text
            if len(lemma) <= 3 or lemma.lower() in _STOPWORDS_ALEMAO:
                continue
            if lemma in vistas:
                continue
            vistas.add(lemma)
            flashcards_extraidos.append({
                'palavra': lemma,
                'exemplo': token.sent.text.strip(),
                'tipo': tipos[token.pos_],
            })

        # Sem cards suficientes no spaCy (texto curto) → completa com heurística
        if len(flashcards_extraidos) < 5:
            existentes = {f['palavra'].lower() for f in flashcards_extraidos}
            for extra in _extrair_flashcards_simples(texto, limite=limite):
                if extra['palavra'].lower() not in existentes:
                    flashcards_extraidos.append(extra)
                    if len(flashcards_extraidos) >= limite:
                        break

        # Traduz em paralelo (com cache) para não travar a requisição
        traduzir_lote([f['palavra'] for f in flashcards_extraidos])
        for f in flashcards_extraidos:
            f.setdefault('tipo', 'Vocabulário')
            f['traducao'] = _cache_traducoes.get(f['palavra'].lower())
        # Gerar alternativas (4 opções, 1 correta) para cada flashcard
        palavras_todas = [f['palavra'] for f in flashcards_extraidos]
        for f in flashcards_extraidos:
            correta = f['palavra']
            outras = [p for p in palavras_todas if p != correta]
            # se houver menos de 3 alternativas, completa com palavras aleatórias do dicionário local
            if len(outras) < 3:
                adicionais = random.sample(list(_TRADUCOES_LOCAIS.keys()), 3 - len(outras))
                outras.extend(adicionais)
            distratores = random.sample(outras, 3)
            opcoes = [correta] + distratores
            random.shuffle(opcoes)
            f['alternativas'] = opcoes

        palavras_ctest = []
        respostas_ctest = []  # palavra completa de cada lacuna, na ordem
        contador = 0
        for token in doc:
            word = token.text
            if token.is_alpha and len(word) > 3:
                contador += 1
                if contador % 2 == 0:
                    metade = len(word) // 2
                    palavras_ctest.append(word[:metade] + "____")
                    respostas_ctest.append(word)
                else:
                    palavras_ctest.append(word)
            else:
                palavras_ctest.append(word)

            if token.whitespace_:
                palavras_ctest.append(" ")

        texto_ctest = "".join(palavras_ctest)

    else:
        # Plano B: modelo do spaCy indisponível.
        # Gera os flashcards por heurística (antes ficava vazio).
        nivel = 'A1'
        flashcards_extraidos = _extrair_flashcards_simples(texto, limite=15)
        traduzir_lote([f['palavra'] for f in flashcards_extraidos])
        for f in flashcards_extraidos:
            f.setdefault('tipo', 'Vocabulário')
            f['traducao'] = _cache_traducoes.get(f['palavra'].lower())

        palavras = [p for p in texto.split() if p]
        ctest_lista = []
        respostas_ctest = []
        for i, p in enumerate(palavras):
            if i % 2 == 0 and len(_normalizar_palavra(p)) > 3:
                ctest_lista.append(p[:len(p)//2] + "____")
                respostas_ctest.append(p)
            else:
                ctest_lista.append(p)
        texto_ctest = " ".join(ctest_lista)

    return {
        'nivel': nivel,
        'flashcards': flashcards_extraidos,
        'ctest': texto_ctest,
        'ctest_respostas': respostas_ctest,
    }