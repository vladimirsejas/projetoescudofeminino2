import sqlite3

banco = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS internacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_cancer TEXT,
    origem TEXT,
    ano INTEGER,
    idade INTEGER,
    dias_permanencia INTEGER,
    obito INTEGER,
    valor_total REAL
)
""")

conexao.commit()
conexao.close()

print("Banco criado com sucesso!")
