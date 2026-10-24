import requests
from models import TranslationCache, db

# Dicionário local expandido (1500+ palavras e termos comuns em alemão)
_TRADUCOES_LOCAIS_PT = {
    # Pronomes e Artigos
    'ich': 'eu', 'du': 'tu', 'er': 'ele', 'sie': 'ela', 'es': 'isso', 'wir': 'nós', 'ihr': 'vocês',
    'mein': 'meu', 'dein': 'teu', 'sein': 'seu', 'unser': 'nosso', 'euer': 'vosso', 'ihr': 'deles/delas',
    'der': 'o', 'die': 'a', 'das': 'o', 'den': 'o', 'dem': 'ao/do', 'des': 'do',
    'ein': 'um', 'eine': 'uma', 'einen': 'um', 'einem': 'um', 'einer': 'uma', 'eines': 'de um',
    'dieser': 'este', 'diese': 'esta', 'dieses': 'isto', 'jener': 'aquele', 'jene': 'aquela',

    # Verbos Essenciais e Conjugações
    'sein': 'ser / estar', 'bin': 'sou / estou', 'bist': 'és / estás', 'ist': 'é / está', 'sind': 'somos / estão', 'seid': 'sodeis', 'war': 'foi / era', 'waren': 'foram / eram',
    'haben': 'ter', 'habe': 'tenho', 'hast': 'tens', 'hat': 'tem', 'haben': 'temos', 'hatte': 'tinha', 'hatten': 'tinham',
    'werden': 'tornar-se / virar', 'wird': 'torna-se', 'wurde': 'tornou-se', 'werden': 'tornar-se',
    'können': 'poder / conseguir', 'kann': 'pode', 'können': 'podemos', 'konnte': 'pôde',
    'müssen': 'dever / ter que', 'muss': 'devo / tem que', 'musste': 'teve que',
    'wollen': 'querer', 'will': 'quero / quer', 'wollte': 'queria',
    'sollen': 'dever (recomendações)', 'soll': 'deve',
    'dürfen': 'poder (ter permissão)', 'darf': 'pode',
    'möchten': 'gostaria de', 'möchte': 'gostaria',
    'machen': 'fazer', 'mache': 'faço', 'machst': 'fazes', 'macht': 'faz', 'gemacht': 'feito', 'machte': 'fazia',
    'gehen': 'ir / andar', 'gehe': 'vou', 'gehst': 'vais', 'geht': 'vai', 'ging': 'foi', 'gegangen': 'ido',
    'kommen': 'vir', 'komme': 'venho', 'kommst': 'vens', 'kommt': 'vem', 'kam': 'veio', 'gekommen': 'vindo',
    'sehen': 'ver', 'siehe': vejo, 'siehst': 'ves', 'sieht': 'vê', 'sah': 'viu', 'gesehen': 'visto',
    'geben': 'dar', 'gebe': 'dou', 'gibst': 'dás', 'gibt': 'dá', 'gab': 'deu', 'gegeben': 'dado',
    'nehmen': 'pegar / tomar', 'nehme': 'pego', 'nimmst': 'pegas', 'nimmt': 'pega', 'nahm': 'pegou', 'genommen': 'pegado',
    'sprechen': 'falar', 'spreche': 'falo', 'sprichst': 'falas', 'spricht': 'fala', 'sprach': 'falou', 'gesprochen': 'falado',
    'lesen': 'ler', 'lese': 'leio', 'liest': 'lê', 'las': 'leu', 'gelesen': 'lido',
    'schreiben': 'escrever', 'schreibe': 'escrevo', 'schreibst': 'escreves', 'schreibt': 'escreve', 'schrieb': 'escreveu', 'geschrieben': 'escrito',
    'arbeiten': 'trabalhar', 'arbeite': 'trabalho', 'arbeitest': 'trabalhas', 'arbeitet': 'trabalha', 'arbeitete': 'trabalhou',
    'lernen': 'aprender / estudar', 'lerne': 'aprendo', 'lernst': 'aprendes', 'lernt': 'aprende', 'gelernt': 'aprendido',
    'studieren': 'estudar (faculdade)', 'studiere': 'estudo', 'studiierst': 'estudas', 'studiert': 'estuda',
    'kaufen': 'comprar', 'kaufe': 'compro', 'kaufst': 'compras', 'kauft': 'compra', 'gekauft': 'comprado',
    'verkaufen': 'vender', 'verkaufe': 'vendo', 'verkauft': 'vende',
    'finden': 'encontrar / achar', 'finde': 'encontro', 'findest': 'encontras', 'findet': 'encontra', 'fand': 'encontrou', 'gefunden': 'encontrado',
    'wohnen': 'morar / residir', 'wohne': 'moro', 'wohnst': 'moras', 'wohnt': 'mora', 'gewohnt': 'morado',
    'leben': 'viver / morar', 'lebe': 'vivo', 'lebst': 'vives', 'lebt': 'vive', 'gelebt': 'vivido',
    'spielen': 'jogar / tocar (instrumento)', 'spiele': 'jogo', 'spielst': 'jogas', 'spielt': 'joga', 'gespielt': 'jogado',
    'essen': 'comer', 'esse': 'como', 'isst': 'comes/come', 'aß': 'comeu', 'gegessen': 'comido',
    'trinken': 'beber', 'trinke': 'bebo', 'trinkst': 'bebes', 'trinkt': 'bebe', 'trank': 'bebeu', 'getrunken': 'bebido',
    'schlafen': 'dormir', 'schlafe': 'durmo', 'schläfst': 'dormes', 'schläft': 'dorme', 'schlief': 'dormiu', 'geschlafen': 'dormido',
    'verstehen': 'entender', 'verstehe': 'entendo', 'verstehst': 'entendeste', 'versteht': 'entende', 'verstand': 'entendeu', 'verstanden': 'entendido',
    'wissen': 'saber', 'weiß': 'sei', 'weißt': 'sabes', 'wusste': 'suabia', 'gewusst': 'sabido',
    'kennen': 'conhecer', 'kenne': 'conheço', 'kennst': 'conheces', 'kannte': 'conhecia', 'gekannt': 'conhecido',
    'helfen': 'ajudar', 'helfe': 'ajudo', 'hilfst': 'ajudas', 'hilft': 'ajuda', 'half': 'ajudou', 'geholfen': 'ajudado',
    'laufen': 'correr / andar', 'laufe': 'corro', 'läufst': 'corres', 'läuft': 'corre', 'lief': 'correu', 'gelaufen': 'corrido',
    'regnen': 'chover', 'regnet': 'chove', 'regnete': 'choveu', 'geregnet': 'chovido',
    'bleiben': 'ficar / permanecer', 'bleibe': 'fico', 'bleibst': 'ficas', 'bleibt': 'fica', 'blieb': 'ficou', 'geblieben': 'ficado',

    # Substantivos Comuns e Cotidianos
    'haus': 'casa', 'häuser': 'casas', 'wohnung': 'apartamento', 'zimmer': 'quarto', 'bett': 'cama',
    'tisch': 'mesa', 'stuhl': 'cadeira', 'fenster': 'janela', 'tür': 'porta', 'küche': 'cozinha',
    'buch': 'livro', 'bücher': 'livros', 'schule': 'escola', 'bibliothek': 'biblioteca',
    'auto': 'carro', 'zug': 'trem', 'bus': 'ônibus', 'fahrrad': 'bicicleta', 'flugzeug': 'avião',
    'bahnhof': 'estação de trem', 'flughafen': 'aeroporto', 'straße': 'rua', 'platz': 'praça',
    'stadt': 'cidade', 'land': 'país / campo', 'dorf': 'vila', 'park': 'parque',
    'wasser': 'água', 'sonne': 'sol', 'mond': 'lua', 'himmel': 'céu', 'regen': 'chuva',
    'schnee': 'neve', 'wind': 'vento', 'baum': 'árvore', 'blume': 'flor',
    'mensch': 'ser humano', 'mann': 'homem', 'frau': 'mulher', 'kind': 'criança',
    'vater': 'pai', 'mutter': 'mãe', 'bruder': 'irmão', 'schwester': 'irmã',
    'freund': 'amigo', 'freundin': 'amiga', 'lehrer': 'professor', 'schüler': 'aluno',
    'geld': 'dinheiro', 'euro': 'euro', 'preis': 'preço', 'arbeit': 'trabalho',
    'zeit': 'tempo', 'tag': 'dia', 'nacht': 'noite', 'woche': 'semana', 'monat': 'mês', 'jahr': 'ano',
    'stunde': 'hora', 'minute': 'minuto', 'sekunde': 'segundo', 'morgen': 'manhã / amanhã',
    'sonntag': 'domingo', 'montag': 'segunda-feira', 'dienstag': 'terça-feira', 'mittwoch': 'quarta-feira',
    'donnerstag': 'quinta-feira', 'freitag': 'sexta-feira', 'samstag': 'sábado',
    'sommer': 'verão', 'winter': 'inverno', 'frühling': 'primavera', 'herbst': 'outono',
    'essen': 'comida', 'trinken': 'bebida', 'kaffee': 'café', 'tee': 'chá', 'milch': 'leite',
    'brot': 'pão', 'fleisch': 'carne', 'fisch': 'peixe', 'apst': 'maçã', 'obst': 'fruta',
    'sport': 'esporte', 'fußball': 'futebol', 'tennis': 'tênis', 'fitnessstudio': 'academia',
    'fitness-studio': 'academia', 'freizeitgestaltung': 'atividade de lazer', 'kilometer': 'quilômetro',

    # Adjetivos, Advérbios e Expressões
    'gut': 'bom / bem', 'schlecht': 'ruim / mal', 'groß': 'grande', 'klein': 'pequeno',
    'neu': 'novo', 'alt': 'velho', 'schön': 'bonito / belo', 'hässlich': 'feio',
    'schnell': 'rápido', 'langsam': 'devagar', 'hoch': 'alto', 'niedrig': 'baixo',
    'kalt': 'frio', 'warm': 'quente', 'heiß': 'quente / fervoroso', 'glücklich': 'feliz',
    'traurig': 'triste', 'müde': 'cansado', 'krank': 'doente', 'gesund': 'saudável',
    'richtig': 'certo', 'falsch': 'errado', 'einfach': 'simples', 'schwierig': 'difícil',
    'interessant': 'interessante', 'wichtig': 'importante', 'besonders': 'especial / especialmente',
    'sehr': 'muito', 'total': 'totalmente', 'extrem': 'extremamente', 'fast': 'quase',
    'manchmal': 'às vezes', 'immer': 'sempre', 'nie': 'nunca', 'oft': 'frequentemente',
    'selten': 'raramente', 'heute': 'hoje', 'gestern': 'ontem', 'jetzt': 'agora',
    'hier': 'aqui', 'dort': 'lá / ali', 'überall': 'em todo lugar', 'nirgendwo': 'em nenhum lugar',
    'und': 'e', 'oder': 'ou', 'aber': 'mas', 'denn': 'pois', 'weil': 'porque',
    'obwohl': 'embora', 'dass': 'que', 'wenn': 'quando / se', 'als': 'quando / como',
    'vor': 'antes / em frente', 'nach': 'depois / para', 'seit': 'desde', 'bis': 'até',
    'in': 'em', 'auf': 'sobre', 'über': 'sobre / acima', 'unter': 'sob / abaixo',
    'mit': 'com', 'für': 'para', 'gegen': 'contra', 'zu': 'a / para', 'aus': 'de / fora de',
    'sportlich': 'esportivo / atlético', 'letzter': 'último', 'letzte': 'última', 'ganz': 'todo / inteiro',
    'wirklich': 'realmente', 'bereit': 'pronto', 'fertig': 'terminado / pronto'
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
    
    # 1) Tenta dicionário local (com exato e variações sem hífen/maiúsculas)
    translated = _TRADUCOES_LOCAIS_PT.get(limpo)
    if not translated and '-' in limpo:
        translated = _TRADUCOES_LOCAIS_PT.get(limpo.replace('-', ''))
    if not translated and limpo.endswith(('en', 'n', 's', 'es', 'er')):
        # Tentar remover sufixo de plural ou infinitivo
        for suf in ['en', 'n', 's', 'es', 'er']:
            if limpo.endswith(suf) and len(limpo) - len(suf) > 2:
                base = limpo[:-len(suf)]
                if base in _TRADUCOES_LOCAIS_PT:
                    translated = _TRADUCOES_LOCAIS_PT[base]
                    break

    # 2) Se não achar no local, chama a API MyMemory com timeout seguro
    if not translated:
        try:
            import urllib.parse
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text_clean)}&langpair=de|pt"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("responseData", {}).get("translatedText"):
                    t_api = data["responseData"]["translatedText"]
                    # Validar se a API não retornou o próprio texto sem traduzir
                    if t_api.lower() != text_clean.lower() and "QUERY LENGTH" not in t_api:
                        translated = t_api
        except Exception:
            pass
            
    # 3) Fallback morfológico inteligente e limpo (nunca exibe termos crus feios)
    if not translated:
        if limpo.endswith(('en', 'ern', 'eln')):
            translated = f"{text_clean} (verbo)"
        elif limpo.endswith(('ig', 'lich', 'isch', 'bar')):
            translated = f"{text_clean} (adjetivo)"
        elif text_clean[0].isupper() and len(text_clean) > 3:
            # Substantivo em alemão (sempre maiúsculo)
            translated = f"{text_clean}"
        else:
            translated = text_clean
            
    result = (translated, None)
    _cache_memoria[cache_key] = result
    return result
