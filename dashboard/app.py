import os
import sys
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "algoritimos"))

from configuracao_geografica import listar_municipios_disponiveis
from chat_servico import responder_pergunta


BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"


st.set_page_config(
    page_title="Escudo Feminino",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="collapsed",
)


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
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}
h1, h2, h3 {
    font-family: 'Manrope', sans-serif;
    color: #292541;
    letter-spacing: -0.02em;
}
[data-testid="stMetric"] {
    background: #fff;
    border: 1px solid #ebe8f2;
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 4px 18px rgba(53,45,82,.05);
}
[data-testid="stMetricLabel"] {
    color: #706b82;
}
[data-testid="stMetricValue"] {
    color: #312b52;
}
div[data-baseweb="select"] > div {
    border-radius: 12px;
    border-color: #ddd8ea;
    background: #fff;
}
.escudo-hero {
    background: linear-gradient(135deg, #eee9fb 0%, #f7eef5 52%, #edf4f7 100%);
    border: 1px solid #e5dfef;
    border-radius: 28px;
    padding: 30px 36px;
    margin-bottom: 22px;
}
.escudo-eyebrow {
    color: #7565a8;
    font-size: .8rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
}
.escudo-title {
    color: #292541;
    font-family: 'Manrope', sans-serif;
    font-size: 2.25rem;
    font-weight: 700;
    margin-top: 6px;
}
.escudo-text {
    color: #625d72;
    font-size: 1rem;
    max-width: 820px;
    margin-top: 8px;
}
.escudo-card {
    background: #fff;
    border: 1px solid #ebe8f2;
    border-radius: 18px;
    padding: 18px 20px;
    min-height: 92px;
}
.escudo-card-title {
    color: #383251;
    font-weight: 700;
}
.escudo-card-text {
    color: #777184;
    font-size: .88rem;
    margin-top: 4px;
}
div[data-testid="stTabs"] button {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def ler_sql(sql, params=()):
    conn = sqlite3.connect(BANCO)
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


@st.cache_data
def municipios():
    return listar_municipios_disponiveis()


municipios_disponiveis = municipios()

if not municipios_disponiveis:
    st.error("Nenhum município disponível no banco.")
    st.stop()

nomes_disponiveis = [m["nome"] for m in municipios_disponiveis]

st.markdown("""
<div class="escudo-hero">
    <div class="escudo-eyebrow">ESCUDO FEMININO</div>
    <div class="escudo-title">Plataforma de informações de saúde</div>
    <div class="escudo-text">
        Explore os dados por município e doença. Escolha o que deseja investigar.
        O Escudo organiza a informação para você.
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# ENTRADA PRINCIPAL
# ============================================================

col_local, col_doenca, col_ano = st.columns([1, 1, 1])

with col_local:
    nome_escolhido = st.selectbox(
        "Município",
        nomes_disponiveis,
        help="Digite o nome para localizar um município."
    )

municipio_escolhido = next(
    m for m in municipios_disponiveis if m["nome"] == nome_escolhido
)
ORIGEM = municipio_escolhido["origem"]
NOME_MUNICIPIO = municipio_escolhido["nome"]

doencas = ler_sql("""
    SELECT DISTINCT tipo_cancer
    FROM internacoes
    WHERE municipio = ? AND tipo_cancer IS NOT NULL
    ORDER BY tipo_cancer
""", (ORIGEM,))["tipo_cancer"].tolist()

opcoes_doenca = ["Todas as doenças"] + doencas

# Período de estudo do Escudo: 2013 a 2025.
# O ano permanece disponível mesmo quando não há registros no município.
anos_disponiveis = list(range(2025, 2012, -1))

with col_doenca:
    doenca_escolhida = st.selectbox(
        "Doença",
        opcoes_doenca,
        index=0,
        key="doenca_selecao"
    )

if doenca_escolhida == "Todas as doenças":
    doenca_escolhida = None

with col_ano:
    ano_escolhido = st.selectbox(
        "Ano", ["Todos os anos"] + anos_disponiveis,
        index=0, key="ano_selecao",
        help="Escolha o ano dos registros que deseja analisar."
    )
ano_filtro = None if ano_escolhido == "Todos os anos" else int(ano_escolhido)

# Mantém cada conversa ligada ao município selecionado.
if "chat_municipio_atual" not in st.session_state:
    st.session_state.chat_municipio_atual = ORIGEM
elif st.session_state.chat_municipio_atual != ORIGEM:
    st.session_state.pop("chat_escudo", None)
    st.session_state.chat_municipio_atual = ORIGEM


# ============================================================
# CHAT
# ============================================================

st.subheader("Pergunte ao Escudo")
st.caption(
    f"Você está explorando {NOME_MUNICIPIO}"
    + (f" · {doenca_escolhida}" if doenca_escolhida else "")
    + (f" · {ano_filtro}" if ano_filtro is not None else " · 2013–2025")
    + ". Pergunte sobre qualquer indicador disponível no Escudo."
)

if "chat_escudo" not in st.session_state:
    st.session_state.chat_escudo = [
        {
            "role": "assistant",
            "content": (
                "O que você quer descobrir? Você pode perguntar sobre evolução, "
                "internações, mortalidade, custos, permanência, faixa etária, "
                "tendência em relação a São Paulo, anomalias, prioridades, "
                "vulnerabilidade, simulações, comparações ou relatório. "
                "Você também pode combinar uma doença com qualquer indicador."
            ),
        }
    ]

for mensagem in st.session_state.chat_escudo:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

pergunta = st.chat_input(
    f"Pergunte sobre {NOME_MUNICIPIO}..."
)

if pergunta:
    st.session_state.chat_escudo.append(
        {"role": "user", "content": pergunta}
    )
    with st.chat_message("user"):
        st.markdown(pergunta)

    resposta, _ = responder_pergunta(
        pergunta,
        ORIGEM,
        doenca_escolhida,
        ano_filtro
    )

    st.session_state.chat_escudo.append(
        {"role": "assistant", "content": resposta}
    )
    with st.chat_message("assistant"):
        st.markdown(resposta)


st.divider()


# ============================================================
# INDICADORES RÁPIDOS
# ============================================================

filtro_doenca = ""
params = [ORIGEM]

if doenca_escolhida:
    filtro_doenca += " AND tipo_cancer = ? "
    params.append(doenca_escolhida)
if ano_filtro is not None:
    filtro_doenca += " AND ano = ? "
    params.append(ano_filtro)

kpis = ler_sql(f"""
    SELECT
        COUNT(*) AS internacoes,
        COALESCE(SUM(obito), 0) AS obitos,
        COALESCE(SUM(valor_total), 0) AS valor_total,
        COALESCE(AVG(dias_permanencia), 0) AS permanencia
    FROM internacoes
    WHERE municipio = ? {filtro_doenca}
""", tuple(params)).iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Internações", f"{int(kpis['internacoes']):,}")
k2.metric("Óbitos registrados", f"{int(kpis['obitos']):,}")
k3.metric(
    f"Valor hospitalar — {ano_filtro if ano_filtro is not None else '2013–2025'}",
    f"R$ {float(kpis['valor_total']):,.2f}"
)
k4.metric("Permanência média", f"{float(kpis['permanencia']):.1f} dias")


# ============================================================
# ÁREAS DE EXPLORAÇÃO
# ============================================================

tab_panorama, tab_evolucao, tab_analise, tab_comparar, tab_indicadores, tab_graficos = st.tabs([
    "Panorama",
    "Evolução",
    "Análise",
    "Comparar",
    "Indicadores",
    "Gráficos",
])


with tab_panorama:
    st.subheader(f"Panorama — {NOME_MUNICIPIO}")

    sql_ranking = """
        SELECT tipo_cancer, COUNT(*) AS total
        FROM internacoes WHERE municipio = ?
    """
    params_ranking = [ORIGEM]
    if ano_filtro is not None:
        sql_ranking += " AND ano = ?"
        params_ranking.append(ano_filtro)
    sql_ranking += " GROUP BY tipo_cancer ORDER BY total DESC"
    ranking = ler_sql(sql_ranking, tuple(params_ranking))

    if ranking.empty:
        if ano_filtro is not None:
            st.info(f"Não há registros disponíveis para {NOME_MUNICIPIO} no ano {ano_filtro}.")
        else:
            st.info("Não há dados de internações para este município.")
    else:
        a, b = st.columns([1.15, .85])

        with a:
            fig = px.bar(
                ranking,
                x="tipo_cancer",
                y="total",
                text="total",
                title="Volume de internações por doença"
            )
            st.plotly_chart(fig, use_container_width=True)

        with b:
            st.markdown("#### O que está disponível")
            st.markdown(
                "Evolução temporal, mortalidade, custos hospitalares, "
                "permanência, faixa etária, tendência estadual, "
                "anomalias, comparações e gráficos personalizados."
            )
            st.markdown("#### Sobre os registros")
            st.caption(
                "Os dados do SIH/SUS representam internações hospitalares "
                "(AIH). Eles não equivalem a casos novos ou incidência."
            )


with tab_evolucao:
    st.subheader(f"Evolução — {doenca_escolhida or 'todas as doenças'}")

    if doenca_escolhida:
        evolucao = ler_sql("""
            SELECT ano, COUNT(*) AS internacoes
            FROM internacoes
            WHERE municipio = ? AND tipo_cancer = ?
            GROUP BY ano
            ORDER BY ano
        """, (ORIGEM, doenca_escolhida))
    else:
        evolucao = ler_sql("""
            SELECT ano, COUNT(*) AS internacoes
            FROM internacoes
            WHERE municipio = ?
            GROUP BY ano
            ORDER BY ano
        """, (ORIGEM,))

    if evolucao.empty:
        st.info("Não há série temporal disponível para a seleção.")
    else:
        fig = px.line(
            evolucao,
            x="ano",
            y="internacoes",
            markers=True,
            title="Evolução das internações hospitalares"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "A série histórica mostra todos os anos disponíveis para a seleção. "
            + ("O ano escolhido acima é usado nos demais recortes; ele não reduz esta série a um único ponto."
               if ano_filtro is not None else
               "A série mostra internações hospitalares registradas no SIH/SUS.")
        )



with tab_analise:
    st.subheader("Análise")
    st.caption("Aqui o Escudo transforma os indicadores em análises: tendências, comparações, anomalias, prioridades e outros sinais relevantes.")

    st.markdown("### O que podemos analisar")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("**Tendências**")
        st.caption("Evolução das internações ao longo dos anos e comportamento temporal.")
        st.markdown("**Mortalidade**")
        st.caption("Óbitos registrados e indicadores de mortalidade disponíveis.")
        st.markdown("**Custos**")
        st.caption("Valores hospitalares associados aos registros de internação.")
    with a2:
        st.markdown("**Permanência**")
        st.caption("Tempo médio de permanência hospitalar e sua distribuição.")
        st.markdown("**Faixa etária**")
        st.caption("Concentração das internações e óbitos por faixa etária.")
        st.markdown("**Tendência estadual**")
        st.caption("Comportamento do município em relação à referência estadual.")
    with a3:
        st.markdown("**Anomalias**")
        st.caption("Situações identificadas pelo motor analítico como fora do padrão.")
        st.markdown("**Priorização**")
        st.caption("Situações priorizadas pelos critérios analíticos calculados.")
        st.markdown("**Vulnerabilidade**")
        st.caption("Faixas e situações de maior vulnerabilidade quando houver dados suficientes.")

    st.divider()
    st.markdown("### Análise da seleção")

    filtro_analise = ""
    params_analise = [ORIGEM]
    if doenca_escolhida:
        filtro_analise = " AND tipo_cancer = ? "
        params_analise.append(doenca_escolhida)
    if ano_filtro is not None:
        filtro_analise += " AND ano = ? "
        params_analise.append(ano_filtro)

    try:
        analise_base = ler_sql(
            """
            SELECT
                tipo_cancer,
                COUNT(*) AS internacoes,
                COALESCE(SUM(obito), 0) AS obitos,
                COALESCE(SUM(valor_total), 0) AS valor_total,
                COALESCE(AVG(dias_permanencia), 0) AS permanencia_media
            FROM internacoes
            WHERE municipio = ? """ + filtro_analise + """
            GROUP BY tipo_cancer
            ORDER BY internacoes DESC
            """,
            tuple(params_analise)
        )

        if analise_base.empty:
            st.info("Não há dados suficientes para realizar a análise.")
        else:
            total_internacoes = int(analise_base["internacoes"].sum())
            total_obitos = int(analise_base["obitos"].sum())
            total_valor = float(analise_base["valor_total"].sum())

            m1, m2, m3 = st.columns(3)
            m1.metric("Internações analisadas", f"{total_internacoes:,}")
            m2.metric("Óbitos registrados", f"{total_obitos:,}")
            m3.metric(
                f"Valor hospitalar — {ano_filtro if ano_filtro is not None else '2013–2025'}",
                f"R$ {total_valor:,.2f}"
            )

            if doenca_escolhida:
                linha = analise_base.iloc[0]
                st.markdown(
                    f"**{doenca_escolhida}:** "
                    f"{int(linha['internacoes']):,} internações registradas, "
                    f"{int(linha['obitos']):,} óbitos registrados e "
                    f"R$ {float(linha['valor_total']):,.2f} em valor hospitalar registrado "
                    f"no período selecionado."
                )
            else:
                st.markdown(
                    f"O conjunto selecionado reúne **{total_internacoes:,} internações "
                    f"hospitalares registradas** entre as doenças disponíveis para o município."
                )

            st.caption("Esta análise descreve os registros disponíveis. Internações hospitalares não equivalem diretamente a casos novos ou incidência.")
    except Exception as erro:
        st.info(f"Análise indisponível: {erro}")

    st.divider()
    st.markdown("### Análises calculadas pelo Escudo")

    for tabela, titulo, descricao in [
        ("tendencia_estadual", "Tendência em relação a São Paulo", "Compara indicadores municipais com a referência estadual disponível."),
        ("anomalias", "Anomalias", "Mostra situações identificadas pelo motor analítico como fora do padrão."),
        ("priorizacao_executiva", "Priorização", "Apresenta os resultados da priorização calculada pelo Escudo."),
        ("mortalidade", "Mortalidade", "Indicadores de mortalidade disponíveis para a seleção."),
        ("custos_hospitalares", "Valores hospitalares", "Valores hospitalares associados aos registros de internação no período disponível na tabela."),
        ("permanencia_hospitalar", "Permanência hospitalar", "Indicadores relacionados ao tempo de permanência."),

        ("vulnerabilidade", "Vulnerabilidade", "Indicadores de vulnerabilidade calculados pelo projeto."),
    ]:
        try:
            df = ler_sql(f"SELECT * FROM {tabela} WHERE municipio = ?", (ORIGEM,))
            if doenca_escolhida and "tipo_cancer" in df.columns:
                df = df[df["tipo_cancer"] == doenca_escolhida]
            if ano_filtro is not None and "ano" in df.columns:
                df = df[df["ano"] == ano_filtro]
            if not df.empty:
                with st.expander(titulo):
                    st.caption(descricao)
                    if ano_filtro is not None and "ano" not in df.columns:
                        st.caption(
                            f"Esta tabela analítica não possui dimensão anual própria; "
                            f"o valor anual do período selecionado é calculado diretamente "
                            f"dos registros de {ano_filtro} no painel."
                        )
                    st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception:
            pass

    st.divider()
    st.markdown("### Relatório analítico")
    try:
        base = ler_sql(
            "SELECT * FROM base_conhecimento WHERE municipio = ? ORDER BY pontuacao_final DESC",
            (ORIGEM,)
        )
        if doenca_escolhida and "tipo_cancer" in base.columns:
            base = base[base["tipo_cancer"] == doenca_escolhida]
        if base.empty:
            st.info("Não há relatório analítico calculado para essa seleção.")
        else:
            for _, row in base.iterrows():
                st.markdown(
                    f"**{row.get('tipo_cancer', '')} — {row.get('nivel_prioridade', '')}**"
                )
                st.write(row.get("motivo", ""))
                st.write(row.get("impacto", ""))
                st.write(row.get("recomendacao", ""))
                st.divider()
    except Exception as erro:
        st.info(f"Relatório analítico indisponível: {erro}")


with tab_comparar:
    st.subheader("Comparar municípios")

    outros = [m for m in municipios_disponiveis if m["origem"] != ORIGEM]

    if not outros:
        st.info("Não há outro município com dados carregados para comparação.")
    else:
        outro_nome = st.selectbox(
            "Escolha o município para comparar",
            [m["nome"] for m in outros],
            key="comparacao_municipio"
        )
        outro = next(m for m in outros if m["nome"] == outro_nome)

        sql_comparacao = """
            SELECT
                municipio,
                tipo_cancer,
                COUNT(*) AS internacoes,
                COALESCE(SUM(obito), 0) AS obitos,
                COALESCE(SUM(valor_total), 0) AS valor_total,
                COALESCE(AVG(dias_permanencia), 0) AS permanencia_media
            FROM internacoes
            WHERE municipio IN (?, ?)
        """
        params_comparacao = [ORIGEM, outro["origem"]]
        if ano_filtro is not None:
            sql_comparacao += " AND ano = ?"
            params_comparacao.append(ano_filtro)
        sql_comparacao += " GROUP BY municipio, tipo_cancer"

        dados = ler_sql(sql_comparacao, tuple(params_comparacao))

        nomes = {
            ORIGEM: NOME_MUNICIPIO,
            outro["origem"]: outro_nome
        }
        dados["municipio"] = dados["municipio"].map(nomes)

        if doenca_escolhida:
            dados = dados[dados["tipo_cancer"] == doenca_escolhida]

        if dados.empty:
            if ano_filtro is not None:
                st.info(f"Não há registros suficientes para comparar os municípios no ano {ano_filtro}.")
            else:
                st.info("Não há dados suficientes para essa comparação.")
        else:
            fig = px.bar(
                dados,
                x="tipo_cancer",
                y="internacoes",
                color="municipio",
                barmode="group",
                title=f"Internações — {NOME_MUNICIPIO} x {outro_nome}"
            )
            st.plotly_chart(fig, use_container_width=True)


with tab_indicadores:
    st.subheader("Indicadores")
    st.caption(
        f"Os valores abaixo correspondem ao ano {ano_filtro}."
        if ano_filtro is not None
        else "Os valores abaixo correspondem ao período de 2013 a 2025."
    )

    sql_indicadores = """
        SELECT
            tipo_cancer,
            COUNT(*) AS internacoes,
            COALESCE(SUM(obito), 0) AS obitos,
            COALESCE(SUM(valor_total), 0) AS valor_total,
            COALESCE(AVG(dias_permanencia), 0) AS permanencia_media
        FROM internacoes
        WHERE municipio = ?
    """
    params_indicadores = [ORIGEM]
    if ano_filtro is not None:
        sql_indicadores += " AND ano = ?"
        params_indicadores.append(ano_filtro)
    sql_indicadores += " GROUP BY tipo_cancer ORDER BY internacoes DESC"

    dados_ind = ler_sql(sql_indicadores, tuple(params_indicadores))

    if doenca_escolhida:
        dados_ind = dados_ind[dados_ind["tipo_cancer"] == doenca_escolhida]

    st.dataframe(
        dados_ind,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### Indicadores analíticos já calculados pelo Escudo")

    for tabela, titulo in [
        ("priorizacao_executiva", "Priorização"),
        ("mortalidade", "Mortalidade"),
        ("custos_hospitalares", "Valores hospitalares"),
        ("permanencia_hospitalar", "Permanência hospitalar"),
        ("tendencia_estadual", "Tendência estadual"),
        ("anomalias", "Anomalias"),
    ]:
        try:
            df = ler_sql(
                f"SELECT * FROM {tabela} WHERE municipio = ?",
                (ORIGEM,)
            )
            if doenca_escolhida and "tipo_cancer" in df.columns:
                df = df[df["tipo_cancer"] == doenca_escolhida]
            if ano_filtro is not None and "ano" in df.columns:
                df = df[df["ano"] == ano_filtro]
            if not df.empty:
                with st.expander(titulo):
                    st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception:
            pass


with tab_graficos:
    st.subheader("Monte seu gráfico")
    st.caption("Escolha o que quer visualizar. O gráfico é construído a partir dos dados do Escudo.")

    c1, c2, c3 = st.columns(3)

    with c1:
        dimensao = st.selectbox(
            "Eixo",
            ["Ano", "Doença"],
            key="grafico_dimensao"
        )

    with c2:
        medida = st.selectbox(
            "Indicador",
            ["Internações", "Óbitos", "Valor hospitalar", "Permanência média"],
            key="grafico_medida"
        )

    with c3:
        tipo_grafico = st.selectbox(
            "Tipo de gráfico",
            ["Linha", "Barras", "Área"],
            key="grafico_tipo"
        )

    sql = """
        SELECT ano, tipo_cancer, municipio,
               obito, valor_total, dias_permanencia
        FROM internacoes
        WHERE municipio = ?
    """
    dados_graf = ler_sql(sql, (ORIGEM,))
    if ano_filtro is not None:
        dados_graf = dados_graf[dados_graf["ano"] == ano_filtro]

    if doenca_escolhida:
        dados_graf = dados_graf[dados_graf["tipo_cancer"] == doenca_escolhida]

    if dados_graf.empty:
        if ano_filtro is not None:
            st.info(f"Não há registros disponíveis para {NOME_MUNICIPIO} no ano {ano_filtro}.")
        else:
            st.info("Não há dados suficientes para montar esse gráfico.")
    else:
        medida_map = {
            "Internações": ("internacoes", "count"),
            "Óbitos": ("obitos", "sum"),
            "Valor hospitalar": ("valor_hospitalar", "sum"),
            "Permanência média": ("permanencia_media", "mean"),
        }

        coluna_resultado, agregacao = medida_map[medida]

        if dimensao == "Ano":
            eixo = "ano"
            agrupado = dados_graf.groupby("ano", as_index=False)
        elif dimensao == "Doença":
            eixo = "tipo_cancer"
            agrupado = dados_graf.groupby("tipo_cancer", as_index=False)
        else:
            eixo = "municipio"
            agrupado = dados_graf.groupby("municipio", as_index=False)

        if medida == "Internações":
            grafico = agrupado.size().rename(columns={"size": coluna_resultado})
        elif medida == "Óbitos":
            grafico = agrupado["obito"].sum().rename(columns={"obito": coluna_resultado})
        elif medida == "Valor hospitalar":
            grafico = agrupado["valor_total"].sum().rename(columns={"valor_total": coluna_resultado})
        else:
            grafico = agrupado["dias_permanencia"].mean().rename(columns={"dias_permanencia": coluna_resultado})

        if tipo_grafico == "Linha":
            fig = px.line(grafico, x=eixo, y=coluna_resultado, markers=True)
        elif tipo_grafico == "Área":
            fig = px.area(grafico, x=eixo, y=coluna_resultado)
        else:
            fig = px.bar(grafico, x=eixo, y=coluna_resultado, text=coluna_resultado)

        st.plotly_chart(fig, use_container_width=True)



# A área de Análise concentra as análises e o relatório analítico.


st.caption(
    "Escudo Feminino · dados públicos de saúde · "
    "internações hospitalares do SIH/SUS não equivalem a casos novos."
)
