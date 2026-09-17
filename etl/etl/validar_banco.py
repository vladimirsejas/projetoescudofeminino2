import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

print("\nTOTAL DE REGISTROS\n")

print(
    pd.read_sql(
        "SELECT COUNT(*) AS total FROM internacoes",
        conexao
    )
)

print("\nTIPOS DE CANCER\n")

print(
    pd.read_sql(
        """
        SELECT DISTINCT tipo_cancer
        FROM internacoes
        ORDER BY tipo_cancer
        """,
        conexao
    )
)

conexao.close()
