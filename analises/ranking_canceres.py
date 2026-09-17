import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

sql = """
SELECT
    tipo_cancer,
    COUNT(*) AS total_internacoes
FROM internacoes
GROUP BY tipo_cancer
ORDER BY total_internacoes DESC
"""

resultado = pd.read_sql(sql, conexao)

print("\nRANKING DOS CÂNCERES\n")
print(resultado)

conexao.close()