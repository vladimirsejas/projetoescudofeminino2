import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

sql = """
SELECT
    tipo_cancer,
    COUNT(*) AS total
FROM internacoes
WHERE origem = 'RIO_CLARO'
GROUP BY tipo_cancer
ORDER BY total DESC
"""

resultado = pd.read_sql(sql, conexao)

print()
print("CANCERES EM RIO CLARO")
print()
print(resultado)

conexao.close()

