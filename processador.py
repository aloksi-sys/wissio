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
# (offline, limite de requisições, etc.) — expansão para 500+ palavras comuns
_TRADUCOES_LOCAIS = {
    # ===== SUBSTANTIVOS - PESSOAS =====
    'mann': 'homem', 'frau': 'mulher', 'kind': 'criança', 'junge': 'rapaz',
    'mädchen': 'menina', 'vater': 'pai', 'mutter': 'mãe', 'bruder': 'irmão',
    'schwester': 'irmã', 'onkel': 'tio', 'tante': 'tia', 'enkel': 'neto',
    'enkelin': 'neta', 'brüder': 'irmãos', 'schwestern': 'irmãs',
    'familie': 'família', 'person': 'pessoa', 'mensch': 'humano',
    'bewohner': 'habitante', 'eingesehen': 'conhecido',
    
    # ===== SUBSTANTIVOS - CASA/ESPAÇO =====
    'haus': 'casa', 'wohnung': 'apartamento', 'zimmer': 'quarto',
    'bad': 'banheiro', 'küche': 'cozinha', 'schlafzimmer': 'quarto de dormir',
    'badezimmer': 'suíte', 'flur': 'corredor', 'eingang': 'entrada',
    'ausgang': 'saída', 'tür': 'porta', 'fenster': 'janela',
    'tür': 'porta', 'fenster': 'janela', 'tür': 'porta',
    'fussboden': 'piso', 'decke': 'telhado', 'wand': 'parede',
    'kachel': 'azulejo', 'fensterbank': 'encosto da janela',
    
    # ===== LOCALIDADES E COLETIVOS =====
    'stadt': 'cidade', 'ort': 'lugar', 'dorf': 'aldeia', 'gemeinde': 'comunidade',
    'platz': 'praça', 'park': 'parque', 'garten': 'jardim',
    'strasse': 'rua', 'gasse': 'beco', 'allee': 'alcova',
    'bahnhof': 'estação de trem', 'bahnhof': 'estação',
    'flughafen': 'aeroporto', 'hafen': 'porto', 'terminal': 'terminal',
    'schule': 'escola', '_kindergarten': 'guarderija',
    'universitaet': 'universidade', 'hochschule': 'instituto superior',
    'bibliothek': 'biblioteca', 'theater': 'teatro', 'kino': 'cinema',
    'restaurant': 'restaurante', 'café': 'café', 'restaurant': 'restaurante',
    'restaurant': 'restaurante', 'restaurant': 'restaurante',
    'hotel': 'hotel', 'gaststaette': 'estabelecimento',
    'pflegeheim': 'asilo', 'krankenhaus': 'hospital', 'klinik': 'clínica',
    'apotheke': 'farmácia', 'arzt': 'médico', 'aerztin': 'médica',
    
    # ===== TEMPO E DATA =====
    'tag': 'dia', 'nacht': 'noite', 'woche': 'semana', 'monat': 'mês',
    'jahr': 'ano', 'stunde': 'hora', 'minute': 'minuto', 'sekunde': 'segundo',
    'morgen': 'manhã', 'nachmittag': 'tarde', 'abend': 'noite',
    'sonntag': 'domingo', 'montag': 'segunda-feira', 'dienstag': 'terça-feira',
    'mittwoch': 'quarta-feira', 'donnerstag': 'quinta-feira',
    'freitag': 'sexta-feira', 'samstag': 'sábado',
    'frueh': 'cedo', 'spät': 'tarde', 'heute': 'hoje', 'gestern': 'ontem',
    'morgen': 'amanhã', 'jetzt': 'agora', 'damals': 'então',
    'immer': 'sempre', 'nie': 'nunca', 'oft': 'muito', 'selten': 'raramente',
    'herbst': 'outono', 'frühjahr': 'primavera', 'sommer': 'verão', 'winter': 'inverno',
    
    # ===== FÍSICA E CIÊNCIA NATURAL =====
    'wasser': 'água', 'wetter': 'tempo (clima)', 'sonne': 'sol',
    'mond': 'lua', 'sterne': 'estrelas', 'himmel': 'céu', 'wolke': 'nuvem',
    'regen': 'chuva', 'schnee': 'neve', 'wind': 'vento', 'bewoelkt': 'nuvemoso',
    'bewölkt': 'nublado', 'eis': 'gelo', 'frost': 'geada', 'hitze': 'calor',
    'kälte': 'frio', 'regen': 'chuva', 'schnee': 'neve',
    'erde': 'terra', 'baum': 'árvore', 'baumwolle': 'carvalho',
    'blume': 'flor', 'blumen': 'flores', 'gras': 'grama', 'feld': 'campo',
    'wiese': 'centro', 'see': 'lago', 'fluss': 'rio', 'meer': 'mar',
    'insel': 'ilha', 'berg': 'montanha', 'wasserfall': 'cachoeira',
    'wald': 'floresta', 'jungle': 'selva', 'oase': 'oásis',
    
    # ===== NÚMEROS E QUANTIDADE =====
    'eins': 'um', 'zwei': 'dois', 'drei': 'três', 'vier': 'quatro',
    'fuenf': 'cinco', 'sechs': 'seis', 'sieben': 'sete', 'acht': 'oito',
    'neun': 'nove', 'zehn': 'dez', 'elf': 'onze', 'zwolf': 'doze',
    'zwanzig': 'vinte', 'dreissig': 'trinta', 'vierzig': 'quarenta',
    'fuenfzig': 'cinquenta', 'hundert': 'cem', 'tausend': 'mil',
    'einhundert': 'cento', 'zweitausend': 'dois mil',
    'plus': 'mais', 'minus': 'menos', 'mal': 'vezes', 'geteilt': 'dividido',
    
    # ===== OBJETOS E CASA =====
    'buch': 'livro', 'bücher': 'livros', 'auto': 'carro', 'auto': 'carro',
    'rad': 'roda', 'fenster': 'janela', 'tuer': 'porta', 'tisch': 'mesa',
    'stuhl': 'cadeira', 'sessel': 'cadeira', 'kanle': 'cesto',
    'schrank': 'armário', 'kuehlschrank': 'geladeira', 'spuhlloch': 'pia',
    'dusche': 'ducha', 'badewanne': 'banho', 'toilette': 'vaso sanitário',
    'bettdecke': 'lençol', 'bettlaken': 'sáterna', 'bettlebte': 'cama',
    'bild': 'imagem', 'kunst': 'arte', 'malerei': 'pintura', 'bilder': 'imagens',
    'freund': 'amigo', 'freunde': 'amigos', 'gefährte': 'companheiro',
    'leben': 'vida', 'welt': 'mundo', 'erdgebäude': 'edifício',
    'fahrzeug': 'veículo', 'zug': 'trens', 'bus': 'ônibus', 'zug': 'trens',
    'zahnrad': 'dente de moeda', 'rad': 'roda',
    'geld': 'dinheiro', 'pfand': ' garantia', 'kredit': 'crédito',
    'bank': 'banco', 'güterschutz': 'proteção de bens',
    'preis': 'preço', 'kosten': 'custo', 'kostenfrei': 'grátis',
    'extra': 'extra', 'steuer': 'imposto', 'abgaben': 'taxas',
    
    # ===== TEMPO E MOVIMENTO =====
    'zeit': 'tempo', 'augenblick': 'momento', 'eundeutig': 'imediato',
    'spät': 'tarde', 'früh': 'cedo', 'jetzt': 'agora', 'morgen': 'manhã',
    'dann': 'então', 'danach': 'depois', 'wendig': 'immediato',
    'schnell': 'rápido', 'langsam': 'devagar', 'schneller': 'mais rápido',
    'schnelles': 'rapidamente', 'langsamer': 'mais lento',
    'gehen': 'ir', 'kommen': 'vir', 'gehen': 'ir', 'gekommen': 'vindo',
    'geht': 'vai', 'gehr': 'vamos', 'gehen': 'ir', 'ging': 'foi',
    'machen': 'fazer', 'machst': 'fazes', 'macht': 'faz', 'machen': 'fazer',
    'gemacht': 'feito', 'machte': 'faça',
    'sehen': 'ver', 'siehst': 'ves', 'sieht': 'vé', 'gesehen': 'visto',
    'sagen': 'dizer', 'sagst': 'dizes', 'sagt': 'diz', 'gesagt': 'dito',
    'geben': 'dar', ' gibst': 'das', 'gibt': 'dá', 'gegeben': 'dado',
    'nehmen': 'pegar', 'nimmst': 'pegas', 'nimmt': 'pega', 'genommen': 'pego',
    'wissen': 'saber', 'weißt': 'sabes', 'weiß': 'sabe', 'gewusst': 'sabido',
    'denken': 'pensar', 'denkst': 'pensas', 'denkt': 'pensa', 'gedacht': 'pensado',
    'sprechen': 'falar', 'sprichst': 'falantes', 'spricht': 'fala', 'gesprochen': 'falado',
    'hören': 'ouvir', 'hörst': 'oves', 'hört': 'ouve', 'gehört': 'ouvido',
    'lesen': 'ler', 'liest': 'lê', 'lesen': 'ler', 'gelesen': 'lido',
    'schreiben': 'escrever', 'schreibst': 'escreves', 'schreibt': 'escreve', 'geschrieben': 'escrito',
    
    # ===== VERBOS ESSENCIAIS =====
    'werden': 'tornar-se', 'wird': 'torna', 'würden': 'tornariam',
    'können': 'poder', 'kannst': 'podes', 'kann': 'pode', 'konnten': 'puderam',
    'müssen': 'dever', 'musst': 'deveres', 'müssen': 'dever', 'musste': 'deveria',
    'wollen': 'querer', 'willst': 'quere', 'will': 'quere', 'wollten': 'queream',
    'dürfen': 'poder (permitir)', 'möchten': 'gostaria de', 'sollen': 'dever (recomendar)',
    'mögen': 'gostar de', 'magst': 'gostas de', 'mögen': 'gostam de',
    'haben': 'ter', 'hast': 'tens', 'hat': 'tem', 'hatte': 'tinha',
    'sein': 'ser/estar', 'bist': 'és', 'ist': 'é', 'war': 'foi', 'warst': 'foraste',
    'werden': 'ser', 'wurde': 'foi', 'wurden': 'foram',
    'bleiben': 'ficar', 'bleibst': 'ficas', 'bleibt': 'ficam', 'blieb': 'ficou',
    'lassen': 'deixar', 'lässt': 'deixam', 'lasse': 'deixe',
    'folgen': 'seguir', 'helfen': 'ajudar', 'springen': 'pular',
    'laufen': 'correr', 'rennen': 'correr rápido', 'fliegen': 'voar',
    'schwimmen': 'nadar', 'tanzen': 'dançar', 'singen': 'cantar',
    'malen': 'pintar', 'zeichnen': 'desenhar', 'backen': 'assar',
    'kochen': 'cozinhar', 'trinken': 'beber', 'rauchen': 'fumar',
    'schlafen': 'dormir', 'wachen': 'vigiar', 'lachen': 'rir', 'weinen': 'chorrar',
    
    # ===== ADJETIVOS =====
    'gut': 'bom', 'schlecht': 'ruim', 'groß': 'grande', 'klein': 'pequeno',
    'neu': 'novo', 'alt': 'velho', 'schön': 'bonito', 'schwul': 'listo',
    'hell': 'claro', 'dunkel': 'escuro', 'lang': 'longo', 'kurz': 'curto',
    'weit': 'longe', 'nah': 'perto', 'heiß': 'quente', 'kalt': 'frio',
    'fein': 'fino', 'grob': 'grosso', 'dünn': 'magro', 'dick': 'gordo',
    'glücklich': 'feliz', 'traurig': 'triste', 'müde': 'cansado',
    'munter': 'animado', 'wild': 'salvage', 'sanft': 'suave',
    'hart': 'duro', 'weich': 'macio', 'dicht': 'espesso', 'flüssig': 'líquido',
    'sicher': 'seguro', 'unsicher': 'inseguro', 'echt': 'auténtico',
    'falsch': 'falso', 'richtig': 'certo', 'korrekt': 'correto',
    'wichtig': 'importante', 'wichtig': 'significativo', 'wichtig': 'essencial',
    'belanglos': 'insignificante', 'interessant': 'interessante',
    'langweilig': 'entedios', 'spaßig': 'divertido', 'bekannt': 'conhecido',
    
    # ===== ADVERBIOS =====
    'jetzt': 'agora', 'damals': 'então', 'heute': 'hoje', 'gestern': 'ontem',
    'immer': 'sempre', 'nie': 'nunca', 'oft': 'muito', 'selten': 'raramente',
    'schnell': 'rápido', 'langsam': 'devagar', 'leise': 'silenciosamente',
    'laut': 'alto', 'gut': 'bem', 'schlecht': 'mal', 'auch': 'também',
    'selbst': 'próprio', 'noch': 'ainda', 'schon': 'já', 'vielleicht': 'talvez',
    'eventuell': 'eventualmente', 'offenbar': 'evidentemente',
    'hier': 'aqui', 'dort': 'ali', 'dann': 'então', 'warum': 'por quê',
    'wie': 'como', 'wo': 'onde', 'wann': 'quando',
    
    # ===== PRONOMES =====
    'ich': 'eu', 'du': 'tu', 'er': 'ele', 'sie': 'ela', 'es': 'isso',
    'wir': 'nós', 'ihr': 'vocês', 'sie': 'eles/elas', 'man': 'ninguém',
    'mein': 'meu', 'dein': 'teu', 'sein': 'seu', 'ihr': 'vosso',
    'unser': 'nosso', 'euer': 'vosso', 'ihr': 'deles/delas',
    'eigentlich': 'propriamente', 'selbst': 'próprio', 'selbst': 'próprio',
    'was': 'o que', 'wer': 'quem', 'welche': 'qual', 'wessen': 'de quem',
    'dieser': 'este', 'diese': 'esta', 'dieses': 'isto',
    'diesem': 'este (dativo)', 'dieser': 'este (genitivo)', 'jener': 'aquele',
    'jene': 'aquela', 'jenes': 'aquilo',
    
    # ===== PREPOSIÇÕES =====
    'und': 'e', 'oder': 'ou', 'aber': 'mas', 'denn': 'pois', 'weil': 'porque',
    'obwohl': 'embora', 'dass': 'que', 'wenn': 'quando/se', 'falls': 'se',
    'damit': 'para que', 'indem': 'enquanto', 'während': 'enquanto',
    'vor': 'antes de', 'nach': 'depois de', 'seit': 'desde', 'bis': 'até',
    'in': 'em', 'vor': 'em/frente a', 'auf': 'sobre', 'über': 'sobre',
    'unter': 'abaixo de', 'hinten': 'atrás de', 'neben': 'ao lado de',
    'durch': 'através de', 'ohne': 'sem', 'mit': 'com', 'für': 'para',
    'gegen': 'contra', 'zu': 'a/n', 'am': 'no (contrado de an + dem)',
    'an': 'por contato/contato com', 'auf': 'em cima de', 'aus': 'de/fora de',
    'bei': 'em/reúne com', 'mit': 'com', 'nach': 'para/depois de',
    'seit': 'desde/há', 'vor': 'antes de/à frente de',
    
    # ===== ARTICULOS E DEMONSTRATIVOS =====
    'der': 'o (masc. definido)', 'die': 'a/a (fem. definido)', 'das': 'o (neutro definido)',
    'ein': 'um/a (masc. indefinido)', 'eine': 'uma (fem. indefinido)',
    'ein': 'um (neutro indefinido)', 'den': 'o (masc. acusativo)',
    'dem': 'o (masc. dativo)', 'des': 'do (masc. genitivo)',
    'einer': 'uma (fem. dativo)', 'eines': 'de um (neutro genitivo)',
    'kein': 'nenhum', 'keine': 'nenhuma', 'keinen': 'nenhum (acusativo)',
    'dieser': 'este (masc.)', 'diese': 'esta (fem.)', 'dieses': 'isto (neutro)',
    'jener': 'aquele (masc.)', 'jene': 'aquela (fem.)', 'jenes': 'aquilo (neutro)',
    
    # ===== NUMERAIS (COMPLEMENTARES) =====
    'eins': 'um', 'zwei': 'dois', 'drei': 'três', 'vier': 'quatro',
    'fünf': 'cinco', 'sechs': 'seis', 'sieben': 'sete', 'acht': 'oito',
    'neun': 'nove', 'zehn': 'dez', 'elf': 'onze', 'zwölf': 'doze',
    'zwanzig': 'vinte', 'dreißig': 'trinta', 'vierzig': 'quarenta',
    'fünfzig': 'cinquenta', 'sechzig': 'sessenta', 'siebzig': 'setenta',
    'achtzig': 'oitenta', 'neunzig': 'noventa', 'hundert': 'cem',
    'tausend': 'mil', 'einhundert': 'cem', 'zweitausend': 'dois mil',
    
    # ===== EXPRESSÕES COMUNS =====
    'bitte': 'por favor/pode/ser', 'danke': 'obrigado', 'danke schön': 'muito obrigado',
    'hallo': 'olá', 'guten tag': 'bom dia', 'guten morgen': 'bom dia',
    'guten abend': 'boa noite', 'tschüss': 'tchau', 'auf wiedersehen': 'até logo',
    'entschuldigung': 'desculpe', 'nichts': 'nada', 'alles': 'tudo',
    'schon gut': 'já basta', 'na klar': 'claro', 'natürlich': 'naturalmente',
    'übrigens': 'p.S.', 'eigentlich': 'na verdade', 'passen': 'ser adequado/combo',
    'genau': 'exato', 'richtig': 'certo', 'falsch': 'errado',
    
    # ===== PAÍSES =====
    'deutschland': 'Alemanha', 'oesterreich': 'Áustria', 'schweiz': 'Suíça',
    'daenemark': 'Dinamarca', 'norge': 'Noruega', 'sverige': 'Suécia',
    'frankreich': 'França', 'italien': 'Itália', 'spanien': 'Espanha',
    'portugal': 'Portugal', 'polen': 'Polônia', 'tschechien': 'República Tcheca',
    'oesterreich': 'Áustria', 'schweiz': 'Suíça',
    'großbritannien': 'Grã-Bretanha', 'eremiten': 'Eritreia',
    
    # ===== CIDADES FAMOSAS =====
    'berlin': 'Berlim', 'hamburg': 'Hamburgo', 'munchen': 'Munique',
    'cologne': 'Colônia', 'frankfurt': 'Frankfurt', 'stuttgart': 'Stuttgart',
    'düsseldorf': 'Düsseldorf', 'dortmund': 'Dortmund', 'essen': 'Essen',
    'leipzig': 'Leipzig', 'dresden': 'Dresden', 'hanover': 'Hanovre',
    'aachen': 'Aachen', 'bonn': 'Bonny', 'weimar': 'Weimar',
    'kiel': 'Kiel', 'moscow': 'Moscou', 'prag': 'Praga', 'wien': 'Viena',
    
    # ===== GRAMÁTICA E TERMINOS TÉCNICOS =====
    'grammatik': 'gramática', 'satz': 'frase', 'wort': 'palavra',
    'präposition': 'preposição', 'artikel': 'artigo', 'flexion': 'flexão',
    'konzession': 'concessão', 'konjunktion': 'conjunção',
    'artikel': 'artigo', 'determinativum': 'determinado',
    'numeral': 'numeral', 'pronomen': 'pronome', 'adjektivum': 'adjetivo',
    'verbformen': 'formas verbais', 'tempus': 'tempo verbal',
    'modus': 'modo', 'kasus': 'caso verbal', 'nummer': 'número',
    'verb': 'verbo', 'noun': 'substantivo', 'adjective': 'adjetivo',
    'adverb': 'advérbio', 'conjunction': 'conjunção', 'preposition': 'preposição',
    
    # ===== TERMOS DE APRENDIZAGEM =====
    'lernen': 'aprender', 'schule': 'escola', 'buch': 'livro',
    'verstehen': 'entender', 'kenntnis': 'conhecimento', 'erfahrung': 'experiência',
    'praxis': 'prática', 'theorie': 'teoria', 'beispiel': 'exemplo',
    'übung': 'exercício', 'aufgabe': 'tarefa', 'leistung': 'desempenho',
    'kurs': 'curso', 'stunde': 'aula', 'termin': 'sessão',
    'professor': 'professor', 'lehrer': 'professor', 'schüler': 'aluno',
    'schülerin': 'aluna', 'lernende': 'aprendiz',
    'prüfung': 'prova', 'note': 'nota', 'zeugnis': 'certificado',
    'abschluss': 'conclusão', 'bildung': 'educação', 'wissen': 'conhecimento',
    
    # ===== SAÚDE E CORPO =====
    'gesundheit': 'saúde', 'arzt': 'médico', 'ärztin': 'médica',
    'kranke': 'doente', 'krankenhaus': 'hospital', 'pflege': 'cuidado',
    'körper': 'corpo', 'gesund': 'sadio', 'krank': 'doente',
    'hand': 'mão', 'fuß': 'pé', 'kopf': 'cabeça', 'augen': 'olhos',
    'ohren': 'ouvidos', 'nase': 'nariz', 'mond': 'boca', 'zunge': 'língua',
    'hals': 'pescoço', 'rücken': 'costas', 'arm': 'braço',
    'bein': 'perna', 'taille': 'cintura', 'beine': 'pernas',
    'gesicht': 'rosto', 'augen': 'olhos', 'mund': 'boca',
    'zahnbürste': 'cerquilha', 'zahn': 'dente', 'zähne': 'dentes',
    'Haar': 'cabelo', 'Haare': 'cabelos', 'Augen': 'olhos',
    
    # ===== ALIMENTAÇÃO =====
    'brot': 'pão', 'brötchen': 'pão francês', 'kaffee': 'café', 'tee': 'chá',
    'wasser': 'água', 'bier': 'cerveja', 'wein': 'vinho', 'essig': 'vinagre',
    'zucker': 'açúcar', 'salz': 'sal', 'schokolade': 'chocolate',
    'obst': 'fruta', 'gemüse': 'legumes', 'fleisch': 'carne',
    'fisch': 'peixe', 'käse': 'queijo', 'joghurt': 'iogurte',
    'nudeln': 'macarrão', 'reis': 'arroz', 'kartoffel': 'batata',
    'pommes': 'batata frita', 'suppe': 'sopa', 'eintopf': 'estufado',
    'milch': 'leite', 'kakao': 'cocoa', 'zitrone': 'limão',
    
    # ===== TECNOLOGIA =====
    'computer': 'computador', 'rechner': 'computador', 'tastatur': 'teclado',
    'maus': 'mouse', 'bildschirm': 'monitor', 'internet': 'internet',
    'software': 'software', 'programm': 'programa', 'programmierung': 'programação',
    'anwendung': 'aplicação', 'applikation': 'aplicação', 'anwendung': 'app',
    'handy': 'celular', 'telefon': 'telefone', 'telefonie': 'telefonia',
    'smartphone': 'smartphone', 'tablet': 'tablet', 'pc': 'computador',
    'email': 'e-mail', 'nachricht': 'mensagem', 'anruf': 'chamada',
    'datei': 'arquivo', 'ordner': 'pasta', 'speicher': 'armazenamento',
    'daten': 'dados', 'netzwerk': 'rede', 'server': 'servidor',
    
    # ===== ESPORTES E ENTREMANSES =====
    'fußball': 'futebol', 'spiel': 'jogo', 'turnier': 'torneio',
    'sport': 'esporte', 'mannschaft': 'equipe', 'spieler': 'jogador',
    'coach': 'técnico', 'training': 'treino', 'übung': 'exercício',
    'sieg': 'vitória', 'niederlage': 'derrota', 'pott': 'pota',
    'siegerehrung': 'cerimônia de vitória', 'wettkampf': 'competição',
    'leistung': 'desempenho', 'erfolg': 'sucesso', 'pech': 'sorte',
    
    # ===== NATUREZA =====
    'baum': 'árvore', 'blume': 'flor', 'blumen': 'flores', 'gras': 'grama',
    'feld': 'campo', 'wasser': 'água', 'see': 'lago', 'fluss': 'rio',
    'meer': 'mar', 'insel': 'ilha', 'berg': 'montanha', 'berg': 'montanha',
    'wald': 'floresta', 'jungle': 'selva', 'oase': 'oásis',
    'regen': 'chuva', 'schnee': 'neve', 'eis': 'gelo',
    'wind': 'vento', 'wetter': 'tempo', 'bewölkt': 'nublado',
    
    # ===== FINANÇAS E ECONOMIA =====
    'geld': 'dinheiro', 'euro': 'euro', 'dollar': 'dólar', 'pfund': 'libra',
    'schilling': 'esquiling', 'bank': 'banco', 'geld': 'dinheiro',
    'zahlung': 'pagamento', 'betrag': 'valor', 'rechnung': 'conta',
    'rechnungen': 'contas', 'kosten': 'custos', 'preis': 'preço',
    'handel': 'comércio', 'wirtschaft': 'economia', 'unternehmen': 'empresa',
    'arbeit': 'trabalho', 'beruf': 'profissão', 'karriere': 'carreira',
    'gehalt': 'salário', 'lohn': 'salário', 'verdienst': 'renda',
    
    # ===== IDADES =====
    'kind': 'criança', 'jung': 'jovem', 'junge': 'rapaz',
    'mann': 'homem', 'vater': 'pai', 'bruder': 'irmão',
    'frau': 'mulher', 'mutter': 'mãe', 'schwester': 'irmã',
    'kind': 'criança', 'junge': 'rapaz', 'mädchen': 'menina',
    'geburtstag': 'aniversário', 'alter': 'idade', 'alter': 'idade',
    
    # ===== RELAÇÕES FAMILIARES =====
    'vater': 'pai', 'mutter': 'mãe', 'sohn': 'filho', 'tochter': 'filha',
    'bruder': 'irmão', 'schwester': 'irmã', 'onkel': 'tio', 'tante': 'tia',
    'enkel': 'neto', 'enkelin': 'neta', 'großvater': 'avô', 'großmutter': 'avó',
    'familie': 'família', 'verwandt': 'parentesco', 'verwandte': 'parentes',
    
    # ===== AÇÕES COMUNS =====
    'gehen': 'ir', 'kommen': 'vir', 'machen': 'fazer', 'sagen': 'dizer',
    'sehen': 'ver', 'geben': 'dar', 'nehmen': 'pegar', 'wissen': 'saber',
    'denken': 'pensar', 'sprechen': 'falar', 'hören': 'ouvir', 'lesen': 'ler',
    'schreiben': 'escrever', 'denken': 'pensar', 'denken': 'pensar',
    'arbeiten': 'trabalhar', 'studieren': 'estudar', 'lernen': 'aprender',
    'kaufen': 'comprar', 'verkaufen': 'vender', 'holen': 'trazer',
    'bringen': 'trazer', 'werden': 'tornar-se', 'sein': 'ser/estar',
    'bleiben': 'ficar', 'lassen': 'deixar', 'folgen': 'seguir',
    'helfen': 'ajudar', 'springen': 'pular', 'laufen': 'correr',
    'rennen': 'correr rapidamente', 'fliegen': 'voar', 'schwimmen': 'nadar',
    'tanzen': 'dançar', 'singen': 'cantar', 'malen': 'pintar',
    'zeichnen': 'desenhar', 'backen': 'assar', 'kochen': 'cozinhar',
    'trinken': 'beber', 'rauchen': 'fumar', 'schlafen': 'dormir',
    'wachen': 'vigiar', 'lachen': 'rir', 'weinen': 'chorrar',
    'arbeiten': 'trabalhar', 'bearbeiten': 'trabalhar', 'bearbeiten': 'manusear',
    
    # ===== DEMONSTRATIVOS =====
    'dieser': 'este', 'diese': 'esta', 'dieses': 'isto',
    'jener': 'aquele', 'jene': 'aquela', 'jenes': 'aquilo',
    'diesem': 'este (dativo)', 'dieser': 'este (genitivo)',
    'jenseits': 'além disso', 'außer': 'exceto',
    
    # ===== INTERROGATIVOS =====
    'was': 'o que', 'wer': 'quem', 'welche': 'qual', 'wessen': 'de quem',
    'wie': 'como', 'wo': 'onde', 'wann': 'quando', 'warum': 'por quê',
    'wieviel': 'quanto', 'wie viel': 'quanto', 'wie groß': 'qual o tamanho',
    
    # ===== DEMONSTRATIVOS =====
    'dies': 'este', 'jener': 'aquele', 'solcher': 'tal',
    'solche': 'tais', 'solches': 'tanto',
    'dieserweise': 'neste caso', 'solcherweise': 'dessa forma',
    
    # ===== MAIS ADJETIVOS =====
    'interessant': 'interessante', 'langweilig': 'entedios',
    'spaßig': 'divertido', 'bekannt': 'conhecido', 'unbekannt': 'desconhecido',
    'wichtig': 'importante', 'wichtig': 'essencial', 'bedeutend': 'significativo',
    'deutlich': 'claramente', 'unmissverständlich': 'inesperado',
    'offensichtlich': 'evidente', 'verständlich': 'compreensível',
    'schwierig': 'difícil', 'einfach': 'simples', 'komplex': 'complexo',
    
    # ===== RELAÇÕES E CONEXÕES =====
    'wegen': 'por causa de', 'während': 'enquanto', 'obwohl': 'embora',
    'nicht': 'não', 'kein': 'nenhum', 'keine': 'nenhuma',
    'nie': 'nunca', 'nie ... niemals': 'nunca...nunca',
    
    # ===== CONECTORES =====
    'und': 'e', 'oder': 'ou', 'aber': 'mas', 'denn': 'pois',
    'weil': 'porque', 'wenn': 'quando', 'als': 'quando',
    'während': 'enquanto', 'obwohl': 'embora', 'damit': 'para que',
    
    # ===== ADRESSAS E CONDOMÍNIOS =====
    'strasse': 'rua', 'hausnummer': 'número da casa', 'postleitzahl': 'CEP',
    'ort': 'cidade', 'plz': 'CEP', 'adresse': 'endereço',
    'haus': 'casa', 'wohnung': 'apartamento', 'haus': 'casa',
    'hausgang': 'corredor da casa', 'haustrakt': 'edifício residencial',
    
    # ===== OUTROS SUBSTANTIVOS =====
    'auto': 'carro', 'bus': 'ônibus', 'zug': 'trens', 'flugzeug': 'avião',
    'schiff': 'navio', 'boot': 'barco', 'fähre': 'ferry',
    'rad': 'bicicleta', 'fahrrad': 'bicicleta', 'motorrad': 'motocicleta',
    'schiff': 'navio', 'boot': 'barco', 'ferry': 'ferry',
    'haus': 'casa', 'wohnung': 'apartamento', 'zimmer': 'quarto',
    'bad': 'banheiro', 'küche': 'cozinha', 'schlafzimmer': 'quarto de dormir',
    'garage': 'garagem', 'pf Garage': 'garagem', 'abstellraum': 'armário',
    
    # ===== CONCEITOS ABSTRATOS =====
    'freiheit': 'liberdade', 'gerechtigkeit': 'justiça', 'frieden': 'paz',
    'krieg': 'guerra', 'mensch': 'humano', 'menschlichkeit': 'humanidade',
    'verantwortung': 'responsabilidade', 'chance': 'chance', 'möglichkeit': 'oportunidade',
    'zeit': 'tempo', 'augenblick': 'momento', 'eundeutig': 'imediato',
    'spät': 'tarde', 'früh': 'cedo', 'jetzt': 'agora',
    'guten morgen': 'bom dia', 'guten tag': 'boa tarde',
    
    # ===== DISCIPLINAS ACADÊMICAS =====
    'mathe': 'matemática', 'physik': 'física', 'chemie': 'química',
    'biologie': 'biologia', 'geschichte': 'história', 'geschichte': 'história',
    'geografie': 'geografia', 'sprache': 'língua', 'literatur': 'literatura',
    'wissenschaft': 'ciência', 'technik': 'tecnologia', 'kunst': 'arte',
    'musik': 'música', 'sport': 'esporte', 'soziologie': 'sociologia',
    
    # ===== VERBOS COMUNS COM DIFERENTES FORMAS =====
    'haben': 'ter', 'habe': 'tenho', 'hast': 'tens', 'hat': 'tem',
    'haben': 'ter', 'hätten': 'teríamos', 'hättest': 'teríamos',
    'sein': 'ser/estar', 'ist': 'é', 'war': 'foi',
    'sein': 'ser', 'sei': 'seja', 'seien': 'sejam',
    'werden': 'tornar-se', 'wird': 'torna', 'würden': 'tornariam',
    'können': 'poder', 'kann': 'pode', 'könnten': 'poderiam',
    'müssen': 'dever', 'muss': 'devo', 'müssten': 'deveríamos',
    'wollen': 'querer', 'will': 'quero', 'wollten': 'queríamos',
    'dürfen': 'poder (permitir)', 'darf': 'pode (permitir)', 'dürften': 'poderiam (permitir)',
    'mögen': 'gostar de', 'mag': 'gosto de', 'mögen': 'gostam de',
}

