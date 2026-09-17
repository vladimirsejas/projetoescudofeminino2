import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

priorizacao = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        score,
        pontuacao_final,
        nivel_prioridade
    FROM priorizacao_executiva
    """,
    conn
)

tendencia = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        RIO_CLARO,
        SP,
        desvio,
        evento
    FROM tendencia_estadual
    """,
    conn
)

anomalias = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        media_historica,
        valor_2025,
        desvio_percentual,
        situacao
    FROM anomalias
    """,
    conn
)

base = priorizacao.merge(
    tendencia,
    on="tipo_cancer",
    how="left"
)

base = base.merge(
    anomalias,
    on="tipo_cancer",
    how="left"
)

def gerar_recomendacao(row):

    if row["nivel_prioridade"] == "CRITICA":
        return "Monitoramento prioritario e acompanhamento continuo."

    elif row["nivel_prioridade"] == "ALTA":
        return "Acompanhamento frequente recomendado."

    elif row["nivel_prioridade"] == "MEDIA":
        return "Monitoramento regular."

    else:
        return "Acompanhamento de rotina."

base["recomendacao"] = base.apply(
    gerar_recomendacao,
    axis=1
)

base = base.sort_values(
    "pontuacao_final",
    ascending=False
)

print("\n=== BASE DE CONHECIMENTO ===\n")

print(
    base[
        [
            "tipo_cancer",
            "score",
            "pontuacao_final",
            "nivel_prioridade",
            "RIO_CLARO",
            "SP",
            "desvio",
            "evento",
            "media_historica",
            "valor_2025",
            "desvio_percentual",
            "situacao",
            "recomendacao"
        ]
    ].to_string(index=False)
)

base.to_sql(
    "base_conhecimento",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela base_conhecimento criada com sucesso.")

conn.close()