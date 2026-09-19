import os
from openai import OpenAI


def obter_cliente():
    chave = os.getenv("OPENAI_API_KEY")

    if not chave:
        return None

    return OpenAI(api_key=chave)


INSTRUCOES_BASE = """
Você é a IA de linguagem do Escudo Feminino.

Sua função é explicar os dados fornecidos pelo sistema
de forma clara, objetiva e responsável.

REGRAS:

1. Use somente as informações presentes no contexto fornecido.
2. Não invente números.
3. Não invente diagnósticos.
4. Não transforme associação em causalidade.
5. Quando os dados forem insuficientes, diga claramente.
6. Diferencie dado observado de recomendação.
7. Responda em português do Brasil.
8. Seja clara e direta.
9. O banco e os algoritmos do Escudo Feminino são a fonte dos fatos.
"""

INSTRUCOES_PERFIL = {
    "SIMPLES": (
        "\n10. O público é a população em geral: não use jargão técnico, "
        "não cite pontuação ou termos estatísticos, foque na conclusão "
        "e na ação recomendada."
    ),
    "TECNICO": (
        "\n10. O público é técnico (gestor, secretário, pesquisador): "
        "pode usar termos técnicos e citar números com precisão."
    ),
}


def responder_com_ia(pergunta, contexto, perfil="TECNICO"):
    cliente = obter_cliente()

    if cliente is None:
        return (
            "A IA de linguagem ainda não está configurada. "
            "A chave OPENAI_API_KEY não foi encontrada."
        )

    resposta = cliente.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        instructions=INSTRUCOES_BASE + INSTRUCOES_PERFIL.get(perfil, ""),
        input=f"""
CONTEXTO DO ESCUDO FEMININO:

{contexto}

PERGUNTA DO USUÁRIO:

{pergunta}

Responda à pergunta usando o contexto acima.
"""
    )

    return resposta.output_text
