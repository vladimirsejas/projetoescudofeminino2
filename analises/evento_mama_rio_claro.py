import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

sql = """
SELECT
    ano,
    COUNT(*) AS internacoes
FROM internacoes
WHERE tipo_cancer = 'MAMA'
AND origem = 'RIO_CLARO'
GROUP BY ano
ORDER BY ano
"""

df = pd.read_sql(sql, conexao)

conexao.close()

print()
print("EVOLUCAO MAMA - RIO CLARO")
print()
print(df)

valor_2024 = int(
    df.loc[df["ano"] == 2024, "internacoes"].values[0]
)

valor_2025 = int(
    df.loc[df["ano"] == 2025, "internacoes"].values[0]
)

variacao = ((valor_2025 - valor_2024) / valor_2024) * 100

print()
print("EVENTO ANALITICO")
print()

print(f"Internacoes 2024: {valor_2024}")
print(f"Internacoes 2025: {valor_2025}")
print(f"Variacao: {variacao:.2f}%")

if variacao > 20:
    print("ALERTA: crescimento expressivo")
elif variacao < -20:
    print("ALERTA: reducao expressiva")
else:
    print("Variacao dentro da faixa esperada")