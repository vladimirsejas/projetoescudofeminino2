import os
import sqlite3
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "algoritimos"))

from configuracao_geografica import listar_municipios_disponiveis, obter_municipio, UF_REFERENCIA
from conversa import registrar_pergunta, responder
from inteligencia import (
    ano_atipico_no_estado,
    anos_fora_do_padrao,
    carregar_serie,
    formatar_numero,
    leitura_evolucao,
    nome_doenca,
    projetar,
    resumo_doencas,
    ritmo_estadual_na_escala,
    serie_doenca,
    testar_projecao,
)

# ============================================================
# ESCUDO FEMININO — painel
#
# Reescrito do zero (09/2026). O painel anterior tinha 7 abas que
# repetiam os mesmos números em vários lugares. Regras deste:
#   - cada informação tem uma casa só;
#   - todo gráfico = pergunta (título) + gráfico + leitura em texto;
#   - a tela não calcula nada: tudo vem de algoritimos/inteligencia.py,
#     a mesma fonte que o chat deve usar.
# O painel antigo continua no histórico do git (commit 273fbe5).
# ============================================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

st.set_page_config(
    page_title="Escudo Feminino",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta validada para daltonismo (ver skill de visualização):
# azul = a cidade, cinza = referência, laranja = fora do padrão.
AZUL = "#2a78d6"
AZUL_FAIXA = "rgba(42,120,214,0.13)"
CINZA = "#b9b7c4"
LARANJA = "#eb6834"
TINTA = "#292541"
TINTA_SUAVE = "#706b82"
GRADE = "#ebe8f2"
CONFIG_GRAFICO = {"displayModeBar": False}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f8f7fb; }
.block-container { max-width: 1180px; padding-top: 3.2rem; padding-bottom: 4rem; }
h1, h2, h3 { font-family: 'Manrope', sans-serif; color: #292541; letter-spacing: -0.02em; }
.escudo-marca { color: #7565a8; font-size: .78rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
.escudo-titulo { font-family: 'Manrope', sans-serif; color: #292541; font-size: 2.1rem; font-weight: 700; line-height: 1.15; margin: 4px 0 6px; }
.escudo-sub { color: #625d72; font-size: 1.02rem; max-width: 760px; }
.escudo-pergunta { font-family: 'Manrope', sans-serif; color: #292541; font-size: 1.35rem; font-weight: 700; margin: 26px 0 2px; }
.escudo-dica { color: #8a8599; font-size: .88rem; margin-bottom: 4px; }
.escudo-leitura { background: #fff; border: 1px solid #ebe8f2; border-radius: 16px; padding: 14px 20px; margin-top: 6px; color: #3d3852; }
.escudo-leitura li { margin: 5px 0; }
.escudo-alerta { background: #fff7ef; border: 1px solid #f6d9c2; border-radius: 16px; padding: 12px 18px; margin-top: 10px; color: #6b3d1e; font-size: .93rem; }
div[data-baseweb="select"] > div { border-radius: 12px; background: #fff; }
section[data-testid="stSidebar"] { min-width: 400px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DADOS (uma consulta só, via inteligencia.py)
# ============================================================

@st.cache_data
def municipios():
    return listar_municipios_disponiveis()


@st.cache_data
def serie_municipio(origem):
    conn = sqlite3.connect(BANCO)
    try:
        return carregar_serie(conn, origem, UF_REFERENCIA)
    finally:
        conn.close()


@st.cache_data
def atipico_estado(origem, ano):
    return ano_atipico_no_estado(serie_municipio(origem), ano)


def estilizar(fig, altura):
    fig.update_layout(
        height=altura,
        font={"family": "DM Sans, sans-serif", "size": 13, "color": TINTA},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin={"l": 10, "r": 30, "t": 16, "b": 10},
        legend={"orientation": "h", "yanchor": "top", "y": -0.12, "x": 0, "title": None},
        hoverlabel={"bgcolor": "#ffffff", "font_color": TINTA, "bordercolor": GRADE},
        separators=",.",
        showlegend=True,
    )
    fig.update_xaxes(showgrid=False, linecolor=GRADE, automargin=True, tickfont={"color": TINTA_SUAVE})
    fig.update_yaxes(gridcolor=GRADE, zeroline=False, automargin=True, tickfont={"color": TINTA_SUAVE})
    return fig


lista_municipios = municipios()
if not lista_municipios:
    st.error("Nenhum município disponível no banco.")
    st.stop()


# ============================================================
# TOPO
# ============================================================

nomes = [m["nome"] for m in lista_municipios]
padrao = obter_municipio()
indice_padrao = next((i for i, m in enumerate(lista_municipios) if m["origem"] == padrao), 0)

col_titulo, col_cidade = st.columns([2.2, 1])
with col_cidade:
    nome_cidade = st.selectbox("Município", nomes, index=indice_padrao,
                               help="Digite para procurar entre os municípios de SP.")
cidade = next(m for m in lista_municipios if m["nome"] == nome_cidade)
ORIGEM = cidade["origem"]

serie = serie_municipio(ORIGEM)
resumo = resumo_doencas(serie) if not serie.empty else pd.DataFrame()

with col_titulo:
    st.markdown('<div class="escudo-marca">Escudo Feminino</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="escudo-titulo">Câncer em mulheres de {nome_cidade}</div>',
                unsafe_allow_html=True)
    if not resumo.empty:
        ano_ini, ano_fim = int(serie["ano"].min()), int(serie["ano"].max())
        st.markdown(
            f'<div class="escudo-sub">De {ano_ini} a {ano_fim}, mulheres que moram em {nome_cidade} '
            f'tiveram <b>{formatar_numero(resumo["internacoes"].sum())} internações</b> no SUS pelos '
            f'{len(resumo)} tipos de câncer acompanhados, com <b>{formatar_numero(resumo["obitos"].sum())} '
            f'óbitos</b> durante a internação.</div>',
            unsafe_allow_html=True,
        )

if resumo.empty:
    st.info(f"Ainda não há internações registradas para {nome_cidade}.")
    st.stop()

# Doença escolhida: começa pela maior; se trocar de cidade e a doença
# não existir lá, volta para a maior.
codigos = resumo["tipo_cancer"].tolist()
if st.session_state.get("doenca") not in codigos:
    st.session_state["doenca"] = codigos[0]
    st.session_state.pop("ultimo_clique", None)


# ============================================================
# 1. QUAIS CÂNCERES PESAM MAIS
# ============================================================

st.markdown(f'<div class="escudo-pergunta">Quais cânceres mais levam as mulheres de {nome_cidade} ao hospital?</div>',
            unsafe_allow_html=True)
st.markdown('<div class="escudo-dica">Total de internações no período. Clique numa barra para ver a história daquele câncer.</div>',
            unsafe_allow_html=True)

barras = resumo.iloc[::-1]  # a maior fica em cima
fig = go.Figure(go.Bar(
    x=barras["internacoes"], y=barras["doenca"], orientation="h",
    text=[formatar_numero(v) for v in barras["internacoes"]],
    textposition="outside", cliponaxis=False,
    marker={"color": [AZUL if c == st.session_state["doenca"] else CINZA for c in barras["tipo_cancer"]],
            "line": {"width": 0}},
    customdata=barras[["tipo_cancer", "obitos"]].values,
    hovertemplate="<b>%{y}</b><br>%{x:,.0f} internações<br>%{customdata[1]:,.0f} óbitos<extra></extra>",
    showlegend=False,
))
fig.update_xaxes(visible=False, range=[0, barras["internacoes"].max() * 1.12])
fig.update_yaxes(showgrid=False)
estilizar(fig, altura=70 + 42 * len(barras))
fig.update_layout(bargap=0.3, showlegend=False)

try:
    evento = st.plotly_chart(fig, use_container_width=True, theme=None, config=CONFIG_GRAFICO,
                             on_select="rerun", selection_mode="points", key="barras")
except TypeError:  # Streamlit antigo, sem clique em gráfico
    st.plotly_chart(fig, use_container_width=True, theme=None, config=CONFIG_GRAFICO)
    evento = None

# O clique só vale quando é novo: a seleção do gráfico continua
# "ligada" nas próximas execuções, e sem isso ela desfaria uma troca
# feita depois pelo seletor abaixo.
pontos = (evento or {}).get("selection", {}).get("points", []) if evento else []
if pontos:
    clicado = pontos[0].get("customdata", [None])[0] or dict(zip(resumo["doenca"], resumo["tipo_cancer"])).get(pontos[0].get("y"))
    if clicado and clicado != st.session_state.get("ultimo_clique"):
        st.session_state["ultimo_clique"] = clicado
        st.session_state["doenca"] = clicado
        st.rerun()


# ============================================================
# 2. COMO ESSE CÂNCER MUDOU
# ============================================================

doenca = st.radio("Câncer", codigos, key="doenca", format_func=nome_doenca, horizontal=True,
                  label_visibility="collapsed")
nome = nome_doenca(doenca)
mun = serie_doenca(serie, doenca)
ano_ini, ano_fim = int(mun["ano"].min()), int(mun["ano"].max())

st.markdown(f'<div class="escudo-pergunta">Como as internações por câncer de {nome.lower()} mudaram de {ano_ini} a {ano_fim}?</div>',
            unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
ver_estado = c1.toggle("Comparar com o Estado de SP", value=True,
                       help="Linha cinza: o ritmo do Estado redimensionado para o tamanho da cidade.")
ver_fora = c2.toggle("Destacar anos fora do padrão", value=True,
                     help="Anos que ficaram longe do esperado pela tendência dos outros anos.")
ver_projecao = c3.toggle("Projeção exploratória até " + str(ano_fim + 3), value=False,
                         help="Continuação da tendência histórica, com faixa de incerteza. Não é previsão clínica.")

fig = go.Figure()

if ver_projecao:
    proj = projetar(mun)
    fig.add_trace(go.Scatter(
        x=list(proj["ano"]) + list(proj["ano"])[::-1],
        y=list(proj["maximo"]) + list(proj["minimo"])[::-1],
        mode="lines", fill="toself", fillcolor=AZUL_FAIXA, line={"width": 0},
        hoverinfo="skip", name="Faixa provável da projeção (90%)",
    ))
    fig.add_trace(go.Scatter(
        x=[ano_fim] + list(proj["ano"]),
        y=[float(mun["internacoes"].iloc[-1])] + list(proj["internacoes"]),
        mode="lines+markers", line={"color": AZUL, "width": 2, "dash": "dot"},
        marker={"size": 8, "symbol": "circle-open"}, name="Projeção exploratória",
        hovertemplate="%{x}: cerca de %{y:.0f} (projeção)<extra></extra>",
    ))

if ver_estado:
    estado = ritmo_estadual_na_escala(serie, doenca)
    if not estado.empty:
        fig.add_trace(go.Scatter(
            x=estado["ano"], y=estado["internacoes"], mode="lines",
            line={"color": CINZA, "width": 2},
            name=f"Ritmo do Estado de SP (na escala de {nome_cidade})",
            hovertemplate="%{x}: Estado no ritmo equivalente a %{y:.0f}<extra></extra>",
        ))

fig.add_trace(go.Scatter(
    x=mun["ano"], y=mun["internacoes"], mode="lines+markers",
    line={"color": AZUL, "width": 2.5}, marker={"size": 8, "color": AZUL},
    name=f"{nome_cidade}: internações registradas",
    hovertemplate="%{x}: %{y:.0f} internações<extra></extra>",
))

fora = anos_fora_do_padrao(mun)
if ver_fora and not fora.empty:
    fig.add_trace(go.Scatter(
        x=fora["ano"], y=fora["observado"], mode="markers",
        marker={"size": 17, "color": "rgba(0,0,0,0)", "line": {"color": LARANJA, "width": 2.5}},
        name="Fora do padrão",
        customdata=fora[["esperado", "direcao"]].values,
        hovertemplate="%{x}: %{y:.0f} internações, %{customdata[1]} do esperado (~%{customdata[0]:.0f})<extra></extra>",
    ))
    for _, linha in fora.iterrows():
        fig.add_annotation(
            x=linha["ano"], y=linha["observado"],
            text=f"{linha['direcao']} do esperado", showarrow=False,
            yshift=20 if linha["direcao"] == "acima" else -20,
            font={"size": 11, "color": LARANJA},
        )

fig.update_xaxes(dtick=1)
fig.update_yaxes(rangemode="tozero")
estilizar(fig, altura=430)
st.plotly_chart(fig, use_container_width=True, theme=None, config=CONFIG_GRAFICO)

# Leitura: frases calculadas em inteligencia.py (as mesmas que o chat
# pode usar), nunca escritas à mão aqui.
frases = leitura_evolucao(serie, doenca)
st.markdown(
    '<div class="escudo-leitura"><b>O que o gráfico mostra</b><ul>'
    + "".join(f"<li>{f}</li>" for f in frases)
    + "</ul></div>",
    unsafe_allow_html=True,
)

fora_estado, total_canceres = atipico_estado(ORIGEM, ano_fim)
if total_canceres and fora_estado >= total_canceres / 2:
    st.markdown(
        f'<div class="escudo-alerta"><b>{ano_fim} em investigação.</b> No Estado de SP inteiro, '
        f'{fora_estado} dos {total_canceres} cânceres acompanhados saltaram ao mesmo tempo nesse ano. '
        f'Quando todas as doenças mudam juntas, é mais provável uma mudança no registro ou no '
        f'processamento das AIHs do que no adoecimento. Até isso ser esclarecido, leia {ano_fim} com cautela.</div>',
        unsafe_allow_html=True,
    )

if ver_projecao:
    teste = testar_projecao(mun)
    if teste:
        melhor = teste["erro_tendencia"] <= teste["erro_media"]
        st.caption(
            f"Projeção exploratória: continua a tendência de {ano_ini}–{ano_fim}, se nada mudar. "
            f"Teste de acerto: treinada até {ano_fim - 3} e comparada com {ano_fim - 2}–{ano_fim}, errou em média "
            f"{formatar_numero(teste['erro_tendencia'], 1)} internações por ano, "
            f"{'menos' if melhor else 'mais'} do que repetir a média dos anos anteriores "
            f"({formatar_numero(teste['erro_media'], 1)}). Não é previsão clínica nem indica causa."
        )


# ============================================================
# MÉTODO
# ============================================================

with st.expander("Como ler estes dados"):
    st.markdown(f"""
- **Fonte:** internações do SUS (SIH/SUS, DATASUS) de mulheres residentes em {nome_cidade}, {ano_ini}–{ano_fim}.
- **Internação não é caso novo.** Uma mesma mulher pode ser internada mais de uma vez; quem se trata só em
  ambulatório ou por plano privado não aparece aqui.
- **O ano é o de processamento da internação** (competência da AIH), que pode não coincidir com o ano em que
  ela aconteceu.
- **Linha cinza (Estado de SP):** a série do Estado redimensionada para o tamanho de {nome_cidade}. Serve para
  comparar o *ritmo*, não o volume: onde a linha azul fica acima da cinza, a cidade cresceu mais que o Estado.
- **Fora do padrão:** o ano ficou longe do esperado pela tendência dos *outros* anos, além da oscilação normal
  da série e com diferença de pelo menos 3 internações. Isso aponta onde olhar; não explica a causa.
- **Projeção exploratória:** a tendência histórica prolongada, com a faixa onde o valor deve cair em 9 de cada
  10 cenários, se o comportamento passado continuar.
""")


# ============================================================
# CHAT (painel lateral, sabe a cidade e o câncer em foco)
# ============================================================

SUGESTOES = [
    "O que merece atenção?",
    f"Como evoluiu o câncer de {nome.lower()}?",
    "O que esperar até 2028?",
    "Qual câncer mais mata?",
    "Estamos crescendo mais que o Estado?",
    "Houve algum ano fora do padrão?",
]

with st.sidebar:
    st.markdown("### Pergunte ao Escudo")
    st.caption(f"Em foco: {nome_cidade} · {nome}. Os números vêm dos mesmos cálculos dos gráficos.")

    linguagem = st.radio("Linguagem", ["Simples", "Técnica"], horizontal=True, key="linguagem")
    perfil = "SIMPLES" if linguagem == "Simples" else "TECNICO"

    chave_chat = f"chat_{ORIGEM}"
    historico = st.session_state.setdefault(chave_chat, [])

    with st.form("form_chat", clear_on_submit=True):
        digitada = st.text_area("Sua pergunta", height=90, label_visibility="collapsed",
                                placeholder=f"Ex.: o que merece atenção em {nome_cidade}?")
        enviar = st.form_submit_button("Perguntar", use_container_width=True, type="primary")

    st.caption("Ou experimente:")
    sugerida = None
    for i, sugestao in enumerate(SUGESTOES):
        if st.button(sugestao, key=f"sugestao_{i}", use_container_width=True):
            sugerida = sugestao

    pergunta = sugerida or (digitada.strip() if enviar else "")
    if pergunta:
        resultado = responder(pergunta, serie, nome_cidade, cancer_em_foco=doenca, perfil=perfil)
        registrar_pergunta(BANCO, pergunta, resultado["assunto"])
        historico.insert(0, (pergunta, resultado))

    for p, r in historico:
        st.markdown(f"**{p}**")
        st.markdown(r["texto"])
        # Só quando a IA redigiu: aí os números de origem acrescentam
        # algo. Sem IA, a resposta já É a lista de números.
        if r["usou_ia"]:
            with st.expander("Números usados nesta resposta"):
                st.markdown("\n".join(f"- {f}" for f in r["fatos"]))
                st.caption("O texto acima foi redigido pela IA a partir destes números, calculados pelo sistema.")
        st.divider()

st.caption("Escudo Feminino · dados públicos do SIH/SUS · internações não equivalem a casos novos.")
