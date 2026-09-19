import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

resultado = pd.read_sql(
    "PRAGMA table_info(internacoes)",
    conexao
)

print(resultado)

conexao.close()
