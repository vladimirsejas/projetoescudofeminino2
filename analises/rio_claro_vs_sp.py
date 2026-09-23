
import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

# Rio Claro = moradoras de Rio Claro (municipio); SP = o Estado
# inteiro (origem). Desde que a carga lê só os arquivos estaduais,
# toda linha tem origem = 'SP' -- agrupar por origem não separa mais
# as cidades.
sql = """
SELECT 'RIO_CLARO' AS territorio, COUNT(*) AS total_registros
FROM internacoes WHERE municipio = 'RIO_CLARO'
UNION ALL
SELECT 'SP', COUNT(*) FROM internacoes WHERE origem = 'SP'
"""

resultado = pd.read_sql(sql, conexao)

print()
print("RIO CLARO X SP")
print()
print(resultado)

conexao.close()
