import sqlite3
import pandas as pd

from configuracao_geografica import obter_municipio

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

MUNICIPIO = obter_municipio()

df = pd.read_sql("""
SELECT
    tipo_cancer,
    COUNT(*) AS internacoes,
    SUM(obito) AS obitos
FROM internacoes
WHERE origem = ?
GROUP BY tipo_cancer
""", conn, params=(MUNICIPIO,))

df["taxa_mortalidade"] = (
    df["obitos"]
    /
    df["internacoes"]
) * 100

df = df.sort_values(
    "taxa_mortalidade",
    ascending=False
)

print(f"\n=== MORTALIDADE ({MUNICIPIO}) ===\n")

print(df)

df.to_sql(
    "mortalidade",
    conn,
    if_exists="replace",
    index=False
)

print(
    "\nTabela mortalidade criada com sucesso."
)

conn.close()
