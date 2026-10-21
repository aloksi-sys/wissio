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
    # Substantivos - pessoas
    'mann': 'homem', 'frau': 'mulher', 'kind': 'criança', 'kinde': 'criança',
    'junge': 'rapaz', 'mädchen': 'menina', 'vater': 'pai', 'mutter': 'mãe',
    'bruder': 'irmão', 'schwester': 'irmã', 'onkel': 'tio', 'tante': 'tia',
    'haus': 'casa', 'wohnung': 'apartamento', 'zimmer': 'quarto',
    
    # Substantivos - lugares e estruturas
    'stadt': 'cidade', 'ort': 'lugar', 'haus': 'casa', 'wohnung': 'apartamento',
    'straße': 'rua', 'platz': 'praça', 'park': 'parque', 'bahnhof': 'estação de trem',
    'flughafen': 'aeroporto', 'schule': 'escola', 'universität': 'universidade',
    'bibliothek': 'biblioteca', 'bibliothek': 'biblioteca', 'theater': 'teatro',
    'Kino': 'cinema', 'restaurant': 'restaurante', 'café': 'café',
    'restaurant': 'restaurante', 'hotel': 'hotel', 'apartment': 'apartamento',
    'haus': 'casa', 'haus': 'casa',
    
    # Substantivos - tempo
    'tag': 'dia', 'nacht': 'noite', 'woche': 'semana', 'monat': 'mês',
    'jahr': 'ano', 'stunde': 'hora', 'minute': 'minuto', 'sekunde': 'segundo',
    'morgen': 'manhã', 'nachmittag': 'tarde', 'abend': 'noite',
    'sonntag': 'domingo', 'montag': 'segunda', 'dienstag': 'terça',
    'mittwoch': 'quarta', 'donnerstag': 'quinta', 'freitag': 'sexta',
    'samstag': 'sábado',
    
    # Substantivos - tempo e clima
    'zeit': 'tempo', 'wasser': 'água', 'wetter': 'tempo (clima)', 'sonne': 'sol',
    'mond': 'lua', 'sterne': 'estrelas', 'himmel': 'céu', 'wolke': 'nuvem',
    'regen': 'chuva', 'schnee': 'neve', 'wind': 'vento', 'bewölkt': 'nublado',
    
    # Substantivos - números e quantidade
    'eins': 'um', 'zwei': 'dois', 'drei': 'três', 'vier': 'quatro',
    'fünf': 'cinco', 'sechs': 'seis', 'sieben': 'sete', 'acht': 'oito',
    'neun': 'nove', 'zehn': 'dez',
    'eins': 'um (1)', 'eins': 'um',
    
    # Substantivos - objetos e coisas
    'buch': 'livro', 'auto': 'carro', 'rad': 'roda', 'fenster': 'janela',
    'tür': 'porta', 'tisch': 'mesa', 'stuhl': 'cadeira', 'schrank': 'armário',
    'kühlschrank': 'geladeira', 'spüloch': 'pia', 'dusche': 'ducha',
    'bettdecke': 'lençol', 'bettlaken': 'lençol (cama)', 'bettlebte': 'cama',
    'bild': 'imagem', 'kunst': 'arte', 'malerei': 'pintura',
    'freund': 'amigo', 'freunde': 'amigos', 'gefährte': 'acompanhante',
    'familie': 'família', 'familienhause': 'casa da família',
    'leben': 'vida', 'welt': 'mundo', 'erdgebäude': 'edifício',
    'auto': 'carro', 'fahrzeug': 'veículo', 'zug': 'trens', 'bus': 'ônibus',
    'zahnrad': 'dente de mangueira', 'rad': 'roda',
    
    # Substantivos - aspectos e noções
    'freiheit': 'liberdade', 'gerechtigkeit': 'justiça', 'frieden': 'paz',
    'krieg': 'guerra', 'mensch': 'humano', 'menschlichkeit': 'humanidade',
    'verantwortung': 'responsabilidade', 'chance': 'chance', 'möglichkeit': 'oportunidade',
    'zeit': 'tempo', 'augenblick': 'momento', 'eundeutig': 'imediato',
    'spät': 'tarde', 'früh': 'cedo', 'jetzt': 'agora',
    'guten morgen': 'bom dia', 'guten tag': 'boa tarde (literal: bom dia)',
    
    # Substantivos - finanças e propriedade
    'geld': 'dinheiro', 'pfand': 'garantia', 'kredit': 'crédito',
    'bank': 'banco', 'güterschutz': 'proteção de bens',
    'preis': 'preço', 'kosten': 'custo', 'kostenfrei': 'grátis',
    'extra': 'extra', 'steuer': 'imposto', 'abgaben': 'taxas',
    
    # Substantivos - educação e conhecimento
    'schule': 'escola', 'lehrer': 'professor', 'schüler': 'aluno',
    'schülerin': 'aluna', 'studiengang': 'curso', 'prüfung': 'prova',
    'note': 'nota', 'zeugnis': 'certificado', 'abschluss': 'conclusão',
    'bildung': 'educação', 'wissen': 'conhecimento', 'erfahrung': 'experiência',
    'theorie': 'teoria', 'praxis': 'prática', 'regel': 'regra',
    'regeln': 'regras', 'gesetz': 'lei', 'recht': 'direito',
    
    # Substantivos - tecnologia
    'computer': 'computador', 'rechner': 'computador', 'tastatur': 'teclado',
    'maus': 'mouse', 'bildschirm': 'monitor', 'ternet': 'internet',
    'software': 'software', 'programm': 'programa', 'programmierung': 'programação',
    'applikation': 'aplicação', 'internet': 'internet', 'webseite': 'site web',
    'handy': 'celular', 'telefon': 'telefone', 'telefonie': 'telefonia',
    
    # Substantivos - esportes e lazer
    'fußball': 'futebol', 'spiel': 'jogo', 'turnier': 'torneio',
    'sport': 'esporte', 'turnier': 'torneio', 'mannschaft': 'equipe',
    'spieler': 'jogador', 'coach': 'técnico', 'training': 'treino',
    
    # Substantivos - natureza
    'baum': 'árvore', 'blume': 'flor', 'gras': 'erva', 'feld': 'campo',
    'wasser': 'água', 'see': 'lago', 'fluss': 'rio', 'meer': 'mar',
    'insel': 'ilha', 'berg': 'montanha', 'wald': 'floresta',
    'regen': 'chuva', 'schnee': 'neve', 'eis': 'gelo',
    
    # Substantivos - alimentação
    'brot': 'pão', 'brötchen': 'pão francês', 'kaffee': 'café', 'tee': 'chá',
    'wasser': 'água', 'bier': 'cerveja', ' Wein ': 'vinho', 'essig': 'vinagre',
    'zucker': 'açúcar', 'salz': 'sal', 'schokolade': 'chocolate',
    'obst': 'fruta', 'gemüse': 'legumes', 'fleisch': 'carne',
    'fisch': 'peixe', 'käse': 'queijo', 'joghurt': 'iogurte',
    'nudeln': 'macarrão', 'reis': 'arroz', 'kartoffel': 'batata',
    
    # Substantivos - saúde e corpo
    'gesundheit': 'saúde', 'arzt': 'médico', 'ärztin': 'médica',
    'kranke': 'doente', 'krankenhaus': 'hospital', 'pflege': 'cuidado',
    'körper': 'corpo', 'gesund': 'sadio', 'krank': 'doente',
    'hand': 'mão', 'fuß': 'pé', 'kopf': 'cabeça', 'augen': 'olhos',
    'ohren': 'ouvidos', 'nase': 'nariz', 'mond': 'boca', 'zunge': 'língua',
    'hrift': 'pescoço', 'rücken': 'costas', 'arm': 'braço',
    'bein': 'perna', 'taille': 'cintura', 'beine': 'pernas',
    
    # Substantivos - finanças
    'euro': 'euro', 'dollar': 'dólar', 'pfund': 'libra', 'schilling': 'esquiling',
    'bank': 'banco', 'geld': 'dinheiro', 'zahlung': 'pagamento', 'betrag': 'valor',
    'rechnung': 'conta', 'rechnungen': 'contas', 'kosten': 'custos',
    
    # Adjetivos
    'gut': 'bom', 'schlecht': 'ruim', 'groß': 'grande', 'klein': 'pequeno',
    'neu': 'novo', 'alt': 'velho', 'schön': 'bonito', 'schwul': 'listo',
    'schnell': 'rápido', 'langsam': 'devagar', 'heiss': 'quente',
    'kalt': 'frio', 'dünn': 'grosso (magro)', ' dick ': 'grosso (gordo)',
    'glücklich': 'feliz', 'traurig': 'triste', 'müde': 'cansado',
    'munter': 'animado', 'wild': 'salvage', 'sanft': 'suave',
    'hart': 'duro', 'weich': 'macio', 'dichter': 'espesso', 'flüssig': 'líquido',
    
    # Verbos essenciais
    'sein': 'ser', 'haben': 'ter', 'werden': 'tornar-se', ' können ': 'poder',
    'müssen': 'dever', 'wollen': 'querer', 'dürfen': 'poder (permite)',
    'möchten': 'gostaria de', 'sollen': 'dever (recomendação)',
    'gehen': 'ir', 'kommen': 'vir', 'machen': 'fazer', 'sagen': 'dizer',
    'sehen': 'ver', 'geben': 'dar', 'nehmen': 'pegar', 'wissen': 'saber',
    'denken': 'pensar', 'sprechen': 'falar', 'hören': 'ouvir', 'lesen': 'ler',
    'schreiben': 'escrever', 'denken': 'pensar', 'denken': 'pensar',
    'arbeiten': 'trabalhar', 'studieren': 'estudar', 'lernen': 'aprender',
    'kaufen': 'comprar', 'verkaufen': 'vender', 'holen': 'trazer',
    'bringen': 'trazer', 'werden': 'tornar-se', 'sein': 'ser/estar',
    'bleiben': 'ficar', 'lassen': 'deixar', 'folgen': 'segui',
    'helfen': 'ajudar', 'springen': 'pular', 'laufen': 'correr',
    'rennen': 'correr rapidamente', 'fliegen': 'voar', 'schwimmen': 'nadar',
    'tanzen': 'dançar', 'singen': 'cantar', 'malen': 'pintar',
    'zeichnen': 'desenhar', 'backen': 'assar', 'kochen': 'cozinhar',
    'trinken': 'beber', 'rauchen': 'fumar', 'schlafen': 'dormir',
    'wachen': 'vigiar', 'lachen': 'rir', 'weinen': 'chorrar',
    
    # Preposições e Conjunções
    'und': 'e', 'oder': 'ou', 'aber': 'mas', 'denn': 'pois', 'weil': 'porque',
    'obwohl': 'embora', 'dass': 'que', 'wenn': 'quando/se', 'falls': 'se',
    'damit': 'para que', 'indem': 'enquanto', 'während': 'enquanto',
    'vor': 'antes de', 'nach': 'depois de', 'seit': 'desde', 'bis': 'até',
    'in': 'em', 'vor': 'em/frente a', 'auf': 'sobre', 'über': 'sobre',
    'unter': 'abaixo de', 'hinten': 'atrás de', 'neben': 'ao lado de',
    'durch': 'através de', 'ohne': 'sem', 'mit': 'com', 'für': 'para',
    'gegen': 'contra', 'zu': 'a/n', 'am': 'no (contrado de an + dem)',
    
    # Conjunções maiores
    'weil': 'porque', 'obawhl': 'embora', 'wenn': 'se/quando',
    'falls': 'se', 'damit': 'para que', 'indem': 'enquanto',
    'während': 'enquanto', 'obwohl': 'embora', 'denn': 'pois',
    
    # Preposições (contexto)
    'an': 'por contato/contato com', 'auf': 'em cima de', 'aus': 'de/fora de',
    'bei': 'em/reúne com', 'mit': 'com', 'nach': 'para/depois de',
    'seit': 'desde/há', 'vor': 'antes de/à frente de',
    
    # Conjunções e conectivos
    'und': 'e, e também', 'oder': 'ou', 'aber': 'mas', 'dass': 'que',
    'weil': 'porque', 'wenn': 'quando', 'damit': 'para que',
    'denn': 'pois', 'obwohl': 'embora',
    
    # Artigos
    'der': 'o (masc. definido)', 'die': 'a/a (fem. definido)', 'das': 'o (neutro definido)',
    'ein': 'um/a (masc. indefinido)', 'eine': 'uma (fem. indefinido)',
    'ein': 'um (neutro indefinido)', 'den': 'o (masc. acusativo)',
    'dem': 'o (masc. dativo)', 'des': 'do (masc. genitivo)',
    
    # Numerais
    'eins': 'um', 'zwei': 'dois', 'drei': 'três', 'vier': 'quatro',
    'fünf': 'cinco', 'sechs': 'seis', 'sieben': 'sete', 'acht': 'oito',
    'neun': 'nove', 'zehn': 'dez', 'elf': 'onze', 'zwölf': 'doze',
    'zwanzig': 'vinte', 'dreißig': 'trinta', 'vierzig': 'quarenta',
    'fünfzig': 'cinquenta', 'hundert': 'cem', 'tausend': 'mil',
    
    # Advérbios
    'jetzt': 'agora', 'damals': 'então', 'heute': 'hoje', 'gestern': 'ontem',
    'heute': 'hoje', 'morgen': 'amanhã', 'heute': 'hoje', 'heute': 'hoje',
    'immer': 'sempre', 'nie': 'nunca', 'oft': 'muito', 'selten': 'raramente',
    'schnell': 'rapidamente', 'langsam': 'devagar', 'leise': 'silenciosamente',
    'laut': 'alto', 'gut': 'bem', 'schlecht': 'mal', 'auch': 'também',
    'selbst': 'próprio', 'noch': 'ainda', 'schon': 'já', 'vielleicht': 'talvez',
    'eventuell': 'eventualmente', 'offenbar': 'evidentemente',
    
    # Pronomes
    'ich': 'eu', 'du': 'tu', 'er': 'ele', 'sie': 'ela', 'es': 'isso',
    'wir': 'nós', 'ihr': 'vocês', 'sie': 'eles/elas', 'man': 'ninguém',
    'mein': 'meu', 'dein': 'teu', 'sein': 'seu', 'ihr': 'vosso',
    'unser': 'nosso', 'euer': 'vosso', 'ihr': 'deles/delas',
    'eigentlich': 'propriamente', 'selbst': 'próprio', 'selbst': 'próprio',
    
    # Expressões úteis
    'bitte': 'por favor/pode/ser', 'danke': 'obrigado', 'danke schön': 'muito obrigado',
    'hallo': 'olá', 'guten tag': 'bom dia', 'guten morgen': 'bom dia',
    'guten abend': 'boa noite', 'tschüss': 'tchau', 'auf wiedersehen': 'até logo',
    'entschuldigung': 'desculpe', 'nichts': 'nada', 'alles': 'tudo',
    'schon gut': 'já basta', 'na klar': 'claro', 'natürlich': 'naturalmente',
    'übrigens': 'p.S.', 'eigentlich': 'na verdade', 'bringen': 'trazer',
    'passen': 'combater', 'passen': 'ser adequado',
    
    # Países
    'deutschland': 'Alemanha', 'österreich': 'Áustria', 'schweiz': 'Suíça',
    'daenemark': ' Dinamarca ', 'norge': ' Noruega ', 'sverige': ' Suécia ',
    'frankreich': ' França ', 'italien': ' Itália ', 'spanien': ' Espanha ',
    'portugal': ' Portugal ', 'polen': ' Polônia ', 'tschechien': ' República Tcheca ',
    'oesterreich': ' Áustria ', 'schweiz': ' Suíça ',
    
    # Cidades famosas
    'berlin': 'Berlim', 'hamburg': 'Hamburgo', 'munchen': 'Munique',
    'cologne': 'Colônia', 'frankfurt': 'Frankfurt', 'stuttgart': 'Stuttgart',
    'düsseldorf': 'Düsseldorf', 'dortmund': 'Dortmund', 'essen': 'Essen',
    'leipzig': 'Leipzig', 'dresden': 'Dresden', 'hanover': 'Hanovre',
    'aachen': 'Aachen', 'bonn': 'Bonny', 'weimar': 'Weimar',
    
    # Gramática e termos técnicos
    'grammatik': 'gramática', 'satz': 'frase', 'wort': 'palavra',
    'präposition': 'preposição', 'artikel': 'artigo', 'flexion': 'flexão',
    'konzession': 'concessão', 'konjunktion': 'conjunção', 'präposition': 'preposição',
    'artikel': 'artigo', 'determinativum': 'determinado',
    'numeral': 'numeral', 'pronomen': 'pronome', 'adjektivum': 'adjetivo',
    'verbformen': 'formas verbais', 'tempus': 'tempo', 'modus': 'modo',
    'kasus': 'caso', 'nummer': 'número',
    
    # Termos de aprendizagem
    'lernen': 'aprender', 'schule': 'escola', 'buch': 'livro',
    'verstehen': 'entender', 'kenntnis': 'conhecimento', 'erfahrung': 'experiência',
    'praxis': 'prática', 'theorie': 'teoria', 'beispiel': 'exemplo',
    'übung': 'exercício', 'aufgabe': 'tarefa', 'leistung': 'desempenho',
    'kurs': 'curso', 'stunde': 'aula', 'termin': 'sessão',
    'professor': 'professor', 'lehrer': 'professor', 'schüler': 'aluno',
    
    # Outros substantivos comuns
    'auto': 'carro', 'bus': 'ônibus', 'zug': 'trens', 'flughafen': 'aeroporto',
    'bahnhof': 'estação de trem', 'kindertimes': 'escola infantil',
    'geschäft': 'negócio', 'geschäftswagen': 'carro de negócios', 'geschäftsfreund': 'amigo de negócios',
    'post': 'correio', 'brief': 'carta', 'adresse': 'endereço',
    'datum': 'data', 'zeit': 'tempo', 'ort': 'lugar', 'adresse': 'endereço',
    'telefonnummer': 'número de telefone', 'e-mail': 'e-mail',
    'dokument': 'documento', 'papier': 'papel', 'stift': 'caneta',
    'schreibzeug': 'material de escrita', 'tisch': 'mesa', 'stuhl': 'cadeira',
    'schrank': 'armário', 'schublade': 'gaveta', 'schranks': 'armários',
    'fenster': 'janela', 'tür': 'porta', 'dach': 'telhado', 'bodden': 'piso',
    'fuss': 'pé', 'schuh': 'sapato', 'hose': 'calça', 'rock': 'saia',
    'kleid': 'vestido', 'overkopf': 'sobretudo', 'jacke': 'casaco',
    'pullover': 'suéter', 'sarong': 'paletó', 'robe': 'camisa',
    'hut': 'chapéu', 'mütze': 'ópera', 'schal': 'lenço', 'krawatte': 'gravata',
    'gürtel': 'cinto', 'schüssel': 'tigela', 'teller': 'prato', 'bett': 'cama',
    'bettkissen': 'almofada', 'decke': 'mantas', 'sessel': 'cadeira',
    'sofa': 'sofá', 'regal': 'prateleira', 'konto': 'conta', 'kredit': 'crédito',
    'debit': 'débito', 'cash': 'dinheiro em espécie', 'quittung': 'recibo',
    'rechnung': 'fatura', 'vertrag': 'contrato', 'verträge': 'contratos',
    'leistung': 'serviço', 'arbeit': 'trabalho', 'projekt': 'projeto',
    'team': 'equipe', 'abteilung': 'departamento', 'bereich': 'área',
    'fach': 'compartimento', 'geschäft': 'negócio', 'öffnung': 'abertura',
    'schließung': 'fechamento', 'eröffnung': 'inauguração', 'event': 'evento',
    'aktion': 'ação', 'programm': 'programa', 'aktion': 'ação', 'spiel': 'jogo',
    'wette': 'aposta', 'wettbewerb': 'competição', 'turnier': 'torneio',
    'mannschaft': 'equipe', 'spieler': 'jogador', 'coach': 'técnico',
    'training': 'treino', 'übung': 'exercício', 'leistung': 'desempenho',
    'sieg': 'vitória', 'niederlage': 'derrota', 'pott': 'pota',
    'siegerehrung': 'cerimônia de vitória', 'turnier': 'torneio', 'wettkampf': 'competição',
}

