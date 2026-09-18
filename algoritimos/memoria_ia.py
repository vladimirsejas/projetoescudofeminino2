import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

df = pd.read_sql("""
SELECT *
FROM base_conhecimento
ORDER BY pontuacao_final DESC
""", conn)

memorias = []

for _, row in df.iterrows():

    # =====================================
    # CAMADA 1 — O QUE ACONTECEU
    # =====================================

    o_que_aconteceu = (
        f"{row['tipo_cancer']} está classificado como prioridade "
        f"{row['nivel_prioridade']}, com pontuação final de "
        f"{row['pontuacao_final']:.2f}."
    )

    # =====================================
    # CAMADA 2 — ISSO É IMPORTANTE?
    # =====================================

    isso_e_importante = (
        f"Isso é relevante porque {row['nivel_prioridade'].lower()} "
        f"é o nível de atenção que a gestão de saúde deveria dar "
        f"hoje a este câncer, em comparação com os demais "
        f"monitorados pelo Escudo Feminino."
    )

    # =====================================
    # TEXTO FINAL — 5 CAMADAS
    # =====================================

    texto = f"""
CÂNCER: {row['tipo_cancer']}

O QUE ACONTECEU:
{o_que_aconteceu}

POR QUE ACONTECEU:
{row['motivo']}

ISSO É IMPORTANTE?
{isso_e_importante}

QUAL O IMPACTO:
{row['impacto']}

O QUE DEVE SER FEITO:
{row['recomendacao']}
"""

    memorias.append(
        {
            "tipo_cancer": row["tipo_cancer"],
            "nivel_prioridade": row["nivel_prioridade"],
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

print("\nTabela memoria_ia atualizada com sucesso.")

conn.close()
