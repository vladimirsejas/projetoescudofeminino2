import sqlite3

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

print("\n=== TABELAS DO BANCO ===\n")

tabelas = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

for tabela in tabelas:
    print(tabela[0])

print("\n=== COLUNAS DE tendencia_estadual ===\n")

colunas = conn.execute(
    "PRAGMA table_info(tendencia_estadual)"
).fetchall()

for coluna in colunas:
    print(coluna)

conn.close()
