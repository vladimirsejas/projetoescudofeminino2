import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

base = pd.read_sql(
    """
    SELECT *
    FROM base_conhecimento
    ORDER BY pontuacao_final DESC
    """,
    conn
)

print("\n=== EXPLICADOR IA ===\n")

cancer = input(
    "Digite o cÃ¢ncer (ou ENTER para o primeiro): "
).upper()

if cancer.strip() == "":

    registro = base.iloc[0]

else:

    filtro = base[
        base["tipo_cancer"].str.upper() == cancer
    ]

    if filtro.empty:

        print("\nCÃ¢ncer nÃ£o encontrado.")
        conn.close()
        exit()

    registro = filtro.iloc[0]

print("\n=== ANÃLISE EXECUTIVA ===\n")

print(
    f"CÃ¢ncer analisado: "
    f"{registro['tipo_cancer']}"
)

print(
    f"Prioridade: "
    f"{registro['nivel_prioridade']}"
)

print(
    f"PontuaÃ§Ã£o Final: "
    f"{registro['pontuacao_final']:.2f}"
)

print("\nJUSTIFICATIVAS:")

print(
    f"- Score epidemiolÃ³gico: "
    f"{registro['score']:.2f}"
)

print(
    f"- Desvio em relaÃ§Ã£o ao Estado: "
    f"{registro['desvio']:.2f}%"
)

print(
    f"- Evento identificado: "
    f"{registro['evento']}"
)

print(
    f"- SituaÃ§Ã£o de anomalia: "
    f"{registro['situacao']}"
)

print(
    f"- MÃ©dia histÃ³rica: "
    f"{registro['media_historica']:.2f}"
)

print(
    f"- Valor observado em 2025: "
    f"{registro['valor_2025']}"
)

print("\nRECOMENDAÃ‡ÃƒO:")

print(
    registro["recomendacao"]
)

texto = f"""
CÃ¢ncer: {registro['tipo_cancer']}

Prioridade: {registro['nivel_prioridade']}

PontuaÃ§Ã£o Final:
{registro['pontuacao_final']:.2f}

Motivos:

Score epidemiolÃ³gico:
{registro['score']:.2f}

Desvio estadual:
{registro['desvio']:.2f}%

Evento:
{registro['evento']}

Anomalia:
{registro['situacao']}

RecomendaÃ§Ã£o:

{registro['recomendacao']}
"""

print("\n=== RESUMO EXECUTIVO ===\n")
print(texto)

conn.close()
