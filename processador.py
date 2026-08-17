import spacy

try:
    nlp = spacy.load('de_core_news_sm')
except Exception:
    nlp = None

def processar_texto_alemao(texto):
    # Se o modelo do spaCy carregou com sucesso
    if nlp:
        doc = nlp(texto)
        palavras = [token.text for token in doc if token.is_alpha]
        tamanho_medio = sum(len(p) for p in palavras) / len(palavras) if palavras else 0
        
        if tamanho_medio < 5:
            nivel = 'A1'
        elif tamanho_medio < 6.5:
            nivel = 'A2'
        elif tamanho_medio < 8:
            nivel = 'B1'
        else:
            nivel = 'B2/C1'

        flashcards_extraidos = []
        vistas = set()
        
        for token in doc:
            if token.pos_ in ['NOUN', 'VERB'] and len(token.lemma_) > 3:
                lemma = token.lemma_
                if lemma not in vistas:
                    vistas.add(lemma)
                    flashcards_extraidos.append({
                        'palavra': lemma,
                        'exemplo': token.sent.text.strip()
                    })
            if len(flashcards_extraidos) >= 8:
                break

        palavras_ctest = []
        contador = 0
        for token in doc:
            word = token.text
            if token.is_alpha and len(word) > 3:
                contador += 1
                if contador % 2 == 0:
                    metade = len(word) // 2
                    palavras_ctest.append(word[:metade] + "____")
                else:
                    palavras_ctest.append(word)
            else:
                palavras_ctest.append(word)
                
            if token.whitespace_:
                palavras_ctest.append(" ")

        texto_ctest = "".join(palavras_ctest)

    else:
        # Plano B: Caso o modelo do spaCy não esteja baixado, faz um processamento básico
        nivel = 'A1/A2'
        flashcards_extraidos = []
        palavras = texto.split()
        ctest_lista = []
        for i, p in enumerate(palavras):
            if i % 2 == 0 and len(p) > 3:
                ctest_lista.append(p[:len(p)//2] + "____")
            else:
                ctest_lista.append(p)
        texto_ctest = " ".join(ctest_lista)

    return {
        'nivel': nivel,
        'flashcards': flashcards_extraidos,
        'ctest': texto_ctest
    }