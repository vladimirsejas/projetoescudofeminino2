import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

score = pd.read_sql(
    """
    SELECT *
    FROM indicadores_epidemiologicos
    """,
    conn
)

tendencia = pd.read_sql(
    """
    SELECT *
    FROM tendencia_estadual
    """,
    conn
)

anomalias = pd.read_sql(
    """
    SELECT *
    FROM anomalias
    """,
    conn
)

df = score.merge(
    tendencia[["tipo_cancer", "desvio"]],
    on="tipo_cancer",
    how="left"
)

df = df.merge(
    anomalias[["tipo_cancer", "situacao"]],
    on="tipo_cancer",
    how="left"
)

def pontos_anomalia(situacao):
    if situacao == "ANOMALIA_POSITIVA":
        return 20
    elif situacao == "ANOMALIA_NEGATIVA":
        return -20
    return 0

df["pontos_anomalia"] = df["situacao"].apply(
    pontos_anomalia
)

df["pontuacao_final"] = (
    df["score"]
    + (df["desvio"] * 0.20)
    + df["pontos_anomalia"]
)

def classificar(valor):
    if valor >= 90:
        return "CRITICA"
    elif valor >= 70:
        return "ALTA"
    elif valor >= 50:
        return "MEDIA"
    else:
        return "BAIXA"

df["nivel_prioridade"] = df["pontuacao_final"].apply(
    classificar
)

df = df.sort_values(
    "pontuacao_final",
    ascending=False
)

print("\n=== PRIORIZAÃ‡ÃƒO EXECUTIVA ===\n")

print(
    df[
        [
            "tipo_cancer",
            "score",
            "desvio",
            "pontuacao_final",
            "nivel_prioridade"
        ]
    ].to_string(index=False)
)

print("\n=== TOP 3 PRIORIDADES ===\n")

top3 = df.head(3)

for _, row in top3.iterrows():
    print(
        f"{row['tipo_cancer']} - "
        f"Score Final: {row['pontuacao_final']:.2f}"
    )

df.to_sql(
    "priorizacao_executiva",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela priorizacao_executiva criada com sucesso.")

conn.close()
