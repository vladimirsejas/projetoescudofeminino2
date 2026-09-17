import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

print("\n=== ESCUDO FEMININO IA ===\n")

pergunta = input("Pergunta: ").upper()

# =====================================
# PRIORIDADE
# =====================================

if (
    "ATENCAO" in pergunta
    or "ATENÃ‡ÃƒO" in pergunta
    or "PRIORIDADE" in pergunta
    or "RISCO" in pergunta
):

    df = pd.read_sql("""
    SELECT *
    FROM priorizacao_executiva
    ORDER BY pontuacao_final DESC
    LIMIT 1
    """, conn)

    r = df.iloc[0]

    print("\nResposta:\n")

    print(
        f"O cÃ¢ncer que merece maior atenÃ§Ã£o "
        f"Ã© {r['tipo_cancer']}."
    )

# =====================================
# ANOMALIAS
# =====================================

elif (
    "ANOMALIA" in pergunta
    or "PADRAO" in pergunta
    or "PADRÃƒO" in pergunta
):

    df = pd.read_sql("""
    SELECT *
    FROM anomalias
    WHERE situacao <> 'NORMAL'
    """, conn)

    print("\nResposta:\n")

    if df.empty:

        print(
            "Nenhuma anomalia identificada."
        )

    else:

        print(
            df[
                ["tipo_cancer", "situacao"]
            ]
        )

# =====================================
# TENDÃŠNCIA
# =====================================

elif (
    "TENDENCIA" in pergunta
    or "TENDÃŠNCIA" in pergunta
    or "ESTADUAL" in pergunta
):

    df = pd.read_sql("""
    SELECT *
    FROM tendencia_estadual
    ORDER BY desvio DESC
    LIMIT 1
    """, conn)

    r = df.iloc[0]

    print("\nResposta:\n")

    print(
        f"{r['tipo_cancer']} estÃ¡ "
        f"{r['desvio']:.2f}% acima "
        f"da tendÃªncia estadual."
    )

# =====================================
# INCIDÃŠNCIA
# =====================================

elif (
    "INCIDENCIA" in pergunta
    or "INCIDÃŠNCIA" in pergunta
    or "INTERNACOES" in pergunta
    or "INTERNAÃ‡Ã•ES" in pergunta
):

    df = pd.read_sql("""
    SELECT
        tipo_cancer,
        COUNT(*) total
    FROM internacoes
    GROUP BY tipo_cancer
    ORDER BY total DESC
    LIMIT 1
    """, conn)

    r = df.iloc[0]

    print("\nResposta:\n")

    print(
        f"O cÃ¢ncer com maior incidÃªncia "
        f"hospitalar Ã© "
        f"{r['tipo_cancer']}."
    )

else:

    print(
        "\nPergunta ainda nÃ£o reconhecida."
    )

conn.close()
