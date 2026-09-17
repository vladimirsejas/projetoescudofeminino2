import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

df = pd.read_sql("""
SELECT *
FROM perfil_epidemiologico
ORDER BY pontuacao_final DESC
""", conn)

fichas = []

for _, row in df.iterrows():

    ficha = f"""
CÂNCER: {row['tipo_cancer']}

PRIORIDADE:
{row['nivel_prioridade']}

PONTUAÇÃO:
{row['pontuacao_final']:.2f}

MORTALIDADE:
{row['taxa_mortalidade']:.2f}%

FAIXA ETÁRIA PREDOMINANTE:
{row['faixa_etaria']}

PERMANÊNCIA MÉDIA:
{row['permanencia_media']:.2f} dias

CUSTO TOTAL:
R$ {row['valor_total']:,.2f}
"""

    fichas.append(
        {
            "tipo_cancer": row["tipo_cancer"],
            "ficha": ficha
        }
    )

resultado = pd.DataFrame(fichas)

print("\n=== FICHAS IA ===\n")

for _, row in resultado.iterrows():

    print("\n--------------------------\n")
    print(row["ficha"])

resultado.to_sql(
    "fichas_ia",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela fichas_ia criada com sucesso.")

conn.close()