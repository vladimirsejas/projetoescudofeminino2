import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

df = pd.read_sql("""
SELECT
    tipo_cancer,
    COUNT(*) AS internacoes,
    SUM(obito) AS obitos
FROM internacoes
GROUP BY tipo_cancer
""", conn)

df["taxa_mortalidade"] = (
    df["obitos"]
    /
    df["internacoes"]
) * 100

df = df.sort_values(
    "taxa_mortalidade",
    ascending=False
)

print("\n=== MORTALIDADE ===\n")

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