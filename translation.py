"""
Modulo de traducao WISSIO (DE -> PT-BR).

Estrategia de traducao (em ordem de prioridade):
  1. Dicionario local expandido (carregado de dicionario_alemao_pt.json + base embutida)
  2. Heuristica morfologica (remocao de sufixos de plural/infinitivo)
  3. API externa MyMemory (com timeout curto e degradacao graciosa)
  4. Fallback morfologico (rotulo leve, nunca retorna None/vazio)

Todas as falhas de rede/API sao registradas (print) em vez de serem
mascaradas silenciosamente. O cache em memoria evita chamadas repetidas.
"""
import json
import os
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutTimeout

DICIONARIO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dicionario_alemao_pt.json')

_BASE_LOCAL_PT = {
    'ich': 'eu', 'du': 'tu', 'er': 'ele', 'sie': 'ela', 'es': 'isso', 'wir': 'nos', 'ihr': 'voces',
    'der': 'o', 'die': 'a', 'das': 'o', 'den': 'o', 'dem': 'ao/do', 'des': 'do',
    'ein': 'um', 'eine': 'uma', 'einen': 'um', 'einem': 'um', 'einer': 'uma', 'eines': 'de um',
    'sein': 'ser / estar', 'bin': 'sou / estou', 'bist': 'es / estas', 'ist': 'e / esta',
    'sind': 'somos / estao', 'war': 'foi / era', 'waren': 'foram / eram',
    'haben': 'ter', 'habe': 'tenho', 'hast': 'tens', 'hat': 'tem', 'hatte': 'tinha',
    'koennen': 'poder / conseguir', 'kann': 'pode', 'konnte': 'pode',
    'muessen': 'dever / ter que', 'muss': 'devo / tem que', 'musste': 'teve que',
    'wollen': 'querer', 'will': 'quero / quer', 'wollte': 'queria',
    'sollen': 'dever (recomendacoes)', 'soll': 'deve',
    'duerfen': 'poder (ter permissao)', 'darf': 'pode',
    'moechten': 'gostaria de', 'moechte': 'gostaria',
    'machen': 'fazer', 'mache': 'faco', 'machst': 'fazes', 'macht': 'faz',
    'gemacht': 'feito', 'machte': 'fazia',
    'gehen': 'ir / andar', 'gehe': 'vou', 'gehst': 'vais', 'geht': 'vai', 'ging': 'foi',
    'gegangen': 'ido',
    'kommen': 'vir', 'komme': 'venho', 'kommst': 'vens', 'kommt': 'vem', 'kam': 'veio',
    'gekommen': 'vindo',
    'sehen': 'ver', 'siehe': 'vejo', 'siehst': 'ves', 'sieht': 've', 'sah': 'viu',
    'gesehen': 'visto',
    'geben': 'dar', 'gebe': 'dou', 'gibst': 'das', 'gibt': 'da', 'gab': 'deu', 'gegeben': 'dado',
    'nehmen': 'pegar / tomar', 'nehme': 'pego', 'nimmst': 'pegas', 'nimmt': 'pega',
    'nahm': 'pegou', 'genommen': 'pegado',
    'sprechen': 'falar', 'spreche': 'falo', 'sprichst': 'falas', 'spricht': 'fala',
    'sprach': 'falou', 'gesprochen': 'falado',
    'lesen': 'ler', 'lese': 'leio', 'liest': 'le', 'las': 'leu', 'gelesen': 'lido',
    'schreiben': 'escrever', 'schreibe': 'escrevo', 'schreibst': 'escreves',
    'schreibt': 'escreve', 'schrieb': 'escreveu', 'geschrieben': 'escrito',
    'arbeiten': 'trabalhar', 'arbeite': 'trabalho', 'arbeitest': 'trabalhas',
    'arbeitet': 'trabalha', 'arbeitete': 'trabalhou',
    'lernen': 'aprender / estudar', 'lerne': 'aprendo', 'lernst': 'aprendes',
    'lernt': 'aprende', 'gelernt': 'aprendido',
    'kaufen': 'comprar', 'kaufe': 'compro', 'kaufst': 'compras', 'kauft': 'compra',
    'gekauft': 'comprado',
    'finden': 'encontrar / achar', 'finde': 'encontro', 'findest': 'encontras',
    'findet': 'encontra', 'fand': 'encontrou', 'gefunden': 'encontrado',
    'wohnen': 'morar / residir', 'wohne': 'moro', 'wohnst': 'moras', 'wohnt': 'mora',
    'gewohnt': 'morado',
    'leben': 'viver / morar', 'lebe': 'vivo', 'lebst': 'vives', 'lebt': 'vive',
    'gelebt': 'vivido',
    'spielen': 'jogar / tocar (instrumento)', 'spiele': 'jogo', 'spielst': 'jogas',
    'spielt': 'joga', 'gespielt': 'jogado',
    'essen': 'comer', 'esse': 'como', 'isst': 'comes/come', 'ass': 'comeu',
    'gegessen': 'comido',
    'trinken': 'beber', 'trinke': 'bebo', 'trinkst': 'bebes', 'trinkt': 'bebe',
    'trank': 'bebeu', 'getrunken': 'bebido',
    'schlafen': 'dormir', 'schlafe': 'durmo', 'schlaefst': 'dormes', 'schlaeft': 'dorme',
    'schlief': 'dormiu', 'geschlafen': 'dormido',
    'verstehen': 'entender', 'verstehe': 'entendo', 'verstehst': 'entendeste',
    'versteht': 'entende', 'verstand': 'entendeu', 'verstanden': 'entendido',
    'wissen': 'saber', 'weiss': 'sei', 'weist': 'sabes', 'wusste': 'sabia', 'gewusst': 'sabido',
    'kennen': 'conhecer', 'kenne': 'conheco', 'kennst': 'conheces', 'kannte': 'conhecia',
    'gekannt': 'conhecido',
    'helfen': 'ajudar', 'helfe': 'ajudo', 'hilfst': 'ajudas', 'hilft': 'ajuda',
    'half': 'ajudou', 'geholfen': 'ajudado',
    'laufen': 'correr / andar', 'laufe': 'corro', 'laeufst': 'corres', 'laeuft': 'corre',
    'lief': 'correu', 'gelaufen': 'corrido',
    'regnen': 'chover', 'regnet': 'chove', 'regnete': 'choveu', 'geregnet': 'chovido',
    'bleiben': 'ficar / permanecer', 'bleibe': 'fico', 'bleibst': 'ficas', 'bleibt': 'fica',
    'blieb': 'ficou', 'geblieben': 'ficado',
    'haus': 'casa', 'haeuser': 'casas', 'wohnung': 'apartamento', 'zimmer': 'quarto',
    'bett': 'cama', 'tisch': 'mesa', 'stuhl': 'cadeira', 'fenster': 'janela',
    'tuer': 'porta', 'kueche': 'cozinha', 'buch': 'livro', 'buecher': 'livros',
    'schule': 'escola', 'bibliothek': 'biblioteca', 'auto': 'carro', 'zug': 'trem',
    'bus': 'onibus', 'fahrrad': 'bicicleta', 'flugzeug': 'aviao',
    'bahnhof': 'estacao de trem', 'flughafen': 'aeroporto', 'strasse': 'rua', 'platz': 'praca',
    'stadt': 'cidade', 'land': 'pais / campo', 'dorf': 'vila', 'park': 'parque',
    'wasser': 'agua', 'sonne': 'sol', 'mond': 'lua', 'himmel': 'ceu', 'regen': 'chuva',
    'schnee': 'neve', 'wind': 'vento', 'baum': 'arvore', 'blume': 'flor',
    'mensch': 'ser humano', 'mann': 'homem', 'frau': 'mulher', 'kind': 'crianca',
    'vater': 'pai', 'mutter': 'mae', 'bruder': 'irmao', 'schwester': 'irma',
    'freund': 'amigo', 'freundin': 'amiga', 'lehrer': 'professor', 'schueler': 'aluno',
    'geld': 'dinheiro', 'euro': 'euro', 'preis': 'preco', 'arbeit': 'trabalho',
    'zeit': 'tempo', 'tag': 'dia', 'nacht': 'noite', 'woche': 'semana', 'monat': 'mes',
    'jahr': 'ano', 'stunde': 'hora', 'minute': 'minuto', 'sekunde': 'segundo',
    'morgen': 'manha / amanha', 'sommer': 'verao', 'winter': 'inverno',
    'fruehling': 'primavera', 'herbst': 'outono',
    'gut': 'bom / bem', 'schlecht': 'ruim / mal', 'gross': 'grande', 'klein': 'pequeno',
    'neu': 'novo', 'alt': 'velho', 'schoen': 'bonito / belo', 'haesslich': 'feio',
    'schnell': 'rapido', 'langsam': 'devagar', 'hoch': 'alto', 'niedrig': 'baixo',
    'kalt': 'frio', 'warm': 'quente', 'heiss': 'quente / fervoroso', 'gluecklich': 'feliz',
    'traurig': 'triste', 'muede': 'cansado', 'krank': 'doente', 'gesund': 'saudavel',
    'richtig': 'certo', 'falsch': 'errado', 'einfach': 'simples', 'schwierig': 'dificil',
    'interessant': 'interessante', 'wichtig': 'importante',
    'besonders': 'especial / especialmente', 'sehr': 'muito', 'total': 'totalmente',
    'extrem': 'extremamente', 'fast': 'quase', 'manchmal': 'as vezes', 'immer': 'sempre',
    'nie': 'nunca', 'oft': 'frequentemente', 'selten': 'raramente', 'heute': 'hoje',
    'gestern': 'ontem', 'jetzt': 'agora', 'hier': 'aqui', 'dort': 'la / ali',
    'ueberall': 'em todo lugar', 'nirgendwo': 'em nenhum lugar',
    'und': 'e', 'oder': 'ou', 'aber': 'mas', 'denn': 'pois', 'weil': 'porque',
    'obwohl': 'embora', 'dass': 'que', 'wenn': 'quando / se', 'als': 'quando / como',
    'vor': 'antes / em frente', 'nach': 'depois / para', 'seit': 'desde', 'bis': 'ate',
    'in': 'em', 'auf': 'sobre', 'ueber': 'sobre / acima', 'unter': 'sob / abaixo',
    'mit': 'com', 'fuer': 'para', 'gegen': 'contra', 'zu': 'a / para', 'aus': 'de / fora de',
    'sportlich': 'esportivo / atletico', 'letzter': 'ultimo', 'letzte': 'ultima',
    'ganz': 'todo / inteiro', 'wirklich': 'realmente', 'bereit': 'pronto',
    'fertig': 'terminado / pronto', 'kilometer': 'quilometro', 'sommer': 'verao',
    'fast': 'quase', 'regnen': 'chover',
}

