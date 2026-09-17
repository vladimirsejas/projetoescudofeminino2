import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

sql = """
SELECT
    tipo_cancer,
    COUNT(*) as total
FROM internacoes
GROUP BY tipo_cancer
ORDER BY total DESC
"""

resultado = pd.read_sql(sql, conexao)

print(resultado)

conexao.close()