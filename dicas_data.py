# -*- coding: utf-8 -*-
"""
Módulo expandido de Dicas Estruturadas para a Língua Alemã no WISSIO.
Contém mais de 45 dicas categorizadas por nível CEFR e tópicos gramaticais/vocabulares.
"""

DICAS_ALEMAO = [
    {
        "id": 1,
        "titulo": "Os Quatro Casos Alemães",
        "nivel": "A2",
        "categoria": "Gramática",
        "resumo": "Nominativ, Akkusativ, Dativ e Genitiv: como funcionam os casos no alemão.",
        "exemplo_alemao": "Der Mann (Nom.) gibt dem Kind (Dat.) den Apfel (Akk.).",
        "exemplo_portugues": "O homem dá a maçã para a criança.",
        "detalhes": """
        O alemão utiliza quatro casos para indicar a função de um substantivo na frase:
        <ul>
            <li><strong>Nominativ (Nominativo):</strong> O sujeito da frase (quem realiza a ação). Pergunta: <em>Wer oder was?</em></li>
            <li><strong>Akkusativ (Acusativo):</strong> O objeto direto (quem sofre a ação diretamente). Pergunta: <em>Wen oder was?</em></li>
            <li><strong>Dativ (Dativo):</strong> O objeto indireto (para quem / a quem). Pergunta: <em>Wem?</em></li>
            <li><strong>Genitiv (Genitivo):</strong> Indica posse ou pertencimento. Pergunta: <em>Wessen?</em></li>
        </ul>
        """
    },
    {
        "id": 2,
        "titulo": "Gêneros dos Substantivos: Der, Die, Das",
        "nivel": "A1",
        "categoria": "Vocabulário",
        "resumo": "Dicas infalíveis para adivinhar o gênero dos substantivos em alemão.",
        "exemplo_alemao": "der Tisch (masculino), die Tür (feminino), das Haus (neutro)",
        "exemplo_portugues": "A mesa, a porta, a casa.",
        "detalhes": """
        Embora pareça aleatório, existem padrões úteis para os gêneros:
        <ul>
            <li><strong>Masculino (der):</strong> Dias da semana, meses, estações, pontos cardeais, e terminações como <em>-ismus, -ant, -er</em> (para pessoas).</li>
            <li><strong>Feminino (die):</strong> Maioria das árvores, flores, números cardinais, e terminações como <em>-ung, -heit, -keit, -schaft, -ion, -tät</em>.</li>
            <li><strong>Neutro (das):</strong> Cores substantivadas, letras, diminutivos em <em>-chen</em> e <em>-lein</em>, e muitos materiais.</li>
        </ul>
        """
    },
    {
        "id": 3,
        "titulo": "A Ordem dos Verbos: Verbklammer (A Moldura Verbal)",
        "nivel": "B1",
        "categoria": "Sintaxe",
        "resumo": "Como posicionar o verbo principal e o verbo auxiliar/modal na frase principal.",
        "exemplo_alemao": "Ich <strong>kann</strong> heute nicht ins Kino <strong>gehen</strong>.",
        "exemplo_portugues": "Eu não posso ir ao cinema hoje.",
        "detalhes": """
        Em frases principais com verbos modais, tempos compostos (Perfekt) ou particípios, ocorre o fenômeno da <em>Verbklammer</em> (moldura verbal):
        <ol>
            <li>O verbo conjugado (auxiliar ou modal) fica na <strong>segunda posição</strong> da frase.</li>
            <li>O verbo principal (no infinitivo ou particípio) vai obrigatoriamente para o <strong>fim absoluto</strong> da frase.</li>
        </ol>
        """
    },
    {
        "id": 4,
        "titulo": "Verbos Separáveis (Trennbare Verben)",
        "nivel": "A2",
        "categoria": "Verbos",
        "resumo": "O que são prefixos separáveis e como conjugá-los.",
        "exemplo_alemao": "Ich <strong>stehe</strong> um 7 Uhr <strong>auf</strong>.",
        "exemplo_portugues": "Eu acordo às 7 horas.",
        "detalhes": """
        Muitos verbos em alemão possuem prefixos que se separam na frase conjugada no presente e pretérito:
        <ul>
            <li>Exemplos de prefixos separáveis: <em>auf-, an-, ein-, mit-, vor-, aus-</em>.</li>
            <li>Na frase conjugada, o prefixo vai para o final da oração.</li>
            <li>No particípio (Perfekt), o prefixo fica colado com o 'ge-': <em>aufgestanden</em>.</li>
        </ul>
        """
    },
    {
        "id": 5,
        "titulo": "Falsos Cognitivos (Falsche Freunde)",
        "nivel": "B1",
        "categoria": "Vocabulário",
        "resumo": "Palavras em alemão que parecem o português ou inglês, mas têm significados totalmente diferentes.",
        "exemplo_alemao": "Gift (em alemão significa 'veneno', não 'presente').",
        "exemplo_portugues": "Das ist kein Geschenk, das ist Gift!",
        "detalhes": """
        Cuidado com estas armadilhas comuns:
        <ul>
            <li><strong>Gift:</strong> Significa <em>veneno</em> (em inglês é presente). Presente em alemão é <em>Geschenk</em>.</li>
            <li><strong>Werden:</strong> Significa <em>tornar-se</em> ou auxiliar de futuro (não significa 'arder' ou 'verde').</li>
            <li><strong>Also:</strong> Significa <em>portanto / então</em> (não significa 'além disso' ou 'também').</li>
            <li><strong>Bekommen:</strong> Significa <em>receber/obter</em> (não significa 'se tornar').</li>
        </ul>
        """
    },
    {
        "id": 6,
        "titulo": "Conjunções que Mandam o Verbo para o Fim (Nebensätze)",
        "nivel": "B1",
        "categoria": "Sintaxe",
        "resumo": "Weil, dass, wenn, obwohl: o verbo conjugado vai para o final da oração subordinada.",
        "exemplo_alemao": "Ich bleibe zu Hause, <strong>weil</strong> es regnet.",
        "exemplo_portugues": "Eu fico em casa porque está chovendo.",
        "detalhes": """
        Nas orações subordinadas introduzidas por conjunções como <em>weil</em> (porque), <em>dass</em> (que), <em>wenn</em> (se/quando) e <em>obwohl</em> (embora):
        <br>O verbo conjugado perde sua segunda posição e vai diretamente para o **último lugar** daquela oração.
        """
    },
    {
        "id": 7,
        "titulo": "Plural dos Substantivos em Alemão",
        "nivel": "A2",
        "categoria": "Gramática",
        "resumo": "Como formar o plural já que não existe uma única regra universal.",
        "exemplo_alemao": "das Buch -> die Bücher | das Auto -> die Autos",
        "exemplo_portugues": "O livro (os livros) | O carro (os carros)",
        "detalhes": """
        O plural em alemão pode assumir várias terminações diferentes, que devem ser memorizadas junto com o gênero do substantivo:
        <ul>
            <li><strong>-e / -¨e:</strong> (ex: Tag -> Tage, Buch -> Bücher)</li>
            <li><strong>-er / -¨er:</strong> (ex: Kind -> Kinder)</li>
            <li><strong>-en / -n:</strong> (ex: Frau -> Frauen, Student -> Studenten)</li>
            <li><strong>-s:</strong> (ex: Auto -> Autos, Hotel -> Hotels)</li>
            <li><strong>Sem alteração:</strong> (ex: Lehrer -> Lehrer)</li>
        </ul>
        """
    },
    {
        "id": 8,
        "titulo": "O Pretérito Perfeito (Perfekt) com Haben ou Sein?",
        "nivel": "A2",
        "categoria": "Verbos",
        "resumo": "Quando usar 'haben' e quando usar 'sein' para formar o passado composto.",
        "exemplo_alemao": "Ich <strong>habe</strong> ein Buch gelesen. Ich <strong>bin</strong> nach Berlin gefahren.",
        "exemplo_portugues": "Eu li um livro. Eu fui para Berlim.",
        "detalhes": """
        A escolha do auxiliar no Perfekt segue regras claras:
        <ul>
            <li><strong>Sein:</strong> Usado com verbos que indicam mudança de estado (ex: <em>einschlafen</em>), movimento de um ponto a outro (ex: <em>gehen, fahren, fliegen</em>) e com <em>sein, bleiben, passieren</em>.</li>
            <li><strong>Haben:</strong> Usado com a grande maioria dos outros verbos (transitivos, reflexivos e modais).</li>
        </ul>
        """
    },
    {
        "id": 9,
        "titulo": "Adjetivos Preditivos vs. Atributivos",
        "nivel": "B1",
        "categoria": "Gramática",
        "resumo": "Quando o adjetivo ganha terminação e quando permanece invariável.",
        "exemplo_alemao": "Das Auto ist schnell. (predicativo) | Das schnelle Auto. (atributivo)",
        "exemplo_portugues": "O carro é rápido. | O carro rápido.",
        "detalhes": """
        <ul>
            <li><strong>Predicativos:</strong> Estão após o verbo (sein, werden) e **não** mudam de forma (ex: <em>Das Haus ist groß</em>).</li>
            <li><strong>Atributivos:</strong> Estão antes do substantivo e recebem terminações de declinação conforme o gênero, caso e artigo (ex: <em>der große Hund</em>).</li>
        </ul>
        """
    },
    {
        "id": 10,
        "titulo": "Expressando Opiniões e Preferências",
        "nivel": "A2",
        "categoria": "Conversação",
        "resumo": "Frases essenciais para debater, concordar e discordar em alemão.",
        "exemplo_alemao": "Ich bin der Meinung, dass... | Ich stimme dir zu.",
        "exemplo_portugues": "Eu sou da opinião de que... | Eu concordo com você.",
        "detalhes": """
        Para enriquecer sua argumentação:
        <ul>
            <li><em>Meiner Ansicht nach...</em> (Na minha opinião...)</li>
            <li><em>Ich bin absolut dagegen.</em> (Sou totalmente contra.)</li>
            <li><em>Das sehe ich auch so.</em> (Vejo isso da mesma forma.)</li>
        </ul>
        """
    },
    {
        "id": 11,
        "titulo": "Uso do 'Es gibt' (Há / Existe)",
        "nivel": "A1",
        "categoria": "Gramática",
        "resumo": "Como indicar a existência de algo exigindo sempre o caso Acusativo.",
        "exemplo_alemao": "<strong>Es gibt</strong> einen Park in dieser Stadt.",
        "exemplo_portugues": "Há um parque nesta cidade.",
        "detalhes": """
        A expressão <em>es gibt</em> é fixa e corresponde ao verbo 'haver' ou 'existir' em português. O substantivo seguinte vem obrigatoriamente no <strong>Akkusativ</strong>.
        """
    },
    {
        "id": 12,
        "titulo": "Verbos Modais: Significado e Posição",
        "nivel": "A2",
        "categoria": "Verbos",
        "resumo": "Können, müssen, wollen, dürfen, sollen, möchten.",
        "exemplo_alemao": "Ich <strong>muss</strong> heute arbeiten.",
        "exemplo_portugues": "Eu preciso trabalhar hoje.",
        "detalhes": """
        Os verbos modais modificam o sentido do verbo principal. Na frase, o verbo modal fica na 2ª posição (conjugado) e o verbo principal vai para o final no infinitivo sem 'zu'.
        """
    },
    {
        "id": 13,
        "titulo": "Como Formar o Imperativo",
        "nivel": "A2",
        "categoria": "Gramática",
        "resumo": "Dando ordens e conselhos educados em alemão (du, ihr, Sie).",
        "exemplo_alemao": "Lies das Buch! | Lesen Sie bitte!",
        "exemplo_portugues": "Leia o livro! | Leia por favor (formal)!",
        "detalhes": """
        <ul>
            <li><strong>Du:</strong> Remove-se o pronome e a terminação '-st' (ex: <em>du machst -> Mach!</em>).</li>
            <li><strong>Ihr:</strong> Remove-se apenas o pronome (ex: <em>ihr macht -> Macht!</em>).</li>
            <li><strong>Sie:</strong> Inverte-se o verbo e o pronome (ex: <em>Sie machen -> Machen Sie!</em>).</li>
        </ul>
        """
    },
    {
        "id": 14,
        "titulo": "Pronomes Relativos (Relativsätze)",
        "nivel": "B2",
        "categoria": "Sintaxe",
        "resumo": "Der, die, das, welcher, welche como pronomes que introduzem orações relativas.",
        "exemplo_alemao": "Das ist der Mann, <strong>den</strong> ich gestern gesehen habe.",
        "exemplo_portugues": "Este é o homem que eu vi ontem.",
        "detalhes": """
        O pronome relativo concorda em gênero e número com o antecedente, mas seu caso (Akkusativ, Dativ, Genitiv) é determinado pela função que ele exerce **dentro** da oração relativa. O verbo vai para o final.
        """
    },
    {
        "id": 15,
        "titulo": "Diferença entre 'Kennen' e 'Wissen'",
        "nivel": "A2",
        "categoria": "Vocabulário",
        "resumo": "Quando usar cada um dos verbos que significam 'saber' ou 'conhecer'.",
        "exemplo_alemao": "Ich <strong>kenne</strong> Berlin. | Ich <strong>weiß</strong>, wie man Deutsch lernt.",
        "exemplo_portugues": "Eu conheço Berlim. | Eu sei como se aprende alemão.",
        "detalhes": """
        <ul>
            <li><strong>Kennen:</strong> Usado para conhecer pessoas, lugares ou obras de arte (objeto direto direto).</li>
            <li><strong>Wissen:</strong> Usado para saber fatos, informações ou dados específicos (geralmente seguido de que/como).</li>
        </ul>
        """
    },
    # ---- NOVAS DICAS ADICIONADAS (30+) ----
    {
        "id": 16,
        "titulo": "Preposições com Acusativo e Dativo (Wechselpräpositionen)",
        "nivel": "B1",
        "categoria": "Gramática",
        "resumo": "an, auf, hinter, in, neben, über, unter, vor, zwischen: quando usam acusativo e quando usam dativo.",
        "exemplo_alemao": "Ich lege das Buch auf den Tisch (Akk.) | Das Buch liegt auf dem Tisch (Dat.).",
        "exemplo_portugues": "Eu coloco o livro sobre a mesa | O livro está sobre a mesa.",
        "detalhes": """
        As chamadas preposições mistas mudam de caso dependendo da ideia da frase:
        <ul>
            <li><strong>Acusativo (Direção / Movimento com destino):</strong> Pergunta <em>Wohin?</em> (Para onde?)</li>
            <li><strong>Dativo (Localização estática / Sem mudança de lugar):</strong> Pergunta <em>Wo?</em> (Onde?)</li>
        </ul>
        """
    },
    {
        "id": 17,
        "titulo": "A Diferença entre 'Man' e 'Mann'",
        "nivel": "A1",
        "categoria": "Vocabulário",
        "resumo": "Cuidado com a grafia e o significado: 'man' (pronome impessoal) vs 'Mann' (homem).",
        "exemplo_alemao": "Hier <strong>spricht man</strong> Deutsch. | Der <strong>Mann</strong> arbeitet.",
        "exemplo_portugues": "Aqui se fala alemão. | O homem trabalha.",
        "detalhes": """
        <ul>
            <li><strong>man:</strong> Pronome indefinido/impessoal (equivalente a 'a gente', 'se', ou 'todos' em português). Sempre com letra minúscula.</li>
            <li><strong>Mann:</strong> Substantivo que significa 'homem' ou 'marido'. Sempre com letra maiúscula (por ser substantivo).</li>
        </ul>
        """
    },
    {
        "id": 18,
        "titulo": "Verbos Reflexivos em Alemão (Reflexive Verben)",
        "nivel": "A2",
        "categoria": "Verbos",
        "resumo": "Como usar pronomes reflexivos como 'mich', 'dich', 'sich'.",
        "exemplo_alemao": "Ich <strong>freue mich</strong> auf den Urlaub.",
        "exemplo_portugues": "Eu me alegro pelas férias.",
        "detalhes": """
        Muitos verbos em alemão exigem um pronome reflexivo que concorda com o sujeito:
        <br><em>ich mich, du dich, er/sie/es sich, wir uns, ihr euch, sie/Sie sich.</em>
        <br>Nota: Alguns verbos que pedem acusativo em português pedem dativo em alemão (ex: <em>sich etwas vorstellen</em> - imaginar algo).
        """
    },
    {
        "id": 19,
        "titulo": "Uso dos numerais ordinais",
        "nivel": "A2",
        "categoria": "Vocabulário",
        "resumo": "Como contar e enumerar datas, andares e posições (erster, zweite, dritte).",
        "exemplo_alemao": "Heute ist der <strong>erste</strong> Mai.",
        "exemplo_portugues": "Hoje é primeiro de maio.",
        "detalhes": """
        <ul>
            <li>Do 1 ao 19, adiciona-se o sufixo <strong>-te</strong> (ex: <em>erste, zweite, dritte, vierte</em>).</li>
            <li>A partir do 20, adiciona-se o sufixo <strong>-ste</strong> (ex: <em>zwanzigste, hundertste</em>).</li>
        </ul>
        """
    },
    {
        "id": 20,
        "titulo": "O Passado Simples (Präteritum)",
        "nivel": "B1",
        "categoria": "Verbos",
        "resumo": "Quando o Präteritum é mais usado do que o Perfekt na língua alemã.",
        "exemplo_alemao": "Ich <strong>war</strong> gestern müde. Er <strong>hatte</strong> ein Auto.",
        "exemplo_portugues": "Eu estava cansado ontem. Ele tinha um carro.",
        "detalhes": """
        Embora o <em>Perfekt</em> seja o mais falado no dia a dia para o passado, o <em>Präteritum</em> é amplamente utilizado com:
        <ul>
            <li>Verbos auxiliares (sein e haben).</li>
            <li>Verbos modais (können, müssen, etc.).</li>
            <li>Textos escritos, narrativas, jornais e literatura.</li>
        </ul>
        """
    },
    {
        "id": 21,
        "titulo": "Orações Condicionais com 'Wenn'",
        "nivel": "B1",
        "categoria": "Sintaxe",
        "resumo": "Como construir frases de condição em alemão.",
        "exemplo_alemao": "<strong>Wenn</strong> es regnet, bleibe ich zu Hause.",
        "exemplo_portugues": "Se chover, eu fico em casa.",
        "detalhes": """
        Na frase condicional com <em>wenn</em>:
        <ol>
            <li>A oração com <em>wenn</em> coloca o verbo no final.</li>
            <li>A oração principal seguinte começa diretamente com o verbo conjugado (posição 1 ou 2 dependendo da inversão).</li>
        </ol>
        """
    },
    {
        "id": 22,
        "titulo": "Substantivos Compostos (Komposita)",
        "nivel": "A2",
        "categoria": "Vocabulário",
        "resumo": "A genialidade e a flexibilidade de juntar palavras em alemão.",
        "exemplo_alemao": "das Handschuh (Hand + Schuh = Luva, literalmente 'sapato de mão')",
        "exemplo_portugues": "Luva",
        "detalhes": """
        O alemão permite unir substantivos para formar novas palavras.
        <br><strong>Regra de ouro:</strong> O gênero e o plural do substantivo composto são determinados pela **última palavra** da composição.
        """
    },
    {
        "id": 23,
        "titulo": "Uso de 'zu' + Infinitivo",
        "nivel": "B1",
        "categoria": "Gramática",
        "resumo": "Como conectar dois verbos na mesma frase usando 'zu'.",
        "exemplo_alemao": "Ich versuche, Deutsch <strong>zu lernen</strong>.",
        "exemplo_portugues": "Eu tento aprender alemão.",
        "detalhes": """
        Quando um verbo rege outro no infinitivo (ex: tentar, planejar, ter vontade de), usamos a partícula <em>zu</em> logo antes do verbo no infinitivo, que vai para o fim da frase.
        """
    },
    {
        "id": 24,
        "titulo": "Pronomes Possessivos no Acusativo",
        "nivel": "A2",
        "categoria": "Gramática",
        "resumo": "mein -> meinen, dein -> deinen: as terminações no caso acusativo masculino.",
        "exemplo_alemao": "Ich suche <strong>meinen</strong> Schlüssel.",
        "exemplo_portugues": "Eu estou procurando minha chave (meu chaveiro/chave - masculino em alemão).",
        "detalhes": """
        No acusativo masculino, os pronomes possessivos ganham a terminação <strong>-en</strong>:
        <br><em>meinen, deinen, seinen, ihren, unseren, euren, ihren.</em> Nos demais gêneros permanecem iguais ao nominativo.
        """
    },
    {
        "id": 25,
        "titulo": "Substantivos Fracos (N-Deklination)",
        "nivel": "B2",
        "categoria": "Gramática",
        "resumo": "Substantivos masculinos que ganham -en / -n em todos os casos exceto no nominativo.",
        "exemplo_alemao": "Ich kenne den Studen<strong>ten</strong>.",
        "exemplo_portugues": "Eu conheço o estudante.",
        "detalhes": """
        Certos substantivos masculinos (geralmente indicando profissões ou nacionalidades terminadas em -e, como <em>der Junge, der Kollege, der Student</em>) recebem a desinência extra <em>-en</em> ou <em>-n</em> no Akkusativ, Dativ e Genitiv.
        """
    },
    {
        "id": 26,
        "titulo": "Partículas Modais (Modalpartikeln)",
        "nivel": "B2",
        "categoria": "Conversação",
        "resumo": "doch, mal, denn, eben, wohl: pequenas palavras que dão tom e emoção ao alemão falado.",
        "exemplo_alemao": "Komm <strong>mal</strong> her!",
        "exemplo_portugues": "Venha aqui cá!",
        "detalhes": """
        As partículas modais não mudam o significado gramatical direto, mas expressam a atitude do falante (impaciência, carinho, dúvida, surpresa). São essenciais para soar natural como um nativo.
        """
    },
    {
        "id": 27,
        "titulo": "Como Formar a Voz Passiva (Passiv)",
        "nivel": "B2",
        "categoria": "Gramática",
        "resumo": "Uso do verbo 'werden' + Partizip II para focar na ação em vez de quem a realiza.",
        "exemplo_alemao": "Das Auto <strong>wird</strong> repariert.",
        "exemplo_portugues": "O carro está sendo consertado.",
        "detalhes": """
        A voz passiva em alemão é construída com o verbo auxiliar <strong>werden</strong> conjugado + o particípio passado do verbo principal no final da frase.
        """
    },
    {
        "id": 28,
        "titulo": "O Genitivo com Nomes Próprios e Posses",
        "nivel": "B1",
        "categoria": "Gramática",
        "resumo": "Como indicar posse usando o apóstrofo ou a terminação -s em nomes.",
        "exemplo_alemao": "Das ist Anna<strong>s</strong> Buch.",
        "exemplo_portugues": "Este é o livro da Anna.",
        "detalhes": """
        Em alemão, ao contrário do inglês, não se usa apóstrofo isolado para posse, mas sim a letra <strong>-s</strong> colada diretamente ao nome próprio (ex: <em>Peters Auto</em>).
        """
    },
    {
        "id": 29,
        "titulo": "Verbos com Preposições Fixas",
        "nivel": "B2",
        "categoria": "Verbos",
        "resumo": "Warten auf, sich freuen auf, denken an: verbos que exigem preposições específicas.",
        "exemplo_alemao": "Ich warte <strong>auf</strong> dich.",
        "exemplo_portugues": "Eu estou esperando por você.",
        "detalhes": """
        Em alemão, muitos verbos vêm acompanhados de uma preposição fixa que rege um caso determinado. É fundamental memorizar o verbo junto com sua preposição e caso correspondente (ex: <em>warten + auf + Akkusativ</em>).
        """
    },
    {
        "id": 30,
        "titulo": "Comparativo e Superlativo dos Adjetivos",
        "nivel": "A2",
        "categoria": "Gramática",
        "resumo": "Wie, als, am...sten: como comparar coisas e pessoas em alemão.",
        "exemplo_alemao": "Berlin ist größer <strong>als</strong> Hamburg. München ist <strong>am größten</strong>.",
        "exemplo_portugues": "Berlim é maior do que Hamburgo. Munique é a maior.",
        "detalhes": """
        <ul>
            <li><strong>Comparativo:</strong> Adjetivo + <em>-er</em> + <em>als</em> (do que). Vogais a, o, u frequentemente recebem trema (ä, ö, ü).</li>
            <li><strong>Superlativo:</strong> <em>am</em> + adjetivo + <em>-sten</em> (ou <em>-esten</em>).</li>
        </ul>
        """
    },
    {
        "id": 31,
        "titulo": "Diferença entre 'Besser' e 'Beste'",
        "nivel": "A2",
        "categoria": "Vocabulário",
        "resumo": "O comparativo e o superlativo irregular do adjetivo 'gut'.",
        "exemplo_alemao": "Das ist <strong>besser</strong>. Das ist das <strong>beste</strong> Buch.",
        "exemplo_portugues": "Isso é melhor. Este é o melhor livro.",
        "detalhes": """
        Assim como em português (bom -> melhor -> o ótimo/melhor), o adjetivo <em>gut</em> é irregular:
        <br><em>gut -> besser -> am besten / der beste</em>.
        """
    },
    {
        "id": 32,
        "titulo": "Uso de 'Um... zu' + Infinitivo",
        "nivel": "B1",
        "categoria": "Sintaxe",
        "resumo": "Expressando finalidade ou objetivo ('para fazer algo').",
        "exemplo_alemao": "Ich lerne Deutsch, <strong>um</strong> in Berlin <strong>zu arbeiten</strong>.",
        "exemplo_portugues": "Eu aprendo alemão para trabalhar em Berlim.",
        "detalhes": """
        A estrutura <em>um ... zu</em> é usada quando o sujeito da oração principal e da subordinada é o mesmo, indicando o propósito ou objetivo da ação. O verbo vai para o fim.
        """
    },
    {
        "id": 33,
        "titulo": "Orações Concessivas com 'Obwohl'",
        "nivel": "B2",
        "categoria": "Sintaxe",
        "resumo": "Como expressar contraste ou concessão ('embora / apesar de').",
        "exemplo_alemao": "<strong>Obwohl</strong> es regnet, gehen wir spazieren.",
        "exemplo_portugues": "Embora esteja chovendo, nós vamos passear.",
        "detalhes": """
        A conjunção <em>obwohl</em> introduz uma concessão e joga o verbo conjugado para o final daquela oração. Na oração principal seguinte, o verbo vem na primeira posição.
        """
    },
    {
        "id": 34,
        "titulo": "O Futuro com 'Werden' (Futur I)",
        "nivel": "A2",
        "categoria": "Verbos",
        "resumo": "Como formar o tempo futuro simples em alemão.",
        "exemplo_alemao": "Morgen <strong>wird</strong> es regne<strong>n</strong>.",
        "exemplo_portugues": "Amanhã vai chover.",
        "detalhes": """
        Para expressar o futuro em alemão, usa-se o verbo auxiliar <strong>werden</strong> na 2ª posição conjugado + o verbo principal no infinitivo posicionado no **fim absoluto** da frase.
        <br>Nota: No dia a dia, os alemães usam frequentemente o presente simples com uma indicação de tempo futuro.
        """
    },
    {
        "id": 35,
        "titulo": "Pronomes Demonstrativos (dieser, jener)",
        "nivel": "B1",
        "categoria": "Gramática",
        "resumo": "Como apontar especificamente para objetos ou pessoas ('este, esta, isto').",
        "exemplo_alemao": "<strong>Dieser</strong> Mantel ist schön.",
        "exemplo_portugues": "Este casaco é bonito.",
        "detalhes": """
        Os pronomes demonstrativos <em>dieser, diese, dieses</em> declinam exatamente como os artigos definidos (der, die, das) e servem para enfatizar um substantivo específico.
        """
    },
    {
        "id": 36,
        "titulo": "Uso da partícula 'Noch'",
        "nivel": "A2",
        "categoria": "Vocabulário",
        "resumo": "Significados de 'noch' ('ainda', 'mais', 'nem sequer').",
        "exemplo_alemao": "Hast du <strong>noch</strong> Kaffee?",
        "exemplo_portugues": "Você ainda tem café? / Tem mais café?",
        "detalhes": """
        A palavra <em>noch</em> é extremamente versátil:
        <ul>
            <li>Significa <em>ainda</em> (continuidade de um estado).</li>
            <li>Significa <em>mais</em> (ex: <em>noch ein Bier</em> - mais uma cerveja).</li>
        </ul>
        """
    },
    {
        "id": 37,
        "titulo": "Uso da partícula 'Schon'",
        "nivel": "A2",
        "categoria": "Vocabulário",
        "resumo": "Significados de 'schon' ('já').",
        "exemplo_alemao": "Ich bin <strong>schon</strong> fertig.",
        "exemplo_portugues": "Eu já terminei.",
        "detalhes": """
        <em>Schon</em> indica que algo ocorreu antes do esperado ou expressa certeza e ênfase (ex: <em>Das geht schon!</em> - Isso dá certo!).
        """
    },
    {
        "id": 38,
        "titulo": "Como dizer as Horas em Alemão",
        "nivel": "A1",
        "categoria": "Conversação",
        "resumo": "O sistema oficial (24h) e o sistema coloquial de relógio.",
        "exemplo_alemao": "Es ist halb drei. (14:30) | Es ist viertel nach vier. (16:15)",
        "exemplo_portugues": "São duas e meia. / São quatro e quinze.",
        "detalhes": """
        No alemão coloquial, usa-se muito as referências relativas:
        <ul>
            <li><em>viertel nach</em> (um quarto após / e quinze)</li>
            <li><em>halb</em> (metade para a hora seguinte, ex: <em>halb drei</em> = 2:30)</li>
            <li><em>viertel vor</em> (um quarto antes / quinze para)</li>
        </ul>
        """
    },
    {
        "id": 39,
        "titulo": "Preposições de Tempo: Um, Am, Im",
        "nivel": "A1",
        "categoria": "Gramática",
        "resumo": "Regras simples para usar 'um' (horas), 'am' (dias/partes do dia) e 'im' (meses/estações/anos).",
        "exemplo_alemao": "<strong>Um</strong> 8 Uhr | <strong>Am</strong> Montag | <strong>Im</strong> Juli",
        "exemplo_portugues": "Às 8 horas | Na segunda-feira | Em julho",
        "detalhes": """
        <ul>
            <li><strong>um:</strong> Usado exclusivamente para horários exatos (ex: <em>um 14 Uhr</em>).</li>
            <li><strong>am:</strong> Usado para dias da semana e partes do dia (ex: <em>am Morgen, am Sonntag</em>).</li>
            <li><strong>im:</strong> Usado para meses, estações do ano e anos (ex: <em>im Sommer, im Jahr 2026</em>).</li>
        </ul>
        """
    },
    {
        "id": 40,
        "titulo": "O Particípio Passado (Partizip II)",
        "nivel": "A2",
        "categoria": "Verbos",
        "resumo": "Como construir o particípio com o prefixo 'ge-' e as terminações '-t' ou '-en'.",
        "exemplo_alemao": "ge-mach<strong>t</strong> (regular) | ge-seh<strong>en</strong> (irregular)",
        "exemplo_portugues": "feito | visto",
        "detalhes": """
        O <em>Partizip II</em> é fundamental para formar os tempos compostos (Perfekt, Plusquamperfekt e Passiv). Verbos regulares adicionam <strong>ge-...-t</strong>, enquanto os irregulares mudam a vogal interna e terminam em <strong>-en</strong>.
        """
    },
    {
        "id": 41,
        "titulo": "Substantivos com Gênero Duplo e Significados Diferentes",
        "nivel": "B2",
        "categoria": "Vocabulário",
        "resumo": "Palavras que mudam completamente de significado ao trocar de artigo (der, die, das).",
        "exemplo_alemao": "der See (o lago) vs. die See (o mar/oceano)",
        "exemplo_portugues": "O lago / O mar",
        "detalhes": """
        Alguns substantivos em alemão mudam de significado se você alterar o artigo definido:
        <ul>
            <li><strong>das Schild</strong> (a placa de sinalização) vs. <strong>der Schild</strong> (o escudo)</li>
            <li><strong>die Leiter</strong> (a escada portátil) vs. <strong>der Leiter</strong> (o líder / diretor)</li>
        </ul>
        """
    },
    {
        "id": 42,
        "titulo": "A Partícula 'Erst'",
        "nivel": "B1",
        "categoria": "Vocabulário",
        "resumo": "Uso de 'erst' ('somente', 'apenas', 'só agora').",
        "exemplo_alemao": "Ich bin <strong>erst</strong> seit zwei Wochen hier.",
        "exemplo_portugues": "Eu estou aqui há apenas duas semanas.",
        "detalhes": """
        A palavra <em>erst</em> expressa restrição temporal (apenas agora) ou quantidade reduzida em comparação com o esperado.
        """
    },
    {
        "id": 43,
        "titulo": "A Partícula 'Doch'",
        "nivel": "B1",
        "categoria": "Conversação",
        "resumo": "Respondendo afirmativamente a uma pergunta negativa ('Sim, pelo contrário!').",
        "exemplo_alemao": "— Kommst du nicht mit? — <strong>Doch!</strong>",
        "exemplo_portugues": "— Você não vem junto? — <strong>Claro que sim!</strong>",
        "detalhes": """
        Em alemão, se alguém lhe faz uma pergunta na negativa (ex: 'Você não gosta de café?'), você não usa <em>ja</em> para discordar e dizer que gosta, mas sim <strong>doch</strong>.
        """
    },
    {
        "id": 44,
        "titulo": "Abreviaturas Comuns no Alemão Escrito",
        "nivel": "B1",
        "categoria": "Vocabulário",
        "resumo": "z.B., u.a., bzw., ca.: decifrando as abreviações mais usadas no dia a dia.",
        "exemplo_alemao": "z.B. (zum Beispiel) | bzw. (beziehungsweise)",
        "exemplo_portugues": "por exemplo | ou seja / respectivamente",
        "detalhes": """
        <ul>
            <li><strong>z.B.</strong> = zum Beispiel (por exemplo)</li>
            <li><strong>bzw.</strong> = beziehungsweise (respectivamente / ou melhor)</li>
            <li><strong>ca.</strong> = circa (cerca de / aproximadamente)</li>
            <li><strong>u.a.</strong> = unter anderem (entre outros)</li>
        </ul>
        """
    },
    {
        "id": 45,
        "titulo": "O Uso da Vírgula em Orações Subordinadas",
        "nivel": "B1",
        "categoria": "Sintaxe",
        "resumo": "Regras rígidas de pontuação que diferem do português.",
        "exemplo_alemao": "Ich weiß<strong>, dass</strong> du Recht hast.",
        "exemplo_portugues": "Eu sei que você tem razão.",
        "detalhes": """
        Em alemão, o uso da vírgula é obrigatório e estrito para separar orações principais de orações subordinadas ou relativas. A vírgula sempre antecede conjunções como <em>dass, weil, obwohl, wenn</em> e pronomes relativos.
        """
    }
]
