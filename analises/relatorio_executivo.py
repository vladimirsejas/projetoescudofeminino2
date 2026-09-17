import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

ranking = pd.read_sql("""
SELECT
    tipo_cancer,
    COUNT(*) AS total
FROM internacoes
GROUP BY tipo_cancer
ORDER BY total DESC
""", conexao)

conexao.close()

print()
print("=" * 60)
print("RELATORIO EXECUTIVO - ESCUDO FEMININO")
print("=" * 60)

print()
print("Principais achados:")

print(
    f"1. O cancer com maior numero de internacoes foi "
    f"{ranking.iloc[0]['tipo_cancer']} "
    f"com {ranking.iloc[0]['total']} registros."
)

print(
    f"2. O segundo lugar foi "
    f"{ranking.iloc[1]['tipo_cancer']} "
    f"com {ranking.iloc[1]['total']} registros."
)

print(
    f"3. O terceiro lugar foi "
    f"{ranking.iloc[2]['tipo_cancer']} "
    f"com {ranking.iloc[2]['total']} registros."
)

print()
print("=" * 60)
