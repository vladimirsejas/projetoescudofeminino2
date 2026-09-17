import sqlite3
import pandas as pd

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# INTERNAÇÕES E ÓBITOS
# =====================================

df = pd.read_sql("""
SELECT
    tipo_cancer,
    COUNT(*) AS internacoes,
    SUM(obito) AS obitos
FROM internacoes
GROUP BY tipo_cancer
""", conn)

# =====================================
# CRESCIMENTO 2024 x 2025
# =====================================

crescimento = pd.read_sql("""
SELECT
    tipo_cancer,
    SUM(CASE WHEN ano = 2024 THEN 1 ELSE 0 END) AS ano_2024,
    SUM(CASE WHEN ano = 2025 THEN 1 ELSE 0 END) AS ano_2025
FROM internacoes
GROUP BY tipo_cancer
""", conn)

crescimento["crescimento"] = (
    (
        crescimento["ano_2025"]
        -
        crescimento["ano_2024"]
    )
    /
    crescimento["ano_2024"].replace(0, 1)
) * 100

# =====================================
# JUNÇÃO DOS DADOS
# =====================================

df = df.merge(
    crescimento[
        [
            "tipo_cancer",
            "crescimento"
        ]
    ],
    on="tipo_cancer"
)

# =====================================
# NORMALIZAÇÃO
# =====================================

df["internacoes_norm"] = (
    df["internacoes"]
    /
    df["internacoes"].max()
) * 100

df["obitos_norm"] = (
    df["obitos"]
    /
    df["obitos"].max()
) * 100

df["crescimento_norm"] = (
    df["crescimento"]
    /
    df["crescimento"].max()
) * 100

# =====================================
# SCORE EPIDEMIOLÓGICO
# =====================================

df["score"] = (
    df["internacoes_norm"] * 0.40
    +
    df["obitos_norm"] * 0.30
    +
    df["crescimento_norm"] * 0.30
)

# =====================================
# CLASSIFICAÇÃO
# =====================================

def classificar(score):

    if score >= 80:
        return "CRITICA"

    elif score >= 60:
        return "ALTA"

    elif score >= 40:
        return "MEDIA"

    else:
        return "BAIXA"


df["prioridade"] = df["score"].apply(classificar)

# =====================================
# ORDENAÇÃO
# =====================================

df = df.sort_values(
    "score",
    ascending=False
)

# =====================================
# RESULTADO
# =====================================

print("\n=== SCORE EPIDEMIOLÓGICO ===\n")

print(
    df[
        [
            "tipo_cancer",
            "internacoes",
            "obitos",
            "crescimento",
            "score",
            "prioridade"
        ]
    ]
)

# =====================================
# GRAVAR NO SQLITE
# =====================================

df[
    [
        "tipo_cancer",
        "internacoes",
        "obitos",
        "crescimento",
        "score",
        "prioridade"
    ]
].to_sql(
    "indicadores_epidemiologicos",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela indicadores_epidemiologicos criada com sucesso.")

conn.close()