_TRADUCOES_LOCAIS_PT = {}
try:
    if os.path.exists(DICIONARIO_PATH):
        with open(DICIONARIO_PATH, encoding='utf-8') as _f:
            _json_dict = json.load(_f)
        if isinstance(_json_dict, dict):
            for _k, _v in _json_dict.items():
                _k = str(_k).strip().lower()
                _v = str(_v).strip()
                if _k and _v:
                    _TRADUCOES_LOCAIS_PT[_k] = _v
except Exception as _e:
    print(f"[translation] Falha ao carregar dicionario_alemao_pt.json: {_e}", flush=True)
# Base embutida preenche apenas chaves ausentes (fallback de qualidade)
for _k, _v in _BASE_LOCAL_PT.items():
    if _k not in _TRADUCOES_LOCAIS_PT:
        _TRADUCOES_LOCAIS_PT[_k] = _v

_CACHE_MEMORIA = {}


def _log(msg):
    print(f"[translation] {msg}", flush=True)


def _traduzir_google(texto, src='de', tgt='pt'):
    """Camada 2a: endpoint publico do Google Translate (client=gtx)."""
    try:
        url = ("https://translate.googleapis.com/translate_a/single"
               f"?client=gtx&sl={src}&tl={tgt}&dt=t&q={urllib.parse.quote(texto)}")
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            # Formato: [[["tradução","original",...],...],...]
            if (isinstance(data, list) and data and isinstance(data[0], list)):
                partes = [seg[0] for seg in data[0] if isinstance(seg, list) and seg]
                if partes:
                    return "".join(partes).strip()
    except Exception as e:
        _log(f"API Google falhou para '{texto}': {e}")
    return None


