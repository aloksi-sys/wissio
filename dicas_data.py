# -*- coding: utf-8 -*-
"""
Módulo de Dicas Estruturadas para a Língua Alemã no WISSIO.
Contém dicas categorizadas por nível CEFR e tópicos gramaticais/vocabulares.
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
    }
]
