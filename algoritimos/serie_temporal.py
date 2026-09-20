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
# SÉRIE TEMPORAL POR ANO
#
# Base para uma futura camada preditiva: agrega internações e óbitos
# por tipo_cancer x ano, para todos os anos que existirem em
# internacoes -- ao contrário de tendencia_estadual.py, que compara
# só 2024 x 2025, aqui a quantidade de anos vem inteiramente do
# banco. Carregar mais histórico (ex.: 2013-2025) aumenta esta série
# automaticamente, sem precisar mudar este script.
# =====================================

query = """
SELECT
    tipo_cancer,
    'MUNICIPIO' AS grupo,
    ano,
    COUNT(*) AS internacoes,
    SUM(obito) AS obitos
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer, ano

UNION ALL

SELECT
    tipo_cancer,
    'SP' AS grupo,
    ano,
    COUNT(*) AS internacoes,
    SUM(obito) AS obitos
FROM internacoes
WHERE origem = ?
GROUP BY tipo_cancer, ano
"""

df = pd.read_sql(query, conn, params=(MUNICIPIO, UF_REFERENCIA))

# =====================================
# TAXA DE MORTALIDADE
# =====================================

df["taxa_mortalidade"] = (
    df["obitos"]
    /
    df["internacoes"].replace(0, 1)
) * 100

# =====================================
# ORDENAÇÃO
# =====================================

df = df.sort_values(["tipo_cancer", "ano", "grupo"])

# =====================================
# RESULTADO
# =====================================

print(f"\n=== SÉRIE TEMPORAL ANUAL ({MUNICIPIO} x {UF_REFERENCIA}) ===\n")

print(
    df[
        [
            "tipo_cancer",
            "grupo",
            "ano",
            "internacoes",
            "obitos",
            "taxa_mortalidade"
        ]
    ].to_string(index=False)
)

# =====================================
# SALVAR
# =====================================

salvar_tabela_municipio(df, "serie_temporal_anual", conn, municipio=MUNICIPIO)

print("\nTabela serie_temporal_anual atualizada com sucesso.")

conn.close()
