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

# ==================================================
# CONFIGURAÇÃO
# ==================================================

st.set_page_config(
    page_title="Escudo Feminino",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================================================
# IDENTIDADE VISUAL — NOVA INTERFACE
# ==================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #f8f7fb;
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif;
    color: #25243a;
    letter-spacing: -0.02em;
}

h1 {
    font-size: 2.5rem !important;
}

[data-testid="stSidebar"] {
    background: #f1eff8;
    border-right: 1px solid #e7e3f0;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #ebe8f2;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 4px 18px rgba(53, 45, 82, 0.05);
}

[data-testid="stMetricLabel"] {
    color: #706b82;
    font-weight: 500;
}

[data-testid="stMetricValue"] {
    color: #312b52;
}

div[data-baseweb="select"] > div {
    border-radius: 12px;
    border-color: #ddd8ea;
    background: #ffffff;
}

button[kind="primary"] {
    border-radius: 12px;
}

.escudo-hero {
    background: linear-gradient(135deg, #eee9fb 0%, #f7eef5 52%, #edf4f7 100%);
    border: 1px solid #e5dfef;
    border-radius: 28px;
    padding: 34px 38px;
    margin: 0 0 26px 0;
}

.escudo-eyebrow {
    color: #7565a8;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.escudo-hero-title {
    color: #292541;
    font-family: 'Manrope', sans-serif;
    font-size: 2.25rem;
    font-weight: 700;
    margin: 0;
}

.escudo-hero-text {
    color: #625d72;
    font-size: 1.02rem;
    margin-top: 10px;
    max-width: 760px;
}

.escudo-section {
    background: #ffffff;
    border: 1px solid #ebe8f2;
    border-radius: 22px;
    padding: 22px 24px;
    margin: 18px 0;
}

.escudo-option {
    background: #ffffff;
    border: 1px solid #e9e5f0;
    border-radius: 18px;
    padding: 20px;
    min-height: 105px;
    box-shadow: 0 3px 14px rgba(53, 45, 82, 0.035);
}

.escudo-option-title {
    color: #383251;
    font-weight: 700;
    font-size: 1rem;
}

.escudo-option-text {
    color: #777184;
    font-size: 0.88rem;
    margin-top: 5px;
}

div[data-testid="stTabs"] button {
    font-weight: 600;
}

hr {
    border-color: #e8e4ef;
}

[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


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

nome_escolhido = st.selectbox("Município", nomes_disponiveis)

municipio_escolhido = next(
    m for m in municipios_disponiveis if m["nome"] == nome_escolhido
)

ORIGEM = municipio_escolhido["origem"]
NOME_MUNICIPIO = municipio_escolhido["nome"]

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
    """,
    conexao
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
    WHERE municipio = ?
    """,
    conexao,
    params=(ORIGEM,)
).iloc[0]["media"] or 0

obitos = pd.read_sql(
    """
    SELECT SUM(obito) AS total
    FROM internacoes
    WHERE municipio = ?
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

st.subheader("Priorização e Recomendações")

base = None
erro_base = None

try:
    base = pd.read_sql(
        """
        SELECT *
        FROM base_conhecimento
        WHERE municipio = ?
        ORDER BY pontuacao_final DESC
        """,
        conexao,
        params=(ORIGEM,)
    )
except Exception as e:
    erro_base = e

if erro_base is not None:
    st.warning(
        f"Não foi possível carregar 'base_conhecimento': {erro_base}. "
        f"Rode algoritimos\\base_conhecimento.py antes de abrir o "
        f"dashboard."
    )
elif base.empty:
    st.info(
        f"{NOME_MUNICIPIO} ainda não foi processado pela cadeia "
        f"determinística. Rode os scripts em algoritimos\\*.py com "
        f"ESCUDO_MUNICIPIO={ORIGEM} (ou o código IBGE correspondente) "
        f"para gerar esta análise."
    )
else:
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

st.divider()

# ==================================================
# RELATÓRIO EXECUTIVO
#
# Mostra o mesmo relatorio_executivo.txt que o chat
# lê quando alguém pede um relatório — aqui, pronto
# pra ler ou baixar direto do painel.
# ==================================================

st.subheader("Relatório Executivo")

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

st.subheader("Ranking dos Cânceres")

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

st.subheader(f"{NOME_MUNICIPIO} x {UF_REFERENCIA}")

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
# COMPARAÇÃO DIRETA ENTRE MUNICÍPIOS
#
# Permite comparar o município selecionado com outro
# município que tenha dados reais carregados no banco.
# Não substitui a comparação com o Estado (SP).
# ==================================================

st.subheader("Comparar cidades")

municipios_comparacao = [
    m for m in municipios_disponiveis
    if m["origem"] != ORIGEM
]

if not municipios_comparacao:
    st.info("Não há outro município com dados carregados para comparação.")
else:
    origens_comparacao = [m["origem"] for m in municipios_comparacao]

    origem_padrao = (
        "SAO_JOSE_DO_RIO_PRETO"
        if ORIGEM == "RIO_CLARO"
        and "SAO_JOSE_DO_RIO_PRETO" in origens_comparacao
        else origens_comparacao[0]
    )

    indice_padrao = origens_comparacao.index(origem_padrao)

    municipio_comparado_nome = st.selectbox(
        "Comparar com",
        [m["nome"] for m in municipios_comparacao],
        index=indice_padrao,
        key="municipio_comparacao"
    )

    municipio_comparado = next(
        m for m in municipios_comparacao
        if m["nome"] == municipio_comparado_nome
    )

    ORIGEM_COMPARADA = municipio_comparado["origem"]

    indicadores_comparacao = pd.read_sql(
        """
        SELECT
            municipio,
            COUNT(*) AS internacoes,
            COALESCE(SUM(obito), 0) AS obitos,
            COALESCE(SUM(valor_total), 0) AS valor_total,
            COALESCE(AVG(dias_permanencia), 0) AS permanencia_media
        FROM internacoes
        WHERE municipio IN (?, ?)
        GROUP BY municipio
        """,
        conexao,
        params=(ORIGEM, ORIGEM_COMPARADA)
    )

    nomes_municipios = {
        ORIGEM: NOME_MUNICIPIO,
        ORIGEM_COMPARADA: municipio_comparado_nome
    }

    indicadores_comparacao["municipio"] = (
        indicadores_comparacao["municipio"].map(nomes_municipios)
    )

    indicadores_comparacao["taxa_obitos_%"] = (
        indicadores_comparacao["obitos"]
        / indicadores_comparacao["internacoes"].replace(0, pd.NA)
        * 100
    ).fillna(0)

    indicadores_comparacao = indicadores_comparacao.rename(columns={
        "municipio": "Município",
        "internacoes": "Internações",
        "obitos": "Óbitos",
        "taxa_obitos_%": "Óbitos / Internações (%)",
        "valor_total": "Valor Total (R$)",
        "permanencia_media": "Permanência Média (dias)"
    })

    st.dataframe(
        indicadores_comparacao[
            [
                "Município",
                "Internações",
                "Óbitos",
                "Óbitos / Internações (%)",
                "Valor Total (R$)",
                "Permanência Média (dias)"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    cancer_comparacao = pd.read_sql(
        """
        SELECT
            municipio,
            tipo_cancer,
            COUNT(*) AS total
        FROM internacoes
        WHERE municipio IN (?, ?)
        GROUP BY municipio, tipo_cancer
        ORDER BY tipo_cancer
        """,
        conexao,
        params=(ORIGEM, ORIGEM_COMPARADA)
    )

    cancer_comparacao["municipio"] = cancer_comparacao["municipio"].map(
        nomes_municipios
    )

    fig_municipios = px.bar(
        cancer_comparacao,
        x="tipo_cancer",
        y="total",
        color="municipio",
        barmode="group",
        title=f"Internações por tipo de câncer — {NOME_MUNICIPIO} x {municipio_comparado_nome}"
    )

    st.plotly_chart(
        fig_municipios,
        use_container_width=True
    )

st.divider()

# ==================================================
# EVOLUÇÃO TEMPORAL
# ==================================================

st.subheader("Evolução Temporal")

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

st.subheader("Alertas Analíticos")

eventos = pd.read_sql(
    """
    SELECT *
    FROM tendencia_estadual
    WHERE municipio = ?
    ORDER BY desvio DESC
    """,
    conexao,
    params=(ORIGEM,)
)

if eventos.empty:
    st.info(
        f"{NOME_MUNICIPIO} ainda não foi processado pela cadeia "
        f"determinística (tendencia_estadual). Rode "
        f"algoritimos\\tendencia_estadual.py com "
        f"ESCUDO_MUNICIPIO={ORIGEM} para gerar esta análise."
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
