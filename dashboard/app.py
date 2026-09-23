import os
import sys
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "algoritimos"))

from configuracao_geografica import listar_municipios_disponiveis, UF_REFERENCIA
from chat_servico import responder_pergunta
from predicao_orcamento import (
    PESOS_PADRAO,
    NOMES_CRITERIOS,
    calcular_prioridades,
    carregar_serie_banco,
    distribuir_orcamento,
    formatar_numero,
    projetar,
    validar,
)


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


@st.cache_data
def serie_anual(origem):
    conn = sqlite3.connect(BANCO)
    try:
        return carregar_serie_banco(conn, origem, UF_REFERENCIA)
    finally:
        conn.close()


# ============================================================
# ESTILO ÚNICO DOS GRÁFICOS
#
# Todo gráfico passa por estilizar(): mesma fonte, grade discreta,
# sem barra de ferramentas do Plotly e cores fixas por papel (uma
# cor para "dado", cinza para "contexto"). Paleta validada para
# daltonismo; como três cores ficam abaixo de 3:1 de contraste, todo
# gráfico tem os números também em tabela ("Ver números").
# ============================================================

COR_PRINCIPAL = "#2a78d6"
COR_CONTEXTO = "#b9b7c4"
COR_TEXTO = "#292541"
COR_TEXTO_SUAVE = "#706b82"
COR_GRADE = "#ebe8f2"
PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
CONFIG_GRAFICO = {"displayModeBar": False, "locale": "pt-BR"}


def estilizar(fig, titulo=None, subtitulo=None, altura=380):
    if titulo:
        texto = f"<b>{titulo}</b>"
        if subtitulo:
            texto += f"<br><span style='font-size:13px;color:{COR_TEXTO_SUAVE}'>{subtitulo}</span>"
        fig.update_layout(title={"text": texto, "x": 0, "xanchor": "left"})
    fig.update_layout(
        height=altura,
        font={"family": "DM Sans, sans-serif", "size": 13, "color": COR_TEXTO},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin={"l": 10, "r": 20, "t": 80 if titulo else 20, "b": 40},
        # legenda embaixo do gráfico: em cima ela disputava espaço com o subtítulo
        legend={"orientation": "h", "yanchor": "top", "y": -0.12, "x": 0, "title": None},
        hoverlabel={"bgcolor": "#ffffff", "font_color": COR_TEXTO, "bordercolor": COR_GRADE},
        separators=",.",
        bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, linecolor=COR_GRADE, title=None, automargin=True,
                     tickfont={"color": COR_TEXTO_SUAVE})
    fig.update_yaxes(gridcolor=COR_GRADE, zeroline=False, title=None, automargin=True,
                     tickfont={"color": COR_TEXTO_SUAVE})
    fig.update_traces(selector={"type": "bar"}, marker_line_width=0)
    return fig


def mostrar(fig):
    st.plotly_chart(fig, use_container_width=True, theme=None, config=CONFIG_GRAFICO)


def reais(valor, casas=0):
    return "R$ " + formatar_numero(valor, casas)


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
k1.metric("Internações", formatar_numero(kpis["internacoes"], 0))
k2.metric("Óbitos registrados", formatar_numero(kpis["obitos"], 0))
valor_kpi = float(kpis["valor_total"])
k3.metric(
    f"Valor hospitalar — {ano_filtro if ano_filtro is not None else '2013–2025'}",
    f"R$ {formatar_numero(valor_kpi / 1e6, 2)} mi" if valor_kpi >= 1e6 else reais(valor_kpi),
    help=f"Valor exato: {reais(valor_kpi, 2)}",
)
k4.metric("Permanência média", f"{formatar_numero(kpis['permanencia'])} dias")


# ============================================================
# ÁREAS DE EXPLORAÇÃO
# ============================================================

tab_investir, tab_panorama, tab_evolucao, tab_analise, tab_comparar, tab_indicadores, tab_graficos = st.tabs([
    "Onde investir",
    "Panorama",
    "Evolução",
    "Análise",
    "Comparar",
    "Indicadores",
    "Gráficos",
])


# ============================================================
# ONDE INVESTIR — predição + sugestão de orçamento
#
# Pedido da Secretaria da Mulher: a predição tem que indicar onde
# colocar o orçamento, não só como cada doença vai evoluir. Toda a
# conta está em algoritimos/predicao_orcamento.py; aqui só mostra.
# Compara sempre todas as doenças entre si (orçamento é repartido
# entre elas), por isso não usa o filtro de doença nem de ano.
# ============================================================

