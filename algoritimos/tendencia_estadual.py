import sqlite3
import pandas as pd

from configuracao_geografica import obter_municipio, UF_REFERENCIA

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"
conn = sqlite3.connect(BANCO)
MUNICIPIO = obter_municipio()

# O município é filtrado pelo campo territorial.
# A referência estadual continua sendo a origem SP,
# que representa o arquivo estadual completo.
query = """
SELECT
    tipo_cancer,
    'MUNICIPIO' AS grupo,
    SUM(CASE WHEN ano = 2024 THEN 1 ELSE 0 END) AS ano_2024,
    SUM(CASE WHEN ano = 2025 THEN 1 ELSE 0 END) AS ano_2025
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer

UNION ALL

SELECT
    tipo_cancer,
    'SP' AS grupo,
    SUM(CASE WHEN ano = 2024 THEN 1 ELSE 0 END) AS ano_2024,
    SUM(CASE WHEN ano = 2025 THEN 1 ELSE 0 END) AS ano_2025
FROM internacoes
WHERE origem = ?
GROUP BY tipo_cancer
"""

df = pd.read_sql(
    query,
    conn,
    params=(MUNICIPIO, UF_REFERENCIA)
)

df["variacao"] = (
    (df["ano_2025"] - df["ano_2024"])
    / df["ano_2024"].replace(0, 1)
) * 100

pivot = df.pivot_table(
    index="tipo_cancer",
    columns="grupo",
    values="variacao"
).reset_index()
pivot.columns.name = None

pivot = pivot.rename(
    columns={
        "MUNICIPIO": MUNICIPIO
    }
)

pivot_base = df.pivot_table(
    index="tipo_cancer",
    columns="grupo",
    values="ano_2024"
).reset_index()
pivot_base.columns.name = None

pivot_base = pivot_base.rename(
    columns={
        "MUNICIPIO": f"base_{MUNICIPIO}",
        "SP": "base_SP"
    }
)

pivot = pivot.merge(pivot_base, on="tipo_cancer", how="left")

pivot["desvio"] = pivot[MUNICIPIO] - pivot["SP"]


def classificar(desvio):
    if desvio > 10:
        return "ACIMA_DA_TENDENCIA_ESTADUAL"
    if desvio < -10:
        return "ABAIXO_DA_TENDENCIA_ESTADUAL"
    return "COMPORTAMENTO_SEMELHANTE"


pivot["evento"] = pivot["desvio"].apply(classificar)

LIMIAR_AMOSTRA_PEQUENA = 10


def classificar_confiabilidade(row):
    if row[f"base_{MUNICIPIO}"] < LIMIAR_AMOSTRA_PEQUENA:
        return (
            f"BAIXA (apenas {int(row[f'base_{MUNICIPIO}'])} internações "
            f"em {MUNICIPIO} em 2024 — percentual pode enganar)"
        )

    if row["base_SP"] < LIMIAR_AMOSTRA_PEQUENA:
        return (
            f"BAIXA (apenas {int(row['base_SP'])} internações "
            "no Estado em 2024 — percentual pode enganar)"
        )

    return "OK"


pivot["confiabilidade"] = pivot.apply(
    classificar_confiabilidade,
    axis=1
)

pivot = pivot.sort_values("desvio", ascending=False)

print(f"\n=== TENDÊNCIA ESTADUAL ({MUNICIPIO} x {UF_REFERENCIA}) ===\n")
print(
    pivot[
        [
            "tipo_cancer",
            MUNICIPIO,
            "SP",
            "desvio",
            "evento",
            "confiabilidade"
        ]
    ].to_string(index=False)
)

pivot.to_sql(
    "tendencia_estadual",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela tendencia_estadual atualizada com sucesso.")
conn.close()
