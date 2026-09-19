import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "algoritimos"))

from ia_linguagem import responder_com_ia
from motor_raciocinio import contexto_geral_raciocinado, contexto_para_ia


CASOS = [
    {"pergunta": "Qual câncer merece mais atenção?", "tipo": "geral"},
    {"pergunta": "Qual câncer mais mata?", "tipo": "geral"},
    {"pergunta": "Qual câncer está acima da tendência estadual?", "tipo": "geral"},
    {"pergunta": "Existem comportamentos anormais?", "tipo": "geral"},
    {"pergunta": "Fale sobre MAMA.", "tipo": "MAMA"},
    {"pergunta": "Por que a MAMA é uma prioridade?", "tipo": "MAMA"},
    {"pergunta": "Qual é o impacto da situação da MAMA?", "tipo": "MAMA"},
    {"pergunta": "O que deve ser feito em relação à MAMA?", "tipo": "MAMA"},
]


def obter_contexto(tipo):
    if tipo == "geral":
        return contexto_geral_raciocinado()
    return contexto_para_ia(tipo)


def gerar_relatorio():
    resultados = []

    for indice, caso in enumerate(CASOS, start=1):
        pergunta = caso["pergunta"]
        contexto = obter_contexto(caso["tipo"])

        if not contexto:
            resultados.append(
                f"""## Caso {indice}

**Pergunta:** {pergunta}

**Status:** CONTEXTO NÃO DISPONÍVEL

O teste não conseguiu obter o contexto necessário.
"""
            )
            continue

        try:
            resposta = responder_com_ia(
                pergunta,
                contexto,
                "TECNICO",
            )
            erro = None
        except Exception as exc:
            resposta = ""
            erro = str(exc)

        if erro:
            corpo = f"""## Caso {indice}

**Pergunta:** {pergunta}

**Status:** ERRO NA RESPOSTA DA IA

{erro}
"""
        else:
            corpo = f"""## Caso {indice}

**Pergunta:** {pergunta}

### Resposta gerada pelo Gemini

{resposta}

### Avaliação humana

| Critério | Registro |
|---|---|
| 1. Correção | A resposta está de acordo com os dados do contexto? |
| 2. Rastreabilidade | É possível identificar de onde vêm os fatos apresentados? |
| 3. Explicação | A resposta explica o dado de forma compreensível? |
| 4. Impacto | Explica a relevância do achado sem exagerar? |
| 5. Recomendação | A recomendação permanece dentro do que os dados permitem? |
| 6. Adequação ao público | A linguagem é adequada a um gestor/profissional técnico? |
| 7. Limitações e causalidade | Evita inventar causalidade ou conclusões não sustentadas? |
| 8. Consistência | Mantém os valores e conclusões do contexto sem contradizê-los? |

**Observações:**  
"""

        resultados.append(corpo)

    relatorio = f"""# Avaliação de Respostas V2 — Escudo Feminino

Data da execução: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Objetivo

Testar a qualidade das respostas produzidas pela camada de linguagem
a partir dos contextos oficiais do Escudo Feminino.

Este teste não recalcula indicadores e não altera os algoritmos
determinísticos. Ele verifica as respostas da IA sobre oito critérios
qualitativos.

## Critérios

1. Correção
2. Rastreabilidade
3. Explicação
4. Impacto
5. Recomendação
6. Adequação ao público
7. Limitações e ausência de causalidade indevida
8. Consistência

---

""" + "\n\n".join(resultados)

    saida = ROOT_DIR / "avaliacao_respostas_v2.md"
    saida.write_text(relatorio, encoding="utf-8")
    print(f"Relatório gerado: {saida}")
    print(f"Casos avaliados: {len(CASOS)}")


if __name__ == "__main__":
    gerar_relatorio()
