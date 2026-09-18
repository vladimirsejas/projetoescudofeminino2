import sqlite3
import pandas as pd

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# LEITURA DAS TABELAS JÁ EXISTENTES
# (nenhuma tabela nova é criada aqui)
# =====================================

priorizacao = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        score,
        pontuacao_final,
        nivel_prioridade
    FROM priorizacao_executiva
    """,
    conn
)

tendencia = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        RIO_CLARO,
        SP,
        desvio,
        evento,
        confiabilidade
    FROM tendencia_estadual
    """,
    conn
)

anomalias = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        media_historica,
        valor_2025,
        desvio_percentual,
        situacao
    FROM anomalias
    """,
    conn
)

mortalidade = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        taxa_mortalidade
    FROM mortalidade
    """,
    conn
)

custos = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        valor_total,
        ranking_custo
    FROM custos_hospitalares
    """,
    conn
)

permanencia = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        permanencia_media
    FROM permanencia_hospitalar
    """,
    conn
)

faixa = pd.read_sql(
    """
    SELECT *
    FROM faixa_etaria
    """,
    conn
)

# faixa etária predominante de cada câncer
# (mesma lógica já usada em perfil_epidemiologico.py)
faixa_top = (
    faixa
    .sort_values("internacoes", ascending=False)
    .drop_duplicates("tipo_cancer")
)

# =====================================
# JUNÇÃO DE TUDO EM UMA ÚNICA BASE
# =====================================

base = priorizacao.merge(tendencia, on="tipo_cancer", how="left")
base = base.merge(anomalias, on="tipo_cancer", how="left")
base = base.merge(mortalidade, on="tipo_cancer", how="left")
base = base.merge(custos, on="tipo_cancer", how="left")
base = base.merge(permanencia, on="tipo_cancer", how="left")
base = base.merge(
    faixa_top[["tipo_cancer", "faixa_etaria"]],
    on="tipo_cancer",
    how="left"
)


# =====================================
# CAMADA 1 — POR QUE ACONTECEU (motivo)
#
# Regra: nunca afirmar causa. Apenas descrever
# associação, mudança de padrão ou desvio.
# =====================================