# Duração máxima de cada chamada à API (segundos)
_TIMEOUT_API = 3

_cache_traducoes = {}


from translation import translate_with_definition

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
    
    def traduzir_ou_cache(palavra):
        # Usar cache local primeiro
        chave = palavra.strip().lower()
        if chave in _cache_traducoes:
            return
        # Usar a função robusta de translation.py
        traducao, definicao = translate_with_definition(palavra, src='de', tgt='pt')
        if traducao:
            _cache_traducoes[chave] = traducao

    ex = ThreadPoolExecutor(max_workers=max_workers)
    try:
        futuros = {ex.submit(traduzir_ou_cache, p): p for p in pendentes}
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
    Traduz uma palavra usando dicionário local com heurísticas avançadas.
    Faz cache em memória para evitar chamadas repetidas.
    Retorna sempre uma tradução (mesmo que heurística) quando possível.
    """
    if not palavra or not palavra.strip():
        return None

    chave = palavra.strip().lower()
    if chave in _cache_traducoes:
        return _cache_traducoes[chave]
    
    # 1) Busca exata no dicionário
    resultado = _TRADUCOES_LOCAIS.get(chave)
    
    # 2) Se não achou, tentar heurísticas avançadas
    if not resultado or resultado.strip().lower() == chave:
        # Remover plural comuns
        for sufixo in ['en', 'n', 's', 'es', 'e', 'er']:
            if chave.endswith(sufixo) and len(chave) - len(sufixo) > 2:
                base = chave[:-len(sufixo)]
                if base in _TRADUCOES_LOCAIS:
                    resultado = _TRADUCOES_LOCAIS[base]
                    break
        
        # 3) Tratamento para nome próprio (maiúscula inicial)
        if not resultado and palavra[0].isupper():
            # Nome próprio - não traduzir, marcar como nome
            resultado = f"'{palavra}' (nome próprio alemão)"
        
        # 4) Tratamento para palavras compostas longas
        if not resultado and len(chave) > 10:
            for i in range(6, len(chave) - 3):
                parte = chave[-i:]
                if parte in _TRADUCOES_LOCAIS:
                    resultado = f"{palavra} (derivado de {_TRADUCOES_LOCAIS[parte]})"
                    break
        
        # 5) Fallback final: indicar que é termo técnico
        if not resultado:
            resultado = f"{palavra} (termo alemão)"
    
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
            'NOUN': 'Substantivo',
            'VERB': 'Verbo', 
            'ADJ': 'Adjetivo', 
            'ADV': 'Advérbio',
        }

        for token in doc:
            if len(flashcards_extraidos) >= limite:
                break
            # Ignorar nomes próprios explicitamente
            if token.pos_ == 'PROPN':
                continue
            if token.pos_ not in tipos:
                continue
            lemma = token.lemma_ or token.text
            # Filtro adicional para nomes próprios que o spaCy pode errar o POS mas começam com maiúscula e não são início de frase
            if token.text[0].isupper() and token.i > 0 and doc[token.i-1].text not in ['.', '!', '?']:
                # Provável nome próprio no meio da frase
                if token.pos_ != 'NOUN': # substantivos alemães sempre maiúsculos, então NOUN é ok
                    continue

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

        # Traduz cada flashcard usando a função oficial de tradução
        for f in flashcards_extraidos:
            trad, _ = translate_with_definition(f['palavra'], src='de', tgt='pt')
            f['traducao'] = trad
            f.setdefault('tipo', 'Vocabulário')

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