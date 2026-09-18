import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

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
# KPIs PRINCIPAIS
# ==================================================

total = pd.read_sql(
    """
    SELECT COUNT(*) AS total
    FROM internacoes
    """,
    conexao
).iloc[0]["total"]

ranking = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        COUNT(*) AS total
    FROM internacoes
    GROUP BY tipo_cancer
    ORDER BY total DESC
    """,
    conexao
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

lider = ranking.iloc[0]["tipo_cancer"]

rio_claro_vals = origens.loc[
    origens["origem"] == "RIO_CLARO",
    "total"
].values

rio_claro = int(rio_claro_vals[0]) if len(rio_claro_vals) > 0 else 0

sp_vals = origens.loc[
    origens["origem"] == "SP",
    "total"
].values

sp = int(sp_vals[0]) if len(sp_vals) > 0 else 0

# ==================================================
# KPIs AVANÇADOS
# ==================================================

valor_total = pd.read_sql(
    """
    SELECT SUM(valor_total) AS valor
    FROM internacoes
    """,
    conexao
).iloc[0]["valor"] or 0

permanencia_media = pd.read_sql(
    """
    SELECT AVG(dias_permanencia) AS media
    FROM internacoes
    """,
    conexao
).iloc[0]["media"] or 0

obitos = pd.read_sql(
    """
    SELECT SUM(obito) AS total
    FROM internacoes
    """,
    conexao
).iloc[0]["total"] or 0

# ==================================================
# CABEÇALHO
# ==================================================

st.title("🎗️ Escudo Feminino")

st.markdown("""
### Sistema de Apoio à Decisão para Saúde Pública

**Rio Claro x Estado de São Paulo**
""")

# ==================================================
# KPIs
# ==================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de Registros", f"{int(total):,}")
col2.metric("Rio Claro", f"{rio_claro:,}")
col3.metric("São Paulo", f"{sp:,}")
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
# RIO CLARO X SP
# ==================================================

comparativo = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        origem,
        COUNT(*) AS total
    FROM internacoes
    GROUP BY tipo_cancer, origem
    ORDER BY tipo_cancer
    """,
    conexao
)

st.subheader("🏥 Rio Claro x São Paulo")

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
    WHERE tipo_cancer = ?
    GROUP BY ano
    ORDER BY ano
    """,
    conexao,
    params=(cancer_escolhido,)
)

fig_evolucao = px.line(
    evolucao,
    x="ano",
    y="internacoes",
    markers=True,
    title=f"Evolução Temporal - {cancer_escolhido}"
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
