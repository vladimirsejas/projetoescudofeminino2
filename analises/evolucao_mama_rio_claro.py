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

resultado = pd.read_sql(sql, conexao)

print()
print("EVOLUCAO DO CANCER DE MAMA - RIO CLARO")
print()
print(resultado)

conexao.close()