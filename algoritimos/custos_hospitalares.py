import sqlite3
import pandas as pd

from configuracao_geografica import obter_municipio

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

MUNICIPIO = obter_municipio()

df = pd.read_sql("""
SELECT
    tipo_cancer,
    SUM(valor_total) AS valor_total,
    AVG(valor_total) AS valor_medio,
    COUNT(*) AS internacoes
FROM internacoes
WHERE origem = ?
GROUP BY tipo_cancer
""", conn, params=(MUNICIPIO,))

df = df.sort_values(
    "valor_total",
    ascending=False
)

df["ranking_custo"] = range(
    1,
    len(df) + 1
)

print(f"\n=== CUSTOS HOSPITALARES ({MUNICIPIO}) ===\n")

print(df)

df.to_sql(
    "custos_hospitalares",
    conn,
    if_exists="replace",
    index=False
)

print(
    "\nTabela custos_hospitalares criada com sucesso."
)

conn.close()