def gerar_motivo(row):

    partes = []

    if row["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL":
        partes.append(
            f"o número de internações em Rio Claro cresceu "
            f"{row['desvio']:.1f} pontos percentuais a mais "
            f"que o Estado de São Paulo no mesmo período"
        )

    elif row["evento"] == "ABAIXO_DA_TENDENCIA_ESTADUAL":
        partes.append(
            f"o número de internações em Rio Claro cresceu "
            f"{abs(row['desvio']):.1f} pontos percentuais a menos "
            f"que o Estado de São Paulo no mesmo período"
        )

    else:
        partes.append(
            "o comportamento de Rio Claro acompanha de perto "
            "o comportamento observado no Estado de São Paulo"
        )

    if row["situacao"] == "ANOMALIA_POSITIVA":
        partes.append(
            f"o volume de 2025 ({int(row['valor_2025'])} internações) "
            f"ficou {row['desvio_percentual']:.1f}% acima da média "
            f"histórica, o que caracteriza um desvio fora do padrão "
            f"dos anos anteriores"
        )

    elif row["situacao"] == "ANOMALIA_NEGATIVA":
        partes.append(
            f"o volume de 2025 ({int(row['valor_2025'])} internações) "
            f"ficou {abs(row['desvio_percentual']):.1f}% abaixo da "
            f"média histórica, também um desvio fora do padrão"
        )

    motivo = "Isso ocorre porque " + "; e ".join(partes) + "."

    motivo += (
        " Esses dados mostram uma associação e uma mudança de "
        "padrão, não uma causa comprovada — a origem exata do "
        "comportamento exige investigação qualitativa (por exemplo: "
        "mudança de protocolo de diagnóstico, campanha de rastreamento "
        "ou fator sazonal)."
    )

    if row.get("confiabilidade", "OK") != "OK":
        motivo += (
            f" ATENÇÃO: {row['confiabilidade']}. O percentual de "
            f"desvio em relação ao Estado deve ser interpretado com "
            f"cautela, pois é calculado sobre uma base pequena de "
            f"casos em 2024 — uma variação em números absolutos "
            f"pequenos gera percentuais desproporcionalmente altos."
        )

    return motivo


# =====================================
# CAMADA 2 — QUAL O IMPACTO
#
# Só traduz para uma dimensão quando há
# número que sustente a afirmação.
# =====================================

def gerar_impacto(row):

    partes = []

    if row["nivel_prioridade"] in ("CRITICA", "ALTA"):
        partes.append(
            "para a gestão pública, este câncer está hoje entre os "
            "de maior risco relativo entre os monitorados, o que "
            "sugere priorizá-lo na alocação de atenção à saúde "
            "da mulher em Rio Claro"
        )

    if pd.notna(row.get("taxa_mortalidade")) and row["taxa_mortalidade"] >= 10:
        partes.append(
            f"do ponto de vista da saúde da população, a taxa de "
            f"mortalidade de {row['taxa_mortalidade']:.1f}% indica "
            f"que uma parcela relevante das internações resulta em "
            f"óbito, reforçando a importância de diagnóstico e "
            f"tratamento precoces"
        )

    if pd.notna(row.get("ranking_custo")) and row["ranking_custo"] <= 2:
        partes.append(
            f"do ponto de vista financeiro, este é o "
            f"{int(row['ranking_custo'])}º câncer em custo hospitalar "
            f"total (R$ {row['valor_total']:,.2f}), representando "
            f"pressão relevante sobre o orçamento da saúde"
        )

    if pd.notna(row.get("permanencia_media")) and row["permanencia_media"] >= 7:
        partes.append(
            f"do ponto de vista da capacidade hospitalar, a "
            f"permanência média de {row['permanencia_media']:.1f} "
            f"dias indica maior ocupação de leitos por internação"
        )

    if not partes:
        partes.append(
            "no momento, este câncer não apresenta impacto que se "
            "destaque frente aos demais monitorados"
        )

    return "Em termos de impacto, " + "; ".join(partes) + "."


# =====================================
# CAMADA 3 — O QUE DEVE SER FEITO
#
# Ação sugerida, não decisão. A decisão
# final é sempre do gestor responsável.
# =====================================

def gerar_recomendacao(row):

    if row["nivel_prioridade"] == "CRITICA":
        base_rec = (
            "monitoramento prioritário e acompanhamento contínuo, "
            "com avaliação imediata das causas do desvio identificado"
        )

    elif row["nivel_prioridade"] == "ALTA":
        base_rec = (
            "acompanhamento frequente e inclusão entre as prioridades "
            "de curto prazo da gestão"
        )

    elif row["nivel_prioridade"] == "MEDIA":
        base_rec = "monitoramento regular, sem urgência imediata"

    else:
        base_rec = "acompanhamento de rotina"

    extra = []

    if row["situacao"] == "ANOMALIA_POSITIVA":
        extra.append(
            "investigar a causa do crescimento atípico em 2025 antes "
            "de decidir sobre alocação adicional de recursos"
        )

    if row["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL":
        extra.append(
            "comparar o comportamento local com campanhas ou mudanças "
            "regionais que possam explicar o descolamento em relação "
            "ao Estado"
        )

    recomendacao = "Recomenda-se " + base_rec + "."

    if extra:
        recomendacao += " Além disso, sugere-se " + " e ".join(extra) + "."

    recomendacao += (
        " Esta é uma sugestão de apoio à decisão; a definição final "
        "cabe ao gestor responsável, considerando orçamento e "
        "capacidade operacional."
    )

    return recomendacao


base["motivo"] = base.apply(gerar_motivo, axis=1)
base["impacto"] = base.apply(gerar_impacto, axis=1)
base["recomendacao"] = base.apply(gerar_recomendacao, axis=1)

base = base.sort_values("pontuacao_final", ascending=False)

# =====================================
# RESULTADO
# =====================================

print("\n=== BASE DE CONHECIMENTO ===\n")

for _, row in base.iterrows():

    print(f"\n--- {row['tipo_cancer']} ({row['nivel_prioridade']}) ---")
    print(row["motivo"])
    print(row["impacto"])
    print(row["recomendacao"])

# =====================================
# SALVAR
# =====================================

base.to_sql(
    "base_conhecimento",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela base_conhecimento atualizada com sucesso.")

conn.close()