with tab_investir:
    serie = serie_anual(ORIGEM)

    if serie.empty or serie[serie["grupo"] == "MUNICIPIO"]["ano"].nunique() < 5:
        st.info(
            f"{NOME_MUNICIPIO} ainda não tem série histórica suficiente "
            "(mínimo de 5 anos) para projetar e sugerir orçamento."
        )
    else:
        with st.expander("Ajustar o que pesa mais na decisão", expanded=False):
            st.caption(
                "Os pesos abaixo definem a sugestão. O padrão equilibra volume, "
                "crescimento, gravidade, custo e o quanto dá para prevenir. "
                "Mude conforme a prioridade política da gestão — a sugestão se "
                "recalcula na hora."
            )
            colunas_peso = st.columns(3)
            pesos = {}
            for i, (chave, padrao) in enumerate(PESOS_PADRAO.items()):
                with colunas_peso[i % 3]:
                    pesos[chave] = st.slider(
                        NOMES_CRITERIOS[chave], 0, 100, int(padrao * 100), 5,
                        key=f"peso_{chave}"
                    ) / 100

        prioridades = calcular_prioridades(serie, pesos)
        projecao = projetar(serie)
        ultimo_ano = int(serie["ano"].max())
        anos_proj = f"{ultimo_ano + 1}–{ultimo_ano + 3}"

        top3 = prioridades.head(3)
        pct_top3 = top3["pct_orcamento"].sum()
        nomes_top = top3["tipo_cancer"].tolist()
        lista_top = nomes_top[0] if len(nomes_top) == 1 else ", ".join(nomes_top[:-1]) + " e " + nomes_top[-1]
        # o texto descreve o que as prioridades têm de fato em comum
        # (muda se a gestora mexer nos pesos), nunca uma frase fixa
        tracos = []
        if (top3["crescimento_anual_pct"] > 1).all():
            tracos.append("crescem ano a ano")
        if (top3["nota_prevencao"] >= 0.8).all():
            tracos.append("têm prevenção ou rastreamento que o município pode executar")
        if top3["internacoes_previstas"].sum() >= prioridades["internacoes_previstas"].sum() / 2:
            tracos.append("concentram a maior parte das internações previstas")
        porque = ("Elas " + ", ".join(tracos) + ". ") if tracos else ""
        st.markdown(
            f"""
<div class="escudo-card" style="margin-bottom:18px">
  <div class="escudo-eyebrow">Recomendação para {NOME_MUNICIPIO} · {anos_proj}</div>
  <div class="escudo-title" style="font-size:1.6rem">
    Concentrar {formatar_numero(pct_top3, 0)}% do orçamento em {lista_top}
  </div>
  <div class="escudo-text">
    {porque}Baseado nas internações do SIH/SUS de {serie["ano"].min()} a {ultimo_ano}
    e nos pesos escolhidos acima.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        col_valor, col_vazia = st.columns([1, 2])
        with col_valor:
            orcamento = st.number_input(
                "Orçamento disponível para câncer feminino (R$)",
                min_value=0.0, value=1_000_000.0, step=50_000.0, format="%.0f",
                help="Digite o valor e veja quanto iria para cada doença."
            )

        distribuicao = distribuir_orcamento(prioridades, orcamento)
        distribuicao = distribuicao.sort_values("pct_orcamento")
        distribuicao["rotulo"] = distribuicao.apply(
            lambda r: f"{formatar_numero(r['pct_orcamento'], 0)}% · {reais(r['valor_sugerido'])}",
            axis=1,
        )
        cores = [COR_PRINCIPAL if c in set(top3["tipo_cancer"]) else COR_CONTEXTO
                 for c in distribuicao["tipo_cancer"]]
        fig = px.bar(
            distribuicao, x="pct_orcamento", y="tipo_cancer", orientation="h",
            text="rotulo", custom_data=["acao_sugerida"],
        )
        fig.update_traces(
            marker_color=cores, textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:.1f}% do orçamento<br>%{customdata[0]}<extra></extra>",
        )
        fig.update_xaxes(visible=False, range=[0, distribuicao["pct_orcamento"].max() * 1.45])
        fig.update_yaxes(showgrid=False)
        mostrar(estilizar(
            fig,
            "Quanto do orçamento para cada doença",
            f"Sugestão sobre {reais(orcamento)} · em azul, as três prioridades",
            altura=360,
        ))

        st.markdown("#### O que fazer com o recurso em cada doença")
        for _, linha in prioridades.iterrows():
            with st.container(border=True):
                a, b = st.columns([1, 3])
                a.metric(
                    linha["tipo_cancer"],
                    f"{formatar_numero(linha['pct_orcamento'], 0)}%",
                    help="Parcela sugerida do orçamento",
                )
                b.markdown(f"**{linha['acao_sugerida']}**")
                b.caption(
                    linha["justificativa"]
                    + f" Previsão para {anos_proj}: {formatar_numero(linha['internacoes_previstas'], 0)} "
                    f"internações (provável entre {formatar_numero(linha['internacoes_previstas_min'], 0)} "
                    f"e {formatar_numero(linha['internacoes_previstas_max'], 0)})."
                )

        # --- Por que essa ordem: contribuição de cada critério ---
        partes = prioridades.melt(
            id_vars="tipo_cancer",
            value_vars=[f"pontos_{k}" for k in PESOS_PADRAO],
            var_name="criterio", value_name="pontos",
        )
        partes["criterio"] = partes["criterio"].str.replace("pontos_", "").map(NOMES_CRITERIOS)
        ordem = prioridades.sort_values("indice")["tipo_cancer"].tolist()
        fig = px.bar(
            partes, x="pontos", y="tipo_cancer", color="criterio", orientation="h",
            category_orders={"tipo_cancer": ordem, "criterio": list(NOMES_CRITERIOS.values())},
            color_discrete_sequence=PALETA,
        )
        fig.update_traces(
            marker_line_color="#ffffff", marker_line_width=2,
            hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:.1f} pontos<extra></extra>",
        )
        fig.update_layout(barmode="stack")
        fig.update_xaxes(showgrid=True, gridcolor=COR_GRADE)
        fig.update_yaxes(showgrid=False)
        mostrar(estilizar(
            fig,
            "Por que essa ordem",
            "Pontos de prioridade (0 a 100) e de onde cada ponto vem",
            altura=420,
        ))

        # --- Predição: histórico + projeção com faixa provável ---
        st.markdown("#### Como cada doença deve evoluir")
        doenca_proj = st.selectbox(
            "Doença", prioridades["tipo_cancer"].tolist(),
            index=(prioridades["tipo_cancer"].tolist().index(doenca_escolhida)
                   if doenca_escolhida in prioridades["tipo_cancer"].tolist() else 0),
            key="doenca_projecao",
        )
        dados_proj = projecao[(projecao["tipo_cancer"] == doenca_proj)
                              & (projecao["grupo"] == "MUNICIPIO")]
        hist = dados_proj[dados_proj["tipo"] == "historico"]
        fut = dados_proj[dados_proj["tipo"] == "projecao"]
        ponte = hist.tail(1)  # liga a linha do histórico à da projeção

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(fut["ano"]) + list(fut["ano"])[::-1],
            y=list(fut["internacoes_max"]) + list(fut["internacoes_min"])[::-1],
            mode="lines", fill="toself", fillcolor="rgba(42,120,214,0.14)", line={"width": 0},
            hoverinfo="skip", name="Faixa provável (90%)",
        ))
        fig.add_trace(go.Scatter(
            x=hist["ano"], y=hist["internacoes"], mode="lines+markers",
            line={"color": COR_PRINCIPAL, "width": 2}, marker={"size": 8},
            name="Registrado", hovertemplate="%{x}: %{y:.0f} internações<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=list(ponte["ano"]) + list(fut["ano"]),
            y=list(ponte["internacoes"]) + list(fut["internacoes"]),
            mode="lines+markers", line={"color": COR_PRINCIPAL, "width": 2, "dash": "dot"},
            marker={"size": 8, "symbol": "circle-open"},
            name="Previsto", hovertemplate="%{x}: %{y:.0f} previstas<extra></extra>",
        ))
        linha_p = prioridades[prioridades["tipo_cancer"] == doenca_proj].iloc[0]
        tendencia = "sobem" if linha_p["crescimento_anual_pct"] > 1 else (
            "caem" if linha_p["crescimento_anual_pct"] < -1 else "ficam estáveis")
        fig.update_xaxes(dtick=1)
        mostrar(estilizar(
            fig,
            f"{doenca_proj}: internações {tendencia} "
            f"({formatar_numero(linha_p['crescimento_anual_pct'])}% ao ano)",
            f"No Estado de SP a mesma doença varia {formatar_numero(linha_p['crescimento_anual_sp_pct'])}% ao ano",
        ))
        if linha_p["ultimo_ano_atipico"]:
            st.caption(
                f"Atenção: {ultimo_ano} ficou bem acima da tendência dos anos anteriores"
                + (" — e o Estado de SP inteiro também saltou nesse ano, o que sugere efeito de "
                   "registro/faturamento das AIHs, não só aumento real de casos"
                   if linha_p["ultimo_ano_atipico_sp"] else "")
                + ". Por isso a previsão segue a tendência de longo prazo e não parte do valor de "
                f"{ultimo_ano}. Se {ultimo_ano} se confirmar como novo patamar, a faixa de cima é a mais provável."
            )

        with st.expander("Ver números"):
            st.dataframe(
                prioridades[[
                    "tipo_cancer", "pct_orcamento", "indice", "internacoes_ultimo_ano",
                    "internacoes_previstas", "internacoes_previstas_min", "internacoes_previstas_max",
                    "custo_previsto", "crescimento_anual_pct", "crescimento_anual_sp_pct",
                    "letalidade_pct", "letalidade_sp_pct",
                ]].rename(columns={
                    "tipo_cancer": "Doença", "pct_orcamento": "% do orçamento",
                    "indice": "Pontos de prioridade",
                    "internacoes_ultimo_ano": f"Internações {ultimo_ano}",
                    "internacoes_previstas": f"Previstas {anos_proj}",
                    "internacoes_previstas_min": "Previstas (mínimo provável)",
                    "internacoes_previstas_max": "Previstas (máximo provável)",
                    "custo_previsto": f"Custo hospitalar previsto {anos_proj} (R$)",
                    "crescimento_anual_pct": "Crescimento ao ano (%)",
                    "crescimento_anual_sp_pct": "Crescimento no Estado (%)",
                    "letalidade_pct": "Letalidade (%)",
                    "letalidade_sp_pct": "Letalidade no Estado (%)",
                }).round(1),
                use_container_width=True, hide_index=True,
            )

        with st.expander("Como a previsão é feita e quanto ela acerta"):
            validacao = validar(serie)
            melhor = validacao[validacao["erro_medio_tendencia"] <= validacao["erro_medio_ingenuo"]]
            st.markdown(
                f"""
**Previsão.** Para cada doença, uma linha de tendência é ajustada sobre todos os anos
de {serie["ano"].min()} a {ultimo_ano} e prolongada por 3 anos. A faixa sombreada mostra
onde o número real deve cair em 9 de cada 10 cenários — com poucas internações por ano,
a faixa é larga, e isso é informação, não defeito.

**Teste de acerto.** O mesmo método foi treinado só até {ultimo_ano - 3} e usado para
"prever" {ultimo_ano - 2}–{ultimo_ano}, anos que já conhecemos. Ele errou menos que
simplesmente repetir a média dos últimos anos em **{len(melhor)} de {len(validacao)}
doenças** ({", ".join(melhor["tipo_cancer"]) or "nenhuma"}).

**Prioridade.** Cada doença recebe de 0 a 100 pontos somando seis critérios com os pesos
ajustáveis acima: internações previstas, ritmo de crescimento, crescimento acima do
Estado, letalidade hospitalar (estabilizada com a taxa estadual quando há poucos casos),
custo hospitalar previsto e potencial de prevenção (diretrizes do INCA). A parcela do
orçamento é proporcional aos pontos.

**Limites.** Os dados são internações do SUS (AIH): não contam casos novos, atendimentos
ambulatoriais (quimioterapia, radioterapia) nem quem usa só plano privado. O custo é o
valor pago pela AIH. A sugestão é um ponto de partida para a decisão da gestão, não uma
regra.
"""
            )
            st.dataframe(
                validacao.rename(columns={
                    "tipo_cancer": "Doença",
                    "erro_medio_tendencia": "Erro médio da tendência (internações/ano)",
                    "erro_medio_ingenuo": "Erro médio de repetir a média",
                    "anos_dentro_intervalo": "Anos dentro da faixa provável",
                    "anos_testados": "Anos testados",
                }).round(1),
                use_container_width=True, hide_index=True,
            )


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
            ranking = ranking.sort_values("total")
            fig = px.bar(ranking, x="total", y="tipo_cancer", orientation="h", text="total")
            fig.update_traces(
                # ordem crescente: a última barra (a maior) fica em destaque
                marker_color=[COR_CONTEXTO] * (len(ranking) - 1) + [COR_PRINCIPAL],
                textposition="outside", cliponaxis=False,
                hovertemplate="%{y}: %{x} internações<extra></extra>",
            )
            fig.update_xaxes(visible=False)
            fig.update_yaxes(showgrid=False)
            lider = ranking.iloc[-1]
            mostrar(estilizar(
                fig,
                f"{lider['tipo_cancer']} lidera as internações",
                f"{int(lider['total']):,} de {int(ranking['total'].sum()):,} internações".replace(",", ".")
                + (f" em {ano_filtro}" if ano_filtro is not None else " em 2013–2025"),
            ))

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
        fig = px.line(evolucao, x="ano", y="internacoes", markers=True)
        fig.update_traces(
            line={"color": COR_PRINCIPAL, "width": 2}, marker={"size": 8},
            hovertemplate="%{x}: %{y} internações<extra></extra>",
        )
        fig.update_xaxes(dtick=1)
        primeiro, ultimo = evolucao.iloc[0], evolucao.iloc[-1]
        variacao = (ultimo["internacoes"] / primeiro["internacoes"] - 1) * 100 if primeiro["internacoes"] else 0
        mostrar(estilizar(
            fig,
            f"Internações {'subiram' if variacao > 0 else 'caíram'} "
            f"{formatar_numero(abs(variacao), 0)}% de {int(primeiro['ano'])} a {int(ultimo['ano'])}",
            f"{int(primeiro['internacoes'])} → {int(ultimo['internacoes'])} internações por ano · "
            "a previsão dos próximos anos está na aba Onde investir",
        ))
        st.caption(
            "A série histórica mostra todos os anos disponíveis para a seleção. "
            + ("O ano escolhido acima é usado nos demais recortes; ele não reduz esta série a um único ponto."
               if ano_filtro is not None else
               "A série mostra internações hospitalares registradas no SIH/SUS.")
        )



with tab_analise:
    st.subheader("Análise")
    st.caption("Aqui o Escudo transforma os indicadores em análises: tendências, comparações, anomalias, prioridades e outros sinais relevantes.")

    st.markdown("### Acesse uma análise")
    st.caption("Clique em uma opção para abrir a análise correspondente aos filtros escolhidos.")

    filtro_analise = ""
    params_analise = [ORIGEM]
    if doenca_escolhida:
        filtro_analise += " AND tipo_cancer = ? "
        params_analise.append(doenca_escolhida)
    if ano_filtro is not None:
        filtro_analise += " AND ano = ? "
        params_analise.append(ano_filtro)

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

    with st.expander("Tendências", expanded=False):
        st.markdown("**Evolução das internações ao longo dos anos**")
        if doenca_escolhida:
            df_tend = ler_sql("""
                SELECT ano, COUNT(*) AS internacoes
                FROM internacoes
                WHERE municipio = ? AND tipo_cancer = ?
                GROUP BY ano
                ORDER BY ano
            """, (ORIGEM, doenca_escolhida))
        else:
            df_tend = ler_sql("""
                SELECT ano, COUNT(*) AS internacoes
                FROM internacoes
                WHERE municipio = ?
                GROUP BY ano
                ORDER BY ano
            """, (ORIGEM,))
        if df_tend.empty:
            st.info("Não há série temporal disponível.")
        else:
            fig = px.line(df_tend, x="ano", y="internacoes", markers=True)
            fig.update_traces(line={"color": COR_PRINCIPAL, "width": 2}, marker={"size": 8},
                              hovertemplate="%{x}: %{y} internações<extra></extra>")
            fig.update_xaxes(dtick=1)
            mostrar(estilizar(fig, altura=300))

    with st.expander("Mortalidade", expanded=False):
        df_mort = ler_sql("""
            SELECT tipo_cancer, COUNT(*) AS internacoes,
                   COALESCE(SUM(obito), 0) AS obitos
            FROM internacoes
            WHERE municipio = ?
        """ + filtro_analise + """
            GROUP BY tipo_cancer
        """, tuple(params_analise))
        if not df_mort.empty:
            df_mort["taxa_mortalidade"] = (
                df_mort["obitos"] / df_mort["internacoes"] * 100
            ).round(1)
            df_mort = df_mort.sort_values("taxa_mortalidade", ascending=False)
        st.dataframe(df_mort, use_container_width=True, hide_index=True)

    with st.expander("Custos", expanded=False):
        df_custos = ler_sql("""
            SELECT tipo_cancer,
                   COUNT(*) AS internacoes,
                   COALESCE(SUM(valor_total), 0) AS valor_total,
                   COALESCE(AVG(valor_total), 0) AS valor_medio
            FROM internacoes
            WHERE municipio = ?
        """ + filtro_analise + """
            GROUP BY tipo_cancer
            ORDER BY valor_total DESC
        """, tuple(params_analise))
        st.dataframe(df_custos, use_container_width=True, hide_index=True)

    with st.expander("Permanência", expanded=False):
        df_perm = ler_sql("""
            SELECT tipo_cancer,
                   COUNT(*) AS internacoes,
                   COALESCE(AVG(dias_permanencia), 0) AS permanencia_media
            FROM internacoes
            WHERE municipio = ?
        """ + filtro_analise + """
            GROUP BY tipo_cancer
            ORDER BY permanencia_media DESC
        """, tuple(params_analise))
        st.dataframe(df_perm, use_container_width=True, hide_index=True)


    with st.expander("Faixa etária", expanded=False):
        st.markdown("**Distribuição das internações por faixa etária**")
        st.caption(
            "Esta análise utiliza a tabela consolidada de faixa etária disponível no banco. "
            + (
                f"O banco não possui uma dimensão anual própria para esta tabela; "
                f"por isso, os valores abaixo não representam exclusivamente o ano {ano_filtro}."
                if ano_filtro is not None
                else
                "Os valores correspondem ao período disponível na tabela consolidada."
            )
        )
        sql_faixa = "SELECT * FROM faixa_etaria WHERE municipio = ?"
        params_faixa = [ORIGEM]
        df_faixa = ler_sql(sql_faixa, tuple(params_faixa))
        if doenca_escolhida and "tipo_cancer" in df_faixa.columns:
            df_faixa = df_faixa[df_faixa["tipo_cancer"] == doenca_escolhida]
        if df_faixa.empty:
            st.info("Não há dados de faixa etária para essa seleção.")
        else:
            st.dataframe(df_faixa, use_container_width=True, hide_index=True)

    with st.expander("Tendência estadual", expanded=False):
        df_estado = ler_sql(
            "SELECT * FROM tendencia_estadual WHERE municipio = ?",
            (ORIGEM,)
        )
        if doenca_escolhida and "tipo_cancer" in df_estado.columns:
            df_estado = df_estado[df_estado["tipo_cancer"] == doenca_escolhida]
        if ano_filtro is not None and "ano" in df_estado.columns:
            df_estado = df_estado[df_estado["ano"] == ano_filtro]
        if df_estado.empty:
            st.info("Não há análise de tendência estadual para essa seleção.")
        else:
            st.caption("Compare os valores do município com a referência estadual.")
            st.dataframe(df_estado, use_container_width=True, hide_index=True)

    with st.expander("Anomalias", expanded=False):
        df_anom = ler_sql("SELECT * FROM anomalias WHERE municipio = ?", (ORIGEM,))
        if doenca_escolhida and "tipo_cancer" in df_anom.columns:
            df_anom = df_anom[df_anom["tipo_cancer"] == doenca_escolhida]
        if ano_filtro is not None and "ano" in df_anom.columns:
            df_anom = df_anom[df_anom["ano"] == ano_filtro]
        if df_anom.empty:
            st.info("Não há anomalias registradas para essa seleção.")
        else:
            st.dataframe(df_anom, use_container_width=True, hide_index=True)

    with st.expander("Priorização", expanded=False):
        df_prior = ler_sql("SELECT * FROM priorizacao_executiva WHERE municipio = ?", (ORIGEM,))
        if doenca_escolhida and "tipo_cancer" in df_prior.columns:
            df_prior = df_prior[df_prior["tipo_cancer"] == doenca_escolhida]
        if ano_filtro is not None and "ano" in df_prior.columns:
            df_prior = df_prior[df_prior["ano"] == ano_filtro]
        if df_prior.empty:
            st.info("Não há priorização calculada para essa seleção.")
        else:
            st.dataframe(df_prior, use_container_width=True, hide_index=True)

    with st.expander("Vulnerabilidade", expanded=False):
        try:
            df_vuln = ler_sql("SELECT * FROM vulnerabilidade WHERE municipio = ?", (ORIGEM,))
            if doenca_escolhida and "tipo_cancer" in df_vuln.columns:
                df_vuln = df_vuln[df_vuln["tipo_cancer"] == doenca_escolhida]
            if ano_filtro is not None and "ano" in df_vuln.columns:
                df_vuln = df_vuln[df_vuln["ano"] == ano_filtro]
            if df_vuln.empty:
                st.info("Não há dados de vulnerabilidade para essa seleção.")
            else:
                st.dataframe(df_vuln, use_container_width=True, hide_index=True)
        except Exception:
            st.info("Não há dados de vulnerabilidade disponíveis.")

    st.divider()
    st.markdown("### Resumo analítico da seleção")
    if analise_base.empty:
        st.info("Não há dados suficientes para gerar o resumo desta seleção.")
    else:
        total_internacoes = int(analise_base["internacoes"].sum())
        total_obitos = int(analise_base["obitos"].sum())
        total_valor = float(analise_base["valor_total"].sum())
        permanencia_media = float(
            analise_base["permanencia_media"].mean()
        )
        principal = analise_base.iloc[0]
        periodo = str(ano_filtro) if ano_filtro is not None else "2013–2025"
        st.markdown(
            f"Para **{NOME_MUNICIPIO}**, no período **{periodo}**, "
            f"a seleção reúne **{total_internacoes:,} internações registradas**, "
            f"**{total_obitos:,} óbitos registrados** e "
            f"**R$ {total_valor:,.2f} em valores hospitalares registrados**."
        )
        st.markdown(
            f"A doença com maior número de internações na seleção é "
            f"**{principal['tipo_cancer']}**, com "
            f"**{int(principal['internacoes']):,} registros**."
        )
        st.caption(
            f"Permanência média calculada entre as doenças selecionadas: "
            f"{permanencia_media:.1f} dias. "
            "O resumo descreve os registros disponíveis e não representa incidência de casos novos."
        )

    st.divider()
    st.markdown("### Relatório analítico")
    st.caption(
        "Prioridades explicadas pelo motor analítico do Escudo (motivo, impacto e "
        "recomendação). Esta tabela não possui dimensão anual própria, por isso não "
        "muda com o ano selecionado acima."
    )
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
                dados, x="tipo_cancer", y="internacoes", color="municipio",
                barmode="group", color_discrete_sequence=PALETA,
                category_orders={"municipio": [NOME_MUNICIPIO, outro_nome]},
            )
            fig.update_traces(hovertemplate="%{x}: %{y} internações<extra>%{fullData.name}</extra>")
            mostrar(estilizar(fig, f"Internações — {NOME_MUNICIPIO} x {outro_nome}",
                              "Números absolutos: municípios de tamanhos diferentes não se comparam só por aqui"))


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
            fig.update_traces(line={"color": COR_PRINCIPAL, "width": 2}, marker={"size": 8})
        elif tipo_grafico == "Área":
            fig = px.area(grafico, x=eixo, y=coluna_resultado)
            fig.update_traces(line={"color": COR_PRINCIPAL, "width": 2})
        else:
            fig = px.bar(grafico, x=eixo, y=coluna_resultado)
            fig.update_traces(marker_color=COR_PRINCIPAL)
        if eixo == "ano":
            fig.update_xaxes(dtick=1)

        mostrar(estilizar(fig, medida, NOME_MUNICIPIO + (f" · {doenca_escolhida}" if doenca_escolhida else "")))



# A área de Análise concentra as análises e o relatório analítico.


st.caption(
    "Escudo Feminino · dados públicos de saúde · "
    "internações hospitalares do SIH/SUS não equivalem a casos novos."
)
