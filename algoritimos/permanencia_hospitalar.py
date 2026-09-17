import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

df = pd.read_sql("""
SELECT
    tipo_cancer,
    AVG(dias_permanencia) AS permanencia_media,
    MAX(dias_permanencia) AS permanencia_maxima,
    SUM(dias_permanencia) AS dias_totais
FROM internacoes
GROUP BY tipo_cancer
""", conn)

df = df.sort_values(
    "permanencia_media",
    ascending=False
)

print("\n=== PERMANÃŠNCIA HOSPITALAR ===\n")

print(df)

df.to_sql(
    "permanencia_hospitalar",
    conn,
    if_exists="replace",
    index=False
)

print(
    "\nTabela permanencia_hospitalar criada com sucesso."
)

conn.close()
