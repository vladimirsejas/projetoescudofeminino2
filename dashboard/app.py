import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "algoritimos")
)

from configuracao_geografica import (
    listar_municipios_disponiveis,
    UF_REFERENCIA
)
from executar_cadeia import executar

# ==================================================
# CONFIGURAÇÃO
# ==================================================

st.set_page_config(
    page_title="Escudo Feminino",
    page_icon="🎗️",
    layout="wide"
)

# ==================================================
# BANCO
# ==================================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(BANCO)

# ==================================================
# SELEÇÃO DE MUNICÍPIO
#
# A lista vem do banco (municipios ∩ internacoes), nunca de uma
# lista fixa no código -- assim que outro município tiver dados
# carregados, ele aparece aqui automaticamente.
# ==================================================

municipios_disponiveis = listar_municipios_disponiveis()

if not municipios_disponiveis:
    st.error(
        "Nenhum município cadastrado em `municipios` com dados "
        "carregados em `internacoes`. Rode "
        "etl\\criar_tabela_municipios.py e confira o ETL antes de "
        "abrir o dashboard."
    )
    st.stop()

nomes_disponiveis = [m["nome"] for m in municipios_disponiveis]

nome_escolhido = st.sidebar.selectbox("Município", nomes_disponiveis)

municipio_escolhido = next(
    m for m in municipios_disponiveis if m["nome"] == nome_escolhido
)

ORIGEM = municipio_escolhido["origem"]
NOME_MUNICIPIO = municipio_escolhido["nome"]

if st.session_state.get("municipio_processado") != ORIGEM:
    conexao.close()
    with st.spinner(f"Calculando indicadores para {NOME_MUNICIPIO}..."):
        try:
            executar(ORIGEM)
            st.session_state["municipio_processado"] = ORIGEM
        except Exception as erro:
            st.error(f"Não foi possível calcular {NOME_MUNICIPIO}: {erro}")
            st.stop()
    conexao = sqlite3.connect(BANCO)

# ==================================================
# KPIs PRINCIPAIS
#
# Total de Registros continua sendo a soma geral (município +
# referência estadual), como visão de conjunto. As demais métricas
# nomeadas pelo município (Câncer Líder, custos, permanência,
# óbitos) são filtradas por origem -- sem isso, ficam diluídas pelo
# volume do Estado (o mesmo problema já corrigido nos indicadores
# em algoritimos/).
# ==================================================

total = pd.read_sql(
    """
    SELECT COUNT(*) AS total
    FROM internacoes
    WHERE origem = ?
    """,
    conexao,
    params=(UF_REFERENCIA,)
).iloc[0]["total"]

ranking = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        COUNT(*) AS total
    FROM internacoes
    WHERE municipio = ?
    GROUP BY tipo_cancer
    ORDER BY total DESC
    """,
    conexao,
    params=(ORIGEM,)
)

origens = pd.read_sql(
    """
    SELECT
        origem,
        COUNT(*) AS total
    FROM internacoes
    GROUP BY origem
    """,
    conexao
)

lider = ranking.iloc[0]["tipo_cancer"] if not ranking.empty else "—"

total_municipio = int(
    pd.read_sql(
        "SELECT COUNT(*) AS total FROM internacoes WHERE municipio = ?",
        conexao,
        params=(ORIGEM,)
    ).iloc[0]["total"]
)

sp_vals = origens.loc[
    origens["origem"] == UF_REFERENCIA,
    "total"
].values

sp = int(sp_vals[0]) if len(sp_vals) > 0 else 0

# ==================================================
# KPIs AVANÇADOS (filtrados pelo município selecionado)
# ==================================================

valor_total = pd.read_sql(
    """
    SELECT SUM(valor_total) AS valor
    FROM internacoes
    WHERE municipio = ?
    """,
    conexao,
    params=(ORIGEM,)
).iloc[0]["valor"] or 0

permanencia_media = pd.read_sql(
    """
    SELECT AVG(dias_permanencia) AS media
    FROM internacoes
    WHERE origem = ?
    """,
    conexao,
    params=(ORIGEM,)
).iloc[0]["media"] or 0

obitos = pd.read_sql(
    """
    SELECT SUM(obito) AS total
    FROM internacoes
    WHERE origem = ?
    """,
    conexao,
    params=(ORIGEM,)
).iloc[0]["total"] or 0

# ==================================================
# CABEÇALHO
# ==================================================

st.title("🎗️ Escudo Feminino")

st.markdown(f"""
### Sistema de Apoio à Decisão para Saúde Pública

**{NOME_MUNICIPIO} x Estado de {UF_REFERENCIA}**
""")

# ==================================================
# KPIs
# ==================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de Registros", f"{int(total):,}")
col2.metric(NOME_MUNICIPIO, f"{total_municipio:,}")
col3.metric(f"Estado ({UF_REFERENCIA})", f"{sp:,}")
col4.metric("Câncer Líder", lider)

st.divider()

col5, col6, col7 = st.columns(3)

col5.metric("Valor Total", f"R$ {valor_total:,.2f}")
col6.metric("Permanência Média", f"{permanencia_media:.1f} dias")
col7.metric("Óbitos", f"{int(obitos):,}")

st.divider()

# ==================================================
# PRIORIZAÇÃO E EXPLICAÇÃO
#
# Esta é a seção nova: traz pro dashboard o mesmo
# conhecimento (motivo, impacto, recomendação) que
# o chat_escudo.py já entrega — até agora o painel
# só mostrava gráficos, sem explicar "e daí".
# ==================================================

st.subheader("🎯 Priorização e Recomendações")

st.caption(
    f"Indicadores calculados automaticamente para {NOME_MUNICIPIO}. "
    "A comparação estadual usa o conjunto de dados do Estado de São Paulo."
)

try:
    base = pd.read_sql(
        """
        SELECT *
        FROM base_conhecimento
        ORDER BY pontuacao_final DESC
        """,
        conexao
    )

    cores_prioridade = {
        "CRITICA": "🔴",
        "ALTA": "🟠",
        "MEDIA": "🟡",
        "BAIXA": "🟢",
    }

    for _, row in base.iterrows():

        emoji = cores_prioridade.get(row["nivel_prioridade"], "⚪")

        titulo = (
            f"{emoji} {row['tipo_cancer']} — "
            f"{row['nivel_prioridade']} "
            f"(pontuação {row['pontuacao_final']:.2f})"
        )

        with st.expander(titulo):

            st.markdown("**Por que acontece:**")
            st.write(row["motivo"])

            st.markdown("**Impacto:**")
            st.write(row["impacto"])

            st.markdown("**Recomendação:**")
            st.write(row["recomendacao"])

            avisos = []

            if row.get("confiabilidade", "OK") != "OK":
                avisos.append(
                    f"Tendência estadual: {row['confiabilidade']}"
                )

            if row.get("confiabilidade_anomalia", "OK") not in (
                "OK", None
            ) and pd.notna(row.get("confiabilidade_anomalia")):
                avisos.append(
                    f"Anomalia: {row['confiabilidade_anomalia']}"
                )

            for aviso in avisos:
                st.warning(aviso)

except Exception as e:
    st.warning(
        f"Não foi possível carregar 'base_conhecimento': {e}. "
        f"Rode algoritimos\\base_conhecimento.py antes de abrir o "
        f"dashboard."
    )

st.divider()

# ==================================================
# RELATÓRIO EXECUTIVO
#
# Mostra o mesmo relatorio_executivo.txt que o chat
# lê quando alguém pede um relatório — aqui, pronto
# pra ler ou baixar direto do painel.
# ==================================================

st.subheader("📋 Relatório Executivo")

try:
    with open("relatorio_executivo.txt", "r", encoding="utf-8") as arquivo:
        texto_relatorio = arquivo.read()

    with st.expander("Ver relatório executivo completo"):
        st.text(texto_relatorio)

    st.download_button(
        label="Baixar relatório executivo (.txt)",
        data=texto_relatorio,
        file_name="relatorio_executivo.txt",
        mime="text/plain"
    )

except FileNotFoundError:
    st.info(
        "Relatório executivo ainda não foi gerado. Rode "
        "algoritimos\\relatorio_executivo.py na raiz do projeto."
    )

st.divider()

# ==================================================
# RANKING DOS CÂNCERES
# ==================================================

st.subheader("📊 Ranking dos Cânceres")

fig_ranking = px.bar(
    ranking,
    x="tipo_cancer",
    y="total",
    color="total",
    text="total",
    title="Ranking de Internações por Tipo de Câncer"
)

st.plotly_chart(
    fig_ranking,
    use_container_width=True
)

# ==================================================
# MUNICÍPIO X SP
# ==================================================

comparativo = pd.read_sql(
    """
    SELECT tipo_cancer, ? AS origem, COUNT(*) AS total
    FROM internacoes
    WHERE municipio = ?
    GROUP BY tipo_cancer

    UNION ALL

    SELECT tipo_cancer, ? AS origem, COUNT(*) AS total
    FROM internacoes
    WHERE origem = ?
    GROUP BY tipo_cancer

    ORDER BY tipo_cancer
    """,
    conexao,
    params=(NOME_MUNICIPIO, ORIGEM, UF_REFERENCIA, UF_REFERENCIA)
)

st.subheader(f"🏥 {NOME_MUNICIPIO} x {UF_REFERENCIA}")

fig_comparativo = px.bar(
    comparativo,
    x="tipo_cancer",
    y="total",
    color="origem",
    barmode="group"
)

st.plotly_chart(
    fig_comparativo,
    use_container_width=True
)

# ==================================================
# EVOLUÇÃO TEMPORAL
# ==================================================

st.subheader("📈 Evolução Temporal")

cancer_escolhido = st.selectbox(
    "Selecione o câncer",
    ranking["tipo_cancer"].tolist()
)

evolucao = pd.read_sql(
    """
    SELECT
        ano,
        COUNT(*) AS internacoes
    FROM internacoes
    WHERE tipo_cancer = ? AND municipio = ?
    GROUP BY ano
    ORDER BY ano
    """,
    conexao,
    params=(cancer_escolhido, ORIGEM)
)

fig_evolucao = px.line(
    evolucao,
    x="ano",
    y="internacoes",
    markers=True,
    title=f"Evolução Temporal - {cancer_escolhido} ({NOME_MUNICIPIO})"
)

st.plotly_chart(
    fig_evolucao,
    use_container_width=True
)

# ==================================================
# ALERTAS ANALÍTICOS
#
# Agora mostra também o selo de confiabilidade
# estatística quando o desvio vem de uma base
# pequena de casos.
# ==================================================

st.subheader("🚨 Alertas Analíticos")

st.caption(
    f"Tendência calculada para {NOME_MUNICIPIO} em comparação com "
    "o Estado de São Paulo."
)

eventos = pd.read_sql(
    """
    SELECT *
    FROM tendencia_estadual
    ORDER BY desvio DESC
    """,
    conexao
)

for _, row in eventos.iterrows():

    mensagem = (
        f"{row['tipo_cancer']} "
        f"({row['desvio']:.2f}%)"
    )

    if row.get("confiabilidade", "OK") != "OK":
        mensagem += f" — ⚠️ {row['confiabilidade']}"

    if row["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL":
        st.error(mensagem)

    elif row["evento"] == "ABAIXO_DA_TENDENCIA_ESTADUAL":
        st.success(mensagem)

    else:
        st.info(mensagem)

# ==================================================
# FECHAMENTO DA CONEXÃO
# ==================================================

conexao.close()
