import sqlite3
import pandas as pd

from configuracao_geografica import obter_municipio

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

MUNICIPIO = obter_municipio()

df = pd.read_sql("""
SELECT
    tipo_cancer,
    AVG(dias_permanencia) AS permanencia_media,
    MAX(dias_permanencia) AS permanencia_maxima,
    SUM(dias_permanencia) AS dias_totais
FROM internacoes
WHERE origem = ?
GROUP BY tipo_cancer
""", conn, params=(MUNICIPIO,))

df = df.sort_values(
    "permanencia_media",
    ascending=False
)

print(f"\n=== PERMANÃŠNCIA HOSPITALAR ({MUNICIPIO}) ===\n")

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
