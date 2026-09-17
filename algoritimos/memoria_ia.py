import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

df = pd.read_sql("""
SELECT *
FROM base_conhecimento
ORDER BY pontuacao_final DESC
""", conn)

memorias = []

for _, row in df.iterrows():

    texto = f"""
Câncer: {row['tipo_cancer']}.

Pontuação final: {row['pontuacao_final']:.2f}.

Classificação: {row['nivel_prioridade']}.

Evento: {row['evento']}.

Situação de anomalia:
{row['situacao']}.

Recomendação:
{row['recomendacao']}
"""

    memorias.append(
        {
            "tipo_cancer": row["tipo_cancer"],
            "memoria": texto.strip()
        }
    )

resultado = pd.DataFrame(memorias)

print("\n=== MEMÓRIA DA IA ===\n")

for _, row in resultado.iterrows():

    print("\n-------------------\n")
    print(row["memoria"])

resultado.to_sql(
    "memoria_ia",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela memoria_ia criada com sucesso.")

conn.close()