def _traduzir_mymemory(texto, src='de', tgt='pt'):
    """Camada 2b: API MyMemory (backup do Google)."""
    try:
        url = ("https://api.mymemory.translated.net/get?q="
               + urllib.parse.quote(texto) + f"&langpair={src}|{tgt}")
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            t_api = (data.get("responseData") or {}).get("translatedText")
            if t_api and t_api.strip():
                t_api = t_api.strip()
                if "QUERY LENGTH" not in t_api.upper():
                    return t_api
    except Exception as e:
        _log(f"API MyMemory falhou para '{texto}': {e}")
    return None


def _quebrar_composto(limpo):
    """Camada 1.5: tenta dividir uma palavra composta alemã em duas partes
    conhecidas do dicionário e combinar as traduções.
    Ex.: 'deutschkurs' -> deutsch (alemão) + kurs (curso) -> 'curso de alemão'.

    Em alemão, o ÚLTIMO elemento é o núcleo do composto, então em português
    ele vem primeiro: "núcleo de modificador".
    """
    if len(limpo) < 7:
        return None
    for i in range(3, len(limpo) - 2):
        esq, direita = limpo[:i], limpo[i:]
        t_esq = _TRADUCOES_LOCAIS_PT.get(esq)
        t_dir = _TRADUCOES_LOCAIS_PT.get(direita)
        if t_esq and t_dir:
            # núcleo (direita) primeiro: "curso de alemão", "oferta de idiomas"
            return f"{t_dir} de {t_esq}"
    return None


