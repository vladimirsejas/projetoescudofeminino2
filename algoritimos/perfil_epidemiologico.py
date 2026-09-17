import sqlite3
import pandas as pd

# =====================================
# CONEXÃƒO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# LEITURA DAS TABELAS
# =====================================

priorizacao = pd.read_sql("""
SELECT
    tipo_cancer,
    pontuacao_final,
    nivel_prioridade
FROM priorizacao_executiva
""", conn)

mortalidade = pd.read_sql("""
SELECT
    tipo_cancer,
    taxa_mortalidade
FROM mortalidade
""", conn)

custos = pd.read_sql("""
SELECT
    tipo_cancer,
    valor_total,
    ranking_custo
FROM custos_hospitalares
""", conn)

permanencia = pd.read_sql("""
SELECT
    tipo_cancer,
    permanencia_media
FROM permanencia_hospitalar
""", conn)

faixa = pd.read_sql("""
SELECT *
FROM faixa_etaria
""", conn)

# =====================================
# FAIXA ETÃRIA DOMINANTE
# =====================================

faixa_top = (
    faixa
    .sort_values(
        "internacoes",
        ascending=False
    )
    .drop_duplicates(
        "tipo_cancer"
    )
)

# =====================================
# PERFIL EPIDEMIOLÃ“GICO
# =====================================

perfil = priorizacao.merge(
    mortalidade,
    on="tipo_cancer",
    how="left"
)

perfil = perfil.merge(
    custos,
    on="tipo_cancer",
    how="left"
)

perfil = perfil.merge(
    permanencia,
    on="tipo_cancer",
    how="left"
)

perfil = perfil.merge(
    faixa_top[
        [
            "tipo_cancer",
            "faixa_etaria"
        ]
    ],
    on="tipo_cancer",
    how="left"
)

# =====================================
# ORDENAÃ‡ÃƒO
# =====================================

perfil = perfil.sort_values(
    "pontuacao_final",
    ascending=False
)

# =====================================
# RESULTADO
# =====================================

print("\n=== PERFIL EPIDEMIOLÃ“GICO ===\n")

print(
    perfil[
        [
            "tipo_cancer",
            "pontuacao_final",
            "nivel_prioridade",
            "taxa_mortalidade",
            "valor_total",
            "ranking_custo",
            "permanencia_media",
            "faixa_etaria"
        ]
    ].to_string(index=False)
)

# =====================================
# GRAVA SQLITE
# =====================================

perfil.to_sql(
    "perfil_epidemiologico",
    conn,
    if_exists="replace",
    index=False
)

print(
    "\nTabela perfil_epidemiologico criada com sucesso."
)

conn.close()
