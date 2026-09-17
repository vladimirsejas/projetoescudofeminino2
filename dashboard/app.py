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

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

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
### Monitoramento de Internações por Câncer Feminino

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

    if row["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL":
        st.error(mensagem)

    elif row["evento"] == "ABAIXO_DA_TENDENCIA_ESTADUAL":
        st.success(mensagem)

    else:
        st.info(mensagem)

# ==================================================
# PRIORIZAÇÃO EPIDEMIOLÓGICA
# ==================================================

st.subheader("🏆 Priorização Epidemiológica")

try:
    score_df = pd.read_sql(
        """
        SELECT *
        FROM indicadores_epidemiologicos
        """,
        conexao
    )

    # Tenta ordenar por uma coluna de score/pontuação, se existir
    coluna_score = None
    for candidato in ["score", "pontuacao", "score_epidemiologico", "indice"]:
        if candidato in score_df.columns:
            coluna_score = candidato
            break

    if coluna_score:
        score_df = score_df.sort_values(by=coluna_score, ascending=False)

    st.dataframe(score_df, use_container_width=True)

    # Só desenha o gráfico se houver uma coluna de score numérica
    # e uma coluna de câncer para usar no eixo X
    coluna_cancer = None
    for candidato in ["tipo_cancer", "cancer", "tipo"]:
        if candidato in score_df.columns:
            coluna_cancer = candidato
            break

    if coluna_score and coluna_cancer:
        fig_score = px.bar(
            score_df,
            x=coluna_cancer,
            y=coluna_score,
            color=coluna_score,
            text=coluna_score,
            title="Priorização Epidemiológica"
        )
        st.plotly_chart(
            fig_score,
            use_container_width=True
        )

except Exception as e:
    st.warning(
        f"Não foi possível carregar a tabela 'indicadores_epidemiologicos': {e}"
    )

# ==================================================
# FECHAMENTO DA CONEXÃO
# ==================================================

conexao.close()