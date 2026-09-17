import sqlite3
from datetime import datetime

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS perguntas_usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT,
    pergunta TEXT
)
""")

print("\n=== APRENDIZADO DE PERGUNTAS ===\n")

while True:

    pergunta = input(
        "Digite uma pergunta (ou sair): "
    )

    if pergunta.lower() == "sair":
        break

    cursor.execute(
        """
        INSERT INTO perguntas_usuarios
        (
            data_hora,
            pergunta
        )
        VALUES (?, ?)
        """,
        (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            pergunta
        )
    )

    conn.commit()

    print(
        "Pergunta registrada."
    )

conn.close()

print(
    "\nTabela perguntas_usuarios atualizada."
)