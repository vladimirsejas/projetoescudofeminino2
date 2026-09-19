import sqlite3
import pandas as pd

from configuracao_geografica import obter_municipio, salvar_tabela_municipio

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

MUNICIPIO = obter_municipio()

# =====================================
# DADOS BASE
# =====================================

df = pd.read_sql("""
SELECT
    tipo_cancer,
    idade,
    obito
FROM internacoes
WHERE origem = ?
""", conn, params=(MUNICIPIO,))

# =====================================
# FAIXA ETÁRIA
# (mesma regra já usada em faixa_etaria.py —
# reaproveitando o critério, não reinventando)
# =====================================

def faixa(idade):

    if idade < 20:
        return "0-19"

    elif idade < 40:
        return "20-39"

    elif idade < 60:
        return "40-59"

    elif idade < 80:
        return "60-79"

    else:
        return "80+"

df["faixa_etaria"] = df["idade"].apply(faixa)

# =====================================
# TAXA DE MORTALIDADE POR FAIXA ETÁRIA
# DENTRO DE CADA CÂNCER
#
# Isso é diferente da taxa de mortalidade
# geral (mortalidade.py): aqui a pergunta é
# "dentro do câncer X, qual faixa etária
# morre proporcionalmente mais" — é isso que
# define vulnerabilidade, não o total geral.
# =====================================

agrupado = (
    df.groupby(["tipo_cancer", "faixa_etaria"])
    .agg(
        internacoes=("obito", "size"),
        obitos=("obito", "sum")
    )
    .reset_index()
)

agrupado["taxa_mortalidade_faixa"] = (
    agrupado["obitos"] / agrupado["internacoes"]
) * 100

# =====================================
# CONFIABILIDADE
# (mesmo princípio já aplicado em
# tendencia_estadual.py e anomalias.py —
# taxa calculada sobre poucos casos pode
# enganar)
# =====================================

LIMIAR_AMOSTRA_PEQUENA = 10

def classificar_confiabilidade(row):

    if row["internacoes"] < LIMIAR_AMOSTRA_PEQUENA:
        return (
            f"BAIXA (apenas {int(row['internacoes'])} internações "
            f"nessa faixa etária — taxa pode enganar)"
        )

    return "OK"

agrupado["confiabilidade"] = agrupado.apply(
    classificar_confiabilidade, axis=1
)

# =====================================
# FAIXA MAIS VULNERÁVEL POR CÂNCER
#
# Prioriza faixas com confiabilidade OK;
# só usa uma faixa de baixa confiabilidade
# se não houver nenhuma outra opção.
# =====================================

resultado = []

for cancer in agrupado["tipo_cancer"].unique():

    sub = agrupado[agrupado["tipo_cancer"] == cancer]

    sub_confiavel = sub[sub["confiabilidade"] == "OK"]

    base_sub = sub_confiavel if not sub_confiavel.empty else sub

    linha = base_sub.sort_values(
        "taxa_mortalidade_faixa", ascending=False
    ).iloc[0]

    resultado.append(
        {
            "tipo_cancer": cancer,
            "faixa_mais_vulneravel": linha["faixa_etaria"],
            "taxa_mortalidade_faixa": round(
                linha["taxa_mortalidade_faixa"], 2
            ),
            "internacoes_faixa": int(linha["internacoes"]),
            "obitos_faixa": int(linha["obitos"]),
            "confiabilidade": linha["confiabilidade"]
        }
    )

vulnerabilidade = pd.DataFrame(resultado)

vulnerabilidade = vulnerabilidade.sort_values(
    "taxa_mortalidade_faixa", ascending=False
)

# =====================================
# RESULTADO
# =====================================

print(f"\n=== VULNERABILIDADE POR FAIXA ETÁRIA ({MUNICIPIO}) ===\n")

print(vulnerabilidade.to_string(index=False))

# =====================================
# SALVAR
# =====================================

salvar_tabela_municipio(
    vulnerabilidade, "vulnerabilidade", conn, municipio=MUNICIPIO
)

print("\nTabela vulnerabilidade criada com sucesso.")

conn.close()
