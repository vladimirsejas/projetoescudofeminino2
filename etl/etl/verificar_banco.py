import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

sql = """
SELECT *
FROM internacoes
LIMIT 10
"""

resultado = pd.read_sql(sql, conexao)

print(resultado)

conexao.close()