def _validar_traducao(original, traduzido):
    """Camada 3 (sanity check): uma tradução 'válida' precisa ser diferente do
    original (salvo internacionais como 'Online', 'Computer')."""
    if not traduzido:
        return False
    trad = " ".join(str(traduzido).split())
    if not trad:
        return False
    # palavras internacionais podem ser idênticas (Computer, Internet, Online)
    _INTERNACIONAIS = {'online', 'computer', 'internet', 'email', 'e-mail',
                       'test', 'teste', 'handy', 'bus', 'taxi', 'park', 'sport'}
    if trad.lower() in _INTERNACIONAIS or original.lower() in _INTERNACIONAIS:
        return True
    return trad.lower() != original.strip().lower()


def translate_with_definition(text, src="de", tgt="pt"):
    if not text:
        return ("", None)

    text_clean = " ".join(text.strip().split())
    limpo = text_clean.lower()

    cache_key = f"{limpo}|{src}|{tgt}"
    if cache_key in _CACHE_MEMORIA:
        return _CACHE_MEMORIA[cache_key]

    translated = None

    # CAMADA 1: dicionario local (exato)
    translated = _TRADUCOES_LOCAIS_PT.get(limpo)
    # 1b) sem hifen
    if not translated and '-' in limpo:
        translated = _TRADUCOES_LOCAIS_PT.get(limpo.replace('-', ''))
    # 1c) remocao de sufixo de plural/infinitivo
    if not translated:
        for suf in ('en', 'n', 's', 'es', 'er', 'e'):
            if limpo.endswith(suf) and len(limpo) - len(suf) > 2:
                base = limpo[:-len(suf)]
                if base in _TRADUCOES_LOCAIS_PT:
                    translated = _TRADUCOES_LOCAIS_PT[base]
                    break
    # 1d) palavra composta alemã (deutschkurs -> curso de alemão)
    if not translated:
        translated = _quebrar_composto(limpo)

    # CAMADA 2: APIs externas (Google primeiro, MyMemory como backup)
    if not translated:
        t_api = _traduzir_google(text_clean, src, tgt)
        if not _validar_traducao(text_clean, t_api):
            # tentar variação em minúsculas antes de desistir (algumas APIs
            # só traduzem substantivos com inicial minúscula)
            t_api = _traduzir_google(limpo, src, tgt)
        if not _validar_traducao(text_clean, t_api):
            t_api = _traduzir_mymemory(text_clean, src, tgt)
        if _validar_traducao(text_clean, t_api):
            translated = t_api

    # CAMADA 3: fallback morfologico — nunca grava tradução idêntica à original
    if not translated:
        if limpo.endswith(('en', 'ern', 'eln')):
            translated = f"{text_clean} (verbo)"
        elif limpo.endswith(('ig', 'lich', 'isch', 'bar', 'sam')):
            translated = f"{text_clean} (adjetivo)"
        else:
            # palavra composta desconhecida: mantém o termo com rótulo claro
            translated = f"{text_clean} (termo alemão)"

    if not translated:
        translated = text_clean or ""

    result = (translated, None)
    _CACHE_MEMORIA[cache_key] = result
    return result


def traduzir_lote(palavras, destino='pt', max_workers=5, budget=8.0):
    if not palavras:
        return
    pendentes = [p for p in palavras if p and p.strip().lower() not in _CACHE_MEMORIA]
    try:
        from processador import _cache_traducoes as _ct
    except Exception:
        _ct = None
    if _ct is not None:
        pendentes = [p for p in pendentes if p.strip().lower() not in _ct]

    if not pendentes:
        if _ct is not None:
            for p in palavras:
                if p and p.strip().lower() in _CACHE_MEMORIA and p.strip().lower() not in _ct:
                    _ct[p.strip().lower()] = _CACHE_MEMORIA[p.strip().lower()][0]
        return

    def traduzir_uma(palavra):
        chave = palavra.strip().lower()
        traducao, _ = translate_with_definition(palavra, src='de', tgt=destino)
        if traducao:
            _CACHE_MEMORIA.setdefault(f"{chave}|de|{destino}", (traducao, None))
            if _ct is not None:
                _ct[chave] = traducao
        return traducao

    ex = ThreadPoolExecutor(max_workers=max_workers)
    try:
        futuros = {ex.submit(traduzir_uma, p): p for p in pendentes}
        try:
            for _ in as_completed(futuros, timeout=budget):
                pass
        except FutTimeout:
            _log(f"traduzir_lote: orcamento de {budget}s esgotado")
        for f, p in futuros.items():
            if f.done():
                try:
                    f.result()
                except Exception as e:
                    _log(f"traduzir_lote: erro ao traduzir '{p}': {e}")
            else:
                chave = p.strip().lower()
                if chave not in _CACHE_MEMORIA:
                    _CACHE_MEMORIA[f"{chave}|de|{destino}"] = (p.strip(), None)
                if _ct is not None and chave not in _ct:
                    _ct[chave] = p.strip()
    finally:
        ex.shutdown(wait=False)

    if _ct is not None:
        for p in palavras:
            if not p:
                continue
            chave = p.strip().lower()
            if chave in _CACHE_MEMORIA and chave not in _ct:
                _ct[chave] = _CACHE_MEMORIA[f"{chave}|de|{destino}"][0]
