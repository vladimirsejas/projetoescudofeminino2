
import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

sql = """
SELECT
    origem,
    COUNT(*) AS total_registros
FROM internacoes
GROUP BY origem
ORDER BY total_registros DESC
"""

resultado = pd.read_sql(sql, conexao)

print()
print("RIO CLARO X SP")
print()
print(resultado)

conexao.close()