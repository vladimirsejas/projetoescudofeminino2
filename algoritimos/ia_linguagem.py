import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def obter_cliente():
    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        return None

    return genai.Client(api_key=chave)


def responder_com_ia(pergunta, contexto, perfil="TECNICO"):
    cliente = obter_cliente()

    if cliente is None:
        raise RuntimeError(
            "A chave GEMINI_API_KEY não foi encontrada."
        )

    if perfil == "SIMPLES":
        orientacao_linguagem = (
            "Use linguagem simples, clara e acessível, evitando "
            "jargões técnicos desnecessários."
        )
    else:
        orientacao_linguagem = (
            "Use linguagem técnica, objetiva e adequada a gestores, "
            "pesquisadores e profissionais de saúde pública."
        )

    response = cliente.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"""
Você é a IA de linguagem do Escudo Feminino.

Sua função é EXPLICAR o conhecimento produzido pelo sistema.
Você não é a fonte dos dados. O banco de dados e os algoritmos
do Escudo Feminino são a fonte dos fatos.

REGRAS:

1. Use somente as informações presentes no contexto fornecido.
2. Não invente números, fatos ou indicadores.
3. Não invente diagnósticos.
4. Não transforme associação, diferença ou tendência em causalidade.
5. Se o contexto não tiver informação suficiente para responder,
   diga claramente que os dados disponíveis não permitem concluir.
6. Diferencie claramente dado observado, interpretação e recomendação.
7. Não altere os valores fornecidos pelo sistema.
8. Responda em português do Brasil.
9. Seja clara, objetiva e direta.
10. Os dados do Escudo Feminino vêm do SIH/SUS e representam
    internações hospitalares (AIH — Autorização de Internação
    Hospitalar), não casos novos nem incidência: uma mesma paciente
    pode gerar mais de uma AIH para o mesmo tratamento ou
    complicação. Nunca descreva esses registros como "casos novos",
    "casos diagnosticados" ou "incidência". Prefira "internações
    hospitalares", "volume de internações" ou "produção
    assistencial registrada".
11. {orientacao_linguagem}

CONTEXTO DO ESCUDO FEMININO:

{contexto}

PERGUNTA DO USUÁRIO:

{pergunta}

Responda à pergunta usando o contexto acima.
"""
    )

    return response.text


def gerar_resposta(pergunta, contexto):
    return responder_com_ia(
        pergunta,
        contexto,
        "TECNICO"
    )
