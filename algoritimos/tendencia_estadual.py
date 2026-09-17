import sqlite3
import pandas as pd

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# CRESCIMENTO RIO CLARO X SP
# =====================================

query = """
SELECT
    tipo_cancer,
    origem,
    SUM(CASE WHEN ano = 2024 THEN 1 ELSE 0 END) AS ano_2024,
    SUM(CASE WHEN ano = 2025 THEN 1 ELSE 0 END) AS ano_2025
FROM internacoes
GROUP BY tipo_cancer, origem
"""

df = pd.read_sql(query, conn)

# =====================================
# VARIAÇÃO %
# =====================================

df["variacao"] = (
    (df["ano_2025"] - df["ano_2024"])
    /
    df["ano_2024"].replace(0, 1)
) * 100

# =====================================
# PIVOT
# =====================================

pivot = df.pivot_table(
    index="tipo_cancer",
    columns="origem",
    values="variacao"
).reset_index()

pivot.columns.name = None

# =====================================
# DESVIO
# =====================================

pivot["desvio"] = (
    pivot["RIO_CLARO"]
    -
    pivot["SP"]
)

# =====================================
# EVENTO
# =====================================

def classificar(desvio):

    if desvio > 10:
        return "ACIMA_DA_TENDENCIA_ESTADUAL"

    elif desvio < -10:
        return "ABAIXO_DA_TENDENCIA_ESTADUAL"

    return "COMPORTAMENTO_SEMELHANTE"

pivot["evento"] = pivot["desvio"].apply(classificar)

# =====================================
# ORDENAÇÃO
# =====================================

pivot = pivot.sort_values(
    "desvio",
    ascending=False
)

# =====================================
# RESULTADO
# =====================================

print("\n=== TENDÊNCIA ESTADUAL ===\n")

print(
    pivot[
        [
            "tipo_cancer",
            "RIO_CLARO",
            "SP",
            "desvio",
            "evento"
        ]
    ]
)

# =====================================
# SALVAR
# =====================================

pivot.to_sql(
    "tendencia_estadual",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela tendencia_estadual criada.")

conn.close()