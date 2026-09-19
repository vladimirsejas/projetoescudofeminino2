import sqlite3
import pandas as pd

from configuracao_geografica import (
    obter_municipio,
    ler_tabela_municipio,
    salvar_tabela_municipio
)

# =====================================
# CONEXÃƒO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

MUNICIPIO = obter_municipio()

# =====================================
# LEITURA DAS TABELAS
# (todas multi-município -- filtrar é obrigatório, senão os merges
# abaixo duplicam linhas assim que outro município for processado)
# =====================================

priorizacao = ler_tabela_municipio(
    "priorizacao_executiva", conn, municipio=MUNICIPIO,
    colunas="tipo_cancer, pontuacao_final, nivel_prioridade"
)

mortalidade = ler_tabela_municipio(
    "mortalidade", conn, municipio=MUNICIPIO,
    colunas="tipo_cancer, taxa_mortalidade"
)

custos = ler_tabela_municipio(
    "custos_hospitalares", conn, municipio=MUNICIPIO,
    colunas="tipo_cancer, valor_total, ranking_custo"
)

permanencia = ler_tabela_municipio(
    "permanencia_hospitalar", conn, municipio=MUNICIPIO,
    colunas="tipo_cancer, permanencia_media"
)

faixa = ler_tabela_municipio("faixa_etaria", conn, municipio=MUNICIPIO)

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

salvar_tabela_municipio(
    perfil, "perfil_epidemiologico", conn, municipio=MUNICIPIO
)

print(
    "\nTabela perfil_epidemiologico criada com sucesso."
)

conn.close()
