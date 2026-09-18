import unicodedata


def normalizar(texto):

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        c
        for c in texto
        if not unicodedata.combining(c)
    )

    return texto.upper()


def identificar_intencao(pergunta):

    pergunta = normalizar(pergunta)

    if any(
        termo in pergunta
        for termo in [
            "ATENCAO",
            "PRIORIDADE",
            "RISCO",
            "URGENTE",
            "PREOCUPA"
        ]
    ):
        return "PRIORIDADE"

    if any(
        termo in pergunta
        for termo in [
            "MORTALIDADE",
            "MORTE",
            "OBITO",
            "LETAL"
        ]
    ):
        return "MORTALIDADE"

    if any(
        termo in pergunta
        for termo in [
            "CUSTO",
            "GASTO",
            "ORCAMENTO"
        ]
    ):
        return "CUSTO"

    if any(
        termo in pergunta
        for termo in [
            "VULNERAVEL",
            "VULNERABILIDADE"
        ]
    ):
        return "VULNERABILIDADE"

    return "DESCONHECIDA"