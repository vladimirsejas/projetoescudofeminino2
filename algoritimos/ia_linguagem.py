import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class RespostaEscudo(BaseModel):
    texto: str = Field(description="Resposta curta e clara em português do Brasil.")
    ressalva: str = Field(
        description="Ressalva metodológica curta. Use vazio quando não houver ressalva adicional."
    )


def obter_cliente():
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        return None
    return genai.Client(api_key=chave)


def responder_com_ia(pergunta, contexto, perfil="TECNICO", memoria=None):
    """
    O Gemini é a camada de linguagem.
    Os números e fatos já foram calculados pelo Escudo e entram no contexto.
    A resposta final é validada por um schema Pydantic antes de chegar à tela.
    """
    cliente = obter_cliente()
    if cliente is None:
        raise RuntimeError("A chave GEMINI_API_KEY não foi encontrada.")

    if perfil == "SIMPLES":
        orientacao_linguagem = (
            "Use linguagem simples, humana e direta. Explique termos técnicos "
            "quando forem indispensáveis."
        )
    else:
        orientacao_linguagem = (
            "Use linguagem técnica, objetiva e adequada a gestores, pesquisadores "
            "e profissionais de saúde pública."
        )

    memoria_texto = ""
    if memoria:
        memoria_texto = (
            "\nHISTÓRICO CURTO DA CONVERSA (use apenas para resolver referências "
            "como 'e esse?', 'e em 2024?', 'e os gastos?'):\n"
            + "\n".join(
                f"- pergunta={m.get('pergunta','')}; assunto={m.get('assunto','')}; "
                f"cancer={m.get('cancer','')}; ano={m.get('ano','')}"
                for m in memoria[-6:]
            )
        )

    prompt = f"""
Você é a camada de linguagem do Escudo Feminino.

Sua função é explicar o conhecimento produzido pelo sistema.
Você NÃO calcula os números e NÃO é a fonte dos dados.

REGRAS OBRIGATÓRIAS:
1. Use somente os fatos presentes no CONTEXTO DO ESCUDO.
2. Nunca invente números, anos, percentuais, custos ou causas.
3. Nunca transforme associação, diferença, correlação, tendência ou anomalia em causalidade.
4. Diferencie claramente dado observado de interpretação.
5. Se a pergunta não puder ser respondida pelo contexto, diga isso.
6. Não chame internações de "casos novos", "incidência" ou "diagnósticos".
7. SIH/SUS registra internações hospitalares/AIHs; uma pessoa pode ter mais de uma AIH.
8. Valores financeiros são valores hospitalares registrados nas AIHs, não o orçamento total da saúde.
9. Óbitos são óbitos ocorridos durante as internações registradas, não mortalidade populacional.
10. Projeções são exploratórias: representam continuidade matemática da tendência, não previsão clínica.
11. Não dê diagnóstico ou aconselhamento médico individual.
12. Não transforme sinais do sistema em ordem de gasto. Para planejamento, diga que os sinais podem orientar investigação e discussão, mas a decisão depende de outras informações da gestão.
13. Responda em português do Brasil.
14. {orientacao_linguagem}
15. Seja curta: normalmente 2 a 5 parágrafos ou uma pequena lista.
16. Não repita todos os números se a pergunta pedir apenas uma explicação.

CONTEXTO DO ESCUDO FEMININO:
{contexto}
{memoria_texto}

PERGUNTA:
{pergunta}
"""

    response = cliente.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": RespostaEscudo,
        },
    )

    if getattr(response, "parsed", None) is not None:
        resultado = response.parsed
    else:
        resultado = RespostaEscudo.model_validate_json(response.text)

    texto = resultado.texto.strip()
    if resultado.ressalva.strip():
        texto += "\n\n" + resultado.ressalva.strip()
    return texto


def gerar_resposta(pergunta, contexto):
    return responder_com_ia(pergunta, contexto, "TECNICO")
