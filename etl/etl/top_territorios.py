import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

sql = """
SELECT
    origem,
    COUNT(*) AS total
FROM internacoes
GROUP BY origem
"""

resultado = pd.read_sql(sql, conexao)

print(resultado)

conexao.close()