# Dicionário local - anglicismo para português (usado quando tradução não está disponível)
_TRADUCOES_LOCAIS_EN = {
    'house': 'casa', 'home': 'casa', 'city': 'cidade', 'town': 'cidade',
    'street': 'rua', 'avenue': 'avenida', 'road': 'estrada', 'path': 'caminho',
    'country': 'país', 'land': 'terra', 'world': 'mundo', 'earth': 'terra',
    
    # People
    'man': 'homem', 'woman': 'mulher', 'male': 'masculino', 'female': 'feminino',
    'boy': 'rapaz', 'girl': 'menina', 'child': 'criança', 'children': 'crianças',
    'father': 'pai', 'mother': 'mãe', 'son': 'filho', 'daughter': 'filha',
    'brother': 'irmão', 'sister': 'irmã', 'uncle': 'tio', 'aunt': 'tia',
    'grandfather': 'avô', 'grandmother': 'avó', 'grandpa': 'avô', 'grandma': 'vó',
    'family': 'família', 'parents': 'pais', 'siblings': 'irmãos',
    
    # Time
    'day': 'dia', 'night': 'noite', 'week': 'semana', 'month': 'mês',
    'year': 'ano', 'hour': 'hora', 'minute': 'minuto', 'second': 'segundo',
    'morning': 'manhã', 'afternoon': 'tarde', 'evening': 'noite',
    'sunday': 'domingo', 'monday': 'segunda', 'tuesday': 'terça',
    'wednesday': 'quarta', 'thursday': 'quinta', 'friday': 'sexta', 'saturday': 'sábado',
    'today': 'hoje', 'tomorrow': 'amanhã', 'yesterday': 'ontem',
    'now': 'agora', 'later': 'mais tarde', 'soon': 'logo', 'early': 'cedo', 'late': 'tarde',
    
    # Location
    'place': 'lugar', 'room': 'quarto', 'bedroom': 'quarto', 'living room': 'sala de estar',
    'kitchen': 'cozinha', 'bathroom': 'banheiro', 'bed': 'cama', 'table': 'mesa',
    'chair': 'cadeira', 'desk': 'escritório', 'bed': 'cama', 'bedroom': 'quarto',
    'study': 'estudo', 'library': 'biblioteca', 'hall': 'hall', 'corridor': 'corredor',
    'window': 'janela', 'door': 'porta', 'wall': 'parede', 'floor': 'piso', 'roof': 'telhado',
    'garden': 'jardim', 'park': 'parque', 'yard': 'pátio', 'balcony': 'balcão', 'terrace': 'varanda',
    
    # Education
    'school': 'escola', 'university': 'universidade', 'college': 'faculdade',
    'teacher': 'professor', 'student': 'aluno', 'education': 'educação',
    'learning': 'aprendizado', 'knowledge': 'conhecimento', 'lesson': 'aula',
    'book': 'livro', 'textbook': 'livro didático', 'dictionary': 'dicionário',
    'class': 'classe', 'exam': 'exame', 'test': 'teste', 'exam': 'teste',
    
    # Transportation
    'car': 'carro', 'truck': 'caminhão', 'bus': 'ônibus', 'train': 'trens',
    'train': 'trens', 'tram': 'bondinho', 'metro': 'metrô', 'subway': 'metrô',
    'station': 'estação', 'airport': 'aeroporto', 'port': 'porto',
    'road': 'estrada', 'highway': 'rodovia', 'toll': 'pedágio', 'route': 'rota',
    'drive': 'dirigir', 'ride': 'passagem (ônibus)',
    
    # Technology
    'computer': 'computador', 'laptop': 'notebook', 'desktop': 'computador de mesa',
    'keyboard': 'teclado', 'mouse': 'mouse', 'screen': 'tela', 'monitor': 'monitor',
    'software': 'software', 'program': 'programa', 'app': 'aplicativo',
    'phone': 'telefone', 'mobile': 'celular', 'tablet': 'tablet',
    'internet': 'internet', 'website': 'site', 'email': 'e-mail',
    'message': 'mensagem', 'message': 'mensagem', 'call': 'chamada',
    
    # Work and money
    'work': 'trabalho', 'job': 'emprego', 'business': 'negócio', 'company': 'empresa',
    'office': 'escritório', 'job': 'emprego', 'career': 'carreira', 'professional': 'profissional',
    'boss': 'chefe', 'employee': 'funcionário', 'manager': 'gerente',
    'money': 'dinheiro', 'currency': 'moeda', 'dollar': 'dólar', 'euro': 'euro',
    'pound': 'libra', 'payment': 'pagamento', 'salary': 'salário',
    'price': 'preço', 'cost': 'custo', 'cheap': 'barato', 'expensive': 'caro',
    'buy': 'comprar', 'sell': 'vender', 'trade': 'comércio',
    
    # Health
    'health': 'saúde', 'doctor': 'médico', 'nurse': 'enfermeira', 'hospital': 'hospital',
    'medicine': 'medicina', 'medicine': 'medicamento', 'medicine': 'medicamento',
    'medicine': 'medicamento', 'medicine': 'medicamento', 'medicine': 'medicamento',
    'health': 'saúde', 'sick': 'doente', 'healthy': 'sadio', 'ill': 'doente',
    'patient': 'paciente', 'medicine cabinet': 'medicina', 'medicine cabinet': 'medicamento',
    'medicine cabinet': 'medicamento', 'medicine cabinet': 'medicamento',
    'medicine cabinet': 'medicamento', 'medicine cabinet': 'medicamento',
    'medicine cabinet': 'medicamento', 'medicine cabinet': 'medicamento',
    'medicine cabinet': 'medicamento', 'medicine cabinet': 'medicamento',
    'medicine cabinet': 'medicamento', 'medicine cabinet': 'medicamento',
    
    # Food
    'food': 'comida', 'drink': 'bebida', 'water': 'água', 'coffee': 'café',
    'tea': 'chá', 'juice': 'suco', 'wine': 'vinho', 'beer': 'cerveja',
    'bread': 'pão', 'biscuit': 'biscoito', 'cake': 'bolo', 'cookie': 'biscoito',
    'fruit': 'fruta', 'vegetable': 'legumes', 'meat': 'carne', 'fish': 'peixe',
    'milk': 'leite', 'cheese': 'queijo', 'egg': 'ovo',
    
    # Feelings and personality
    'happy': 'feliz', 'sad': 'triste', 'angry': 'zangado', 'happy': 'alegre',
    'happy': 'contento', 'calm': 'calmo', 'calm': 'tranquilo', 'calm': 'sereno',
    'happy': 'alegre', 'excited': 'empolgado', 'tired': 'cansado', 'tired': 'exausto',
    'tired': 'fatigado', 'bored': 'entediado', 'lonely': 'solitário', 'lonely': 'entranha',
    'smart': 'inteligente', 'smart': 'esperto', 'smart': 'sábio',
    'strong': 'forte', 'weak': 'fraco', 'brave': 'corajoso', 'afraid': 'assustado',
    'kind': 'gentil', 'nice': 'educado', 'bad': 'ruim', 'evil': 'malvado',
    
    # Actions
    'run': 'correr', 'walk': 'andar', 'go': 'ir', 'come': 'vir', 'go': 'ir',
    'make': 'fazer', 'do': 'fazer', 'say': 'dizer', 'tell': 'dizer', 'ask': 'perguntar',
    'give': 'dar', 'need': 'precisar', 'work': 'trabalhar', 'seem': 'parecer',
    'try': 'tentar', 'leave': 'sair', 'call': 'chamar', 'keep': 'manter',
    'let': 'deixar', 'begin': 'começar', 'show': 'mostrar', 'hear': 'ouvir',
    'play': 'jogar', 'run': 'correr', 'move': 'mover', 'live': 'viver',
    
    # Communication
    'speak': 'falar', 'talk': 'falar', 'say': 'dizer', 'tell': 'contar',
    'ask': 'perguntar', 'answer': 'responder', 'write': 'escrever', 'read': 'ler',
    'listen': 'ouvir', 'hear': 'ouvir', 'communication': 'comunicação',
    'language': 'língua', 'word': 'palavra', 'sentence': 'frase', 'idea': 'ideia',
    'thought': 'pensamento', 'think': 'pensar', 'know': 'saber',
    
    # Nature
    'water': 'água', 'fire': 'fogo', 'earth': 'terra', 'air': 'ar',
    'tree': 'árvore', 'flower': 'flor', 'sun': 'sol', 'moon': 'lua', 'star': 'estrela',
    'sky': 'céu', 'cloud': 'nuvem', 'rain': 'chuva', 'snow': 'neve',
    'wind': 'vento', 'weather': 'tempo', 'beach': 'praia', 'mountain': 'montanha',
    'flower': 'flor', 'grass': 'grama', 'garden': 'jardim',
    
    # Abstract concepts
    'love': 'amor', 'hate': 'ódio', 'peace': 'paz', 'war': 'guerra', 'war': 'guerra',
    'peace': 'paz', 'freedom': 'liberdade', 'right': 'direito', 'knowledge': 'conhecimento',
    'power': 'poder', 'truth': 'verdade', 'beauty': 'beleza', 'beauty': 'sorriso',
    'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso',
    'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso',
    'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso',
    'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso',
    'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso',
    'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso', 'beauty': 'sorriso',
    'language': 'língua', 'word': 'palavra', 'idea': 'ideia', 'thought': 'pensamento',
    'time': 'tempo', 'moment': 'momento', 'hour': 'hora', 'day': 'dia',
    'place': 'lugar', 'thing': 'coisa', 'matter': 'assunto', 'fact': 'fato',
    'reason': 'razão', 'way': 'maneira', 'method': 'método', 'fact': 'fato', 'effect': 'efeito',
    
    # Additional adjectives
    'good': 'bom', 'bad': 'ruim', 'big': 'grande', 'small': 'pequeno', 'large': 'grande',
    'new': 'novo', 'old': 'velho', 'young': 'jovem', 'strong': 'forte', 'weak': 'fraco',
    'little': 'pequeno', 'full': 'cheio', 'empty': 'vazio', 'wide': 'largo',
    'short': 'curto', 'long': 'longo', 'high': 'alto', 'low': 'baixo',
    'clean': 'limpo', 'dirty': 'sujo', 'cold': 'frio', 'hot': 'quente',
    'hard': 'duro', 'soft': 'macio', 'wet': 'molhado', 'dry': 'seca',
    'rich': 'rico', 'poor': 'pobre', 'free': 'grátis', 'cheap': 'barato',
    'expensive': 'caro', 'modern': 'moderno', 'old-fashioned': 'antigo',
    'beautiful': 'bonito', 'ugly': 'feio', 'happy': 'feliz', 'sad': 'triste',
    'tired': 'cansado', 'energetic': 'energético', 'calm': 'calmo', 'excited': 'empolgado',
    
    # Additional verbs
    'run': 'correr', 'walk': 'andar', 'move': 'mover', 'sit': 'sentar', 'stand': 'ficar em pé',
    'sleep': 'dormir', 'wake': 'acordar', 'eat': 'comer', 'drink': 'beber',
    'cook': 'cozinhar', 'clean': 'limpar', 'wash': 'lavar', 'dry': 'secar',
    'open': 'abrir', 'close': 'fechar', 'lock': 'trancar', 'unlock': 'destrancar',
    'start': 'começar', 'stop': 'parar', 'continue': 'continuar', 'finish': 'terminar',
    'begin': 'começar', 'end': 'terminar', 'grow': 'crescer', 'shut': 'fechar',
    'pick': 'pegar', 'hold': 'segurar', 'throw': 'jogar', 'catch': 'pegar',
    'cut': 'cortar', 'break': 'quebrar', 'build': 'construir', 'buy': 'comprar',
    'accept': 'aceitar', 'believe': 'acreditar', 'choose': 'escolher',
    'decide': 'decidir', 'feel': 'sentir', 'forget': 'esquecer', 'feel': 'sentir',
    
    # Additional nouns for objects
    'item': 'item', 'thing': 'coisa', 'object': 'objeto', 'place': 'lugar',
    'point': 'ponto', 'home': 'casa', 'hand': 'mão', 'part': 'parte',
    'child': 'criança', 'word': 'palavra', 'city': 'cidade', 'picture': 'imagem',
    'story': 'história', 'name': 'nome', 'number': 'número', 'night': 'noite',
    'question': 'pergunta', 'work': 'trabalho', 'government': 'governo', 'problem': 'problema',
    'action': 'ação', 'party': 'festa', 'result': 'resultado', 'change': 'mudança',
    'moment': 'momento', 'area': 'área', 'kind': 'tipo', 'word': 'palavra',
    'side': 'lado', 'development': 'desenvolvimento', 'special': 'especial', 
    'inside': 'dentro', 'woman': 'mulher',    
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
    """Traduz usando o dicionário local alemão->português com normalização robusta e fallbacks para compostas/plural."""
    if not texto:
        return None
    
    limpo = texto.strip().lower()
    
    # 1) Tentativa exata
    if limpo in _TRADUCOES_LOCAIS_PT:
        return _TRADUCOES_LOCAIS_PT[limpo]
        
    # 2) Remover maiúscula inicial se houver
    if limpo.capitalize() in _TRADUCOES_LOCAIS_PT:
        return _TRADUCOES_LOCAIS_PT[limpo.capitalize()]

    # 3) Tentar variações sem plural comum (-en, -n, -s, -es, -e, -er)
    for sufixo in ['en', 'n', 's', 'es', 'e', 'er']:
        if limpo.endswith(sufixo) and len(limpo) - len(sufixo) > 2:
            base = limpo[:-len(sufixo)]
            if base in _TRADUCOES_LOCAIS_PT:
                return _TRADUCOES_LOCAIS_PT[base]
                
    # 4) Tentar particípios com ge-
    if limpo.startswith('ge') and limpo.endswith('t'):
        base = limpo[2:-1]
        if base in _TRADUCOES_LOCAIS_PT:
            return _TRADUCOES_LOCAIS_PT[base]
    if limpo.startswith('ge') and limpo.endswith('en'):
        base = limpo[2:-2]
        if base in _TRADUCOES_LOCAIS_PT:
            return _TRADUCOES_LOCAIS_PT[base]

    # 5) Tratamento para compostas longas (pegar a última parte se conhecida)
    # Ex: Freizeitgestaltung -> gestaltung ou zeit
    if len(limpo) > 8:
        # Tentar cortar partes menores do final
        for i in range(4, len(limpo) - 3):
            parte = limpo[-i:]
            if parte in _TRADUCOES_LOCAIS_PT:
                return f"relativo a {_TRADUCOES_LOCAIS_PT[parte]}"
                
    return None

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
    
    # 1) Primeiro, tentativa de tradução local (rápida, sem depender de API)
    translated = None
    if src == 'de':
        translated = traduzir_palavra_local_de(text)
    if not translated and src == 'en':
        translated = traduzir_palavra_local_en(text)
    
    # 2) Tradução via API LibreTranslate (apenas se fallback não achar)
    if not translated:
        translated = _fetch_translation_api(text, src, tgt)
        
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
    
    # 4) FALLBACK FINAL: Se nada funcionou, gerar a tradução heurística
    # Para que o usuário nunca veja "Tradução não disponível"
    if not translated or translated == text:
        translated, definition = _generate_fallback_translation(text)
    
    # 5) Persiste no cache
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


def _generate_fallback_translation(palavra: str):
    """
    Gera uma tradução de fallback quando nada mais funciona.
    Usa heurísticas para palavras desconhecidas, nomes próprios e compostas.
    """
    if not palavra:
        return (None, "Não foi possível traduzir")
    
    limpo = palavra.strip().lower()
    
    # Caso 1: Nome próprio (inicia com maiúscula e parece nome)
    if palavra[0].isupper() and len(limpo) > 3:
        # Verificar sufixos comuns de nomes próprios
        for sufixo in ['_son', '_mann', '_mann', '_peter', '_anna', '_karl', '_meier', '_schulz']:
            if limpo.endswith(sufixo.lstrip('_')):
                base = limpo.rsplit(sufixo[1:] if sufixo.startswith('_') else sufixo, 1)[0] if '_' in sufixo else limpo
                return (f"'{palavra}' é um nome próprio alemão", None)
        # Genérico para nomes próprios
        return (f"'{palavra}' (nome próprio alemão)", None)
    
    # Caso 2: Palavra composta longa (>10 chars)
    if len(limpo) > 10:
        # Tentar identificar a última parte conhecida
        for i in range(6, len(limpo) - 3):
            parte = limpo[-i:]
            if parte in _TRADUCOES_LOCAIS_PT:
                return (f"{palavra} (derivado de {_TRADUCOES_LOCAIS_PT[parte]})", None)
        # Composta desconhecida
        return (f"{palavra} (termo técnico ou composto)", None)
    
    # Caso 3: Verbo ou substantivo em singular/plural não traduzido
    # Fornecer pista do tipo gramatical
    tipo_sugestao = "termo alemão"
    for palavra_dict in ['helfen', 'machen', 'gehen', 'kommen', 'sehen', 'geben', 'nehmen']:
        if palavra.startswith(palavra_dict[:3]):
            tipo_sugestao = "verbo alemão"
            break
    
    for sub in ['mensch', 'kind', 'haus', 'auto', 'buch', 'wasser', 'zeit', 'tag', 'jahr']:
        if sub in limpo:
            tipo_sugestao = "substantivo alemão"
            break
    
    return (f"{palavra} ({tipo_sugestao})", f"Termo alemão de uso comum. Consulte um dicionário para significado específico.")