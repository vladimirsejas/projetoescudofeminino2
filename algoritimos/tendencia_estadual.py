import sqlite3
import pandas as pd

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

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
# PIVOT DA VARIAÇÃO
# =====================================

pivot = df.pivot_table(
    index="tipo_cancer",
    columns="origem",
    values="variacao"
).reset_index()

pivot.columns.name = None

# =====================================
# PIVOT DA BASE (ano_2024)
#
# Guardamos também o número absoluto de
# internações em 2024, para poder avaliar
# se o percentual calculado é confiável ou
# se está inflado por uma base pequena.
# =====================================

pivot_base = df.pivot_table(
    index="tipo_cancer",
    columns="origem",
    values="ano_2024"
).reset_index()

pivot_base.columns.name = None

pivot_base = pivot_base.rename(
    columns={
        "RIO_CLARO": "base_RIO_CLARO",
        "SP": "base_SP"
    }
)

pivot = pivot.merge(pivot_base, on="tipo_cancer", how="left")

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
# CONFIABILIDADE ESTATÍSTICA
#
# Um percentual calculado sobre uma base
# pequena de casos em 2024 pode parecer
# dramático sem ser representativo (ex.:
# ir de 2 para 9 casos já é +350%, mesmo
# sendo uma variação pequena em números
# absolutos). Abaixo do limiar, marcamos
# a linha como de baixa confiabilidade.
# =====================================

LIMIAR_AMOSTRA_PEQUENA = 10

def classificar_confiabilidade(row):

    if row["base_RIO_CLARO"] < LIMIAR_AMOSTRA_PEQUENA:
        return (
            f"BAIXA (apenas {int(row['base_RIO_CLARO'])} internações "
            f"em Rio Claro em 2024 — percentual pode enganar)"
        )

    if row["base_SP"] < LIMIAR_AMOSTRA_PEQUENA:
        return (
            f"BAIXA (apenas {int(row['base_SP'])} internações "
            f"no Estado em 2024 — percentual pode enganar)"
        )

    return "OK"

pivot["confiabilidade"] = pivot.apply(
    classificar_confiabilidade, axis=1
)

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
            "evento",
            "confiabilidade"
        ]
    ].to_string(index=False)
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

print("\nTabela tendencia_estadual atualizada com sucesso.")

conn.close()
