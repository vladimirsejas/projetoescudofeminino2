import sqlite3
import pandas as pd

from configuracao_geografica import (
    obter_municipio,
    salvar_tabela_municipio,
    UF_REFERENCIA
)

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

MUNICIPIO = obter_municipio()

# =====================================
# CRESCIMENTO MUNICÍPIO X SP
#
# Compara sempre o município selecionado com a referência
# estadual (SP) -- nunca entre dois municípios diretamente, e
# nunca mistura outros municípios que existam em internacoes.
# =====================================

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

df = pd.read_sql(query, conn, params=(MUNICIPIO, UF_REFERENCIA))

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
    columns="grupo",
    values="variacao"
).reset_index()

pivot.columns.name = None

# Renomeia para nomes fixos (não o nome do município) logo após o
# pivot: a tabela agora é multi-tenant (várias linhas de municípios
# diferentes, marcadas por uma coluna `municipio`), então o nome da
# coluna de valor não pode variar conforme quem gerou a linha --
# senão salvar_tabela_municipio() falharia ao tentar concatenar
# dataframes com esquemas diferentes.
pivot = pivot.rename(
    columns={"MUNICIPIO": "variacao_municipio", "SP": "variacao_sp"}
)

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
    columns="grupo",
    values="ano_2024"
).reset_index()

pivot_base.columns.name = None

pivot_base = pivot_base.rename(
    columns={
        "MUNICIPIO": "base_municipio",
        "SP": "base_sp"
    }
)

pivot = pivot.merge(pivot_base, on="tipo_cancer", how="left")

# =====================================
# DESVIO
# =====================================

pivot["desvio"] = (
    pivot["variacao_municipio"]
    -
    pivot["variacao_sp"]
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

    if row["base_municipio"] < LIMIAR_AMOSTRA_PEQUENA:
        return (
            f"BAIXA (apenas {int(row['base_municipio'])} internações "
            f"em {MUNICIPIO} em 2024 — percentual pode enganar)"
        )

    if row["base_sp"] < LIMIAR_AMOSTRA_PEQUENA:
        return (
            f"BAIXA (apenas {int(row['base_sp'])} internações "
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

print(f"\n=== TENDÊNCIA ESTADUAL ({MUNICIPIO} x {UF_REFERENCIA}) ===\n")

print(
    pivot[
        [
            "tipo_cancer",
            "variacao_municipio",
            "variacao_sp",
            "desvio",
            "evento",
            "confiabilidade"
        ]
    ].to_string(index=False)
)

# =====================================
# SALVAR
# =====================================

salvar_tabela_municipio(pivot, "tendencia_estadual", conn, municipio=MUNICIPIO)

print("\nTabela tendencia_estadual atualizada com sucesso.")

conn.close()
