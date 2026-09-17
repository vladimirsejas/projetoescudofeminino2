import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

memoria = pd.read_sql("""
SELECT *
FROM memoria_ia
""", conn)

print("\n=== ESCUDO FEMININO IA ===\n")

pergunta = input("Pergunta: ").upper()

if "ATENCAO" in pergunta or "ATENÇÃO" in pergunta:

    top = pd.read_sql("""
    SELECT *
    FROM priorizacao_executiva
    ORDER BY pontuacao_final DESC
    LIMIT 1
    """, conn)

    linha = top.iloc[0]

    print("\nResposta:\n")

    print(
        f"O câncer que merece maior atenção atualmente "
        f"é {linha['tipo_cancer']}."
    )

    print(
        f"Classificação: "
        f"{linha['nivel_prioridade']}."
    )

    print(
        f"Pontuação final: "
        f"{linha['pontuacao_final']:.2f}."
    )

elif "TOP" in pergunta:

    top3 = pd.read_sql("""
    SELECT *
    FROM priorizacao_executiva
    ORDER BY pontuacao_final DESC
    LIMIT 3
    """, conn)

    print("\nResposta:\n")

    for i, row in top3.iterrows():

        print(
            f"{i+1}º "
            f"{row['tipo_cancer']} "
            f"({row['pontuacao_final']:.2f})"
        )

elif "ANOMALIA" in pergunta:

    resultado = pd.read_sql("""
    SELECT *
    FROM anomalias
    WHERE situacao <> 'NORMAL'
    """, conn)

    print("\nResposta:\n")

    if resultado.empty:

        print(
            "Nenhuma anomalia identificada."
        )

    else:

        for _, row in resultado.iterrows():

            print(
                f"{row['tipo_cancer']} - "
                f"{row['situacao']}"
            )

else:

    print(
        "\nPergunta ainda não reconhecida "
        "pela IA."
    )

conn.close()