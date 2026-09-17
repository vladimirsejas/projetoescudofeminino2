import sqlite3

banco = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

cursor = conexao.cursor()

cursor.execute("DELETE FROM internacoes")

conexao.commit()

conexao.close()

print("Tabela internacoes limpa com sucesso!")
