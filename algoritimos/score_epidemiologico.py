import sqlite3
import pandas as pd

from configuracao_geografica import obter_municipio, salvar_tabela_municipio

# =====================================
# CONEXÃƒO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

MUNICIPIO = obter_municipio()

# =====================================
# INTERNAÃ‡Ã•ES E Ã“BITOS
# =====================================

df = pd.read_sql("""
SELECT
    tipo_cancer,
    COUNT(*) AS internacoes,
    SUM(obito) AS obitos
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer
""", conn, params=(MUNICIPIO,))

# =====================================
# CRESCIMENTO 2024 x 2025
# =====================================

crescimento = pd.read_sql("""
SELECT
    tipo_cancer,
    SUM(CASE WHEN ano = 2024 THEN 1 ELSE 0 END) AS ano_2024,
    SUM(CASE WHEN ano = 2025 THEN 1 ELSE 0 END) AS ano_2025
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer
""", conn, params=(MUNICIPIO,))

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
# JUNÃ‡ÃƒO DOS DADOS
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
# NORMALIZAÃ‡ÃƒO
# =====================================

df["internacoes_norm"] = (
    df["internacoes"]
    /
    df["internacoes"].max()
) * 100

# Mortalidade hospitalar: usa a taxa de obitos por internacoes.
# O SIH/SUS registra obitos ocorridos nas internacoes; quando nenhum
# cancer possui obito registrado no municipio, nao existe denominador
# para normalizar essa dimensao. Nesse caso, ela nao diferencia os
# canceres e sua contribuicao e 0.
df["taxa_obito_hospitalar"] = (
    df["obitos"]
    /
    df["internacoes"]
) * 100

if df["taxa_obito_hospitalar"].max() == 0:
    df["obitos_norm"] = 0
else:
    df["obitos_norm"] = (
        df["taxa_obito_hospitalar"]
        /
        df["taxa_obito_hospitalar"].max()
    ) * 100

# Crescimento: se nao houver crescimento positivo em nenhum cancer,
# a dimensao nao acrescenta prioridade e nao produz divisao por zero.
if df["crescimento"].max() <= 0:
    df["crescimento_norm"] = 0
else:
    df["crescimento_norm"] = (
        df["crescimento"]
        /
        df["crescimento"].max()
    ) * 100

# =====================================
# SCORE EPIDEMIOLÃ“GICO
# =====================================

df["score"] = (
    df["internacoes_norm"] * 0.40
    +
    df["obitos_norm"] * 0.30
    +
    df["crescimento_norm"] * 0.30
)

# =====================================
# CLASSIFICAÃ‡ÃƒO
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
# ORDENAÃ‡ÃƒO
# =====================================

df = df.sort_values(
    "score",
    ascending=False
)

# =====================================
# RESULTADO
# =====================================

print(f"\n=== SCORE EPIDEMIOLÃ“GICO ({MUNICIPIO}) ===\n")

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

salvar_tabela_municipio(
    df[
        [
            "tipo_cancer",
            "internacoes",
            "obitos",
            "crescimento",
            "score",
            "prioridade"
        ]
    ],
    "indicadores_epidemiologicos",
    conn,
    municipio=MUNICIPIO
)

print("\nTabela indicadores_epidemiologicos criada com sucesso.")

conn.close()
