import os
import sqlite3
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "algoritimos"))

from configuracao_geografica import listar_municipios_disponiveis, obter_municipio, UF_REFERENCIA
from lia import INICIO, Contexto, responder as lia_responder
from lia_rosto import img as rosto_lia
from inteligencia import (
    anos_fora_do_padrao,
    anos_fora_todos,
    cancer_de,
    canceres_com_duplicidade,
    carregar_faixas,
    carregar_serie,
    comparar_faixas,
    confiabilidade,
    destaques_cancer,
    evidencias_planejamento,
    ficha_cancer,
    formatar_numero,
    leitura_evolucao,
    leitura_faixas,
    nome_doenca,
    projetar,
    quando_aparece,
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
#   - a tela não calcula nada: tudo vem de algoritimos/inteligencia.py.
# Portas (abas): Panorama (o que está acontecendo), Evolução (como
# mudou e para onde vai), Investigar (o que merece ser pesquisado),
# Planejamento (que evidências entram na discussão), Método. A Lia
# (lateral; algoritimos/lia.py, docs/LIA.md) atravessa todas: conduz
# por botões e leva o painel até o gráfico. Sem caixa de texto livre
# (saiu em 09/2026). Dinheiro aparece sempre como "valor hospitalar
# registrado no SIH/SUS", nunca como orçamento.
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
.escudo-info { background: #f3f2f8; border: 1px solid #e6e3ef; border-radius: 16px; padding: 12px 18px; margin-top: 10px; color: #4d4863; font-size: .92rem; }
.escudo-cartao { background: #fff; border: 1px solid #ebe8f2; border-radius: 16px; padding: 16px 20px; margin: 10px 0; }
.escudo-cartao h4 { margin: 0 0 6px 0; font-family: 'Manrope', sans-serif; color: #292541; }
.escudo-cartao li { margin: 3px 0; color: #3d3852; }
.escudo-cartao .acao { color: #4d4863; font-size: .92rem; margin-top: 6px; }
.lia-nome { font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 1.25rem; color: #292541; }
.lia-nome span { font-weight: 500; font-size: .95rem; color: #706b82; }
.lia-cargo { color: #706b82; font-size: .85rem; line-height: 1.3; }
.lia-fala-grande { color: #3d3852; font-size: 1.08rem; margin: 6px 0 12px; }
div[data-testid="stRadio"]:has(input[value="Panorama"]) > div { gap: 4px; border-bottom: 1px solid #e6e3ef; }
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
def duplicados_municipio(origem):
    conn = sqlite3.connect(BANCO)
    try:
        return canceres_com_duplicidade(conn, origem)
    finally:
        conn.close()


@st.cache_data
def faixas_municipio(origem):
    conn = sqlite3.connect(BANCO)
    try:
        return carregar_faixas(conn, origem, UF_REFERENCIA)
    finally:
        conn.close()


@st.cache_data
def evidencias(origem):
    return evidencias_planejamento(serie_municipio(origem))


def reais(valor, compacto=False):
    """R$ no formato brasileiro; compacto para rótulos de gráfico."""
    if compacto and valor >= 1e6:
        return f"R$ {formatar_numero(valor / 1e6, 2)} mi"
    if compacto and valor >= 1e3:
        return f"R$ {formatar_numero(valor / 1e3)} mil"
    return f"R$ {formatar_numero(valor)}"


def pergunta(texto):
    st.markdown(f'<div class="escudo-pergunta">{texto}</div>', unsafe_allow_html=True)


def leitura(titulo, frases):
    st.markdown(
        f'<div class="escudo-leitura"><b>{titulo}</b><ul>'
        + "".join(f"<li>{f}</li>" for f in frases) + "</ul></div>",
        unsafe_allow_html=True,
    )


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
            f'óbitos</b> durante a internação e <b>{reais(resumo["valor_total"].sum())}</b> em valores '
            f'hospitalares registrados no SIH/SUS.</div>',
            unsafe_allow_html=True,
        )

if resumo.empty:
    st.info(f"Ainda não há internações registradas para {nome_cidade}.")
    st.stop()

# ------------------------------------------------------------
# ESTADO DA TELA
#
# Aba, câncer em foco, medida e camadas ficam em chaves próprias do
# session_state, e cada widget tem uma chave que inclui o valor atual
# (ex.: "w_doenca_PULMAO"). Motivo: o Streamlit apaga o estado de um
# widget que sai da tela, e quando ele volta o navegador pode devolver
# o valor ANTIGO, desfazendo o que a Lia escolheu (foi o que aconteceu
# nos testes: pulmão virava mama ao trocar de aba). Com a chave
# atrelada ao valor, todo valor mudado por fora cria um widget novo,
# sem lembrança velha. definir() é como a Lia "leva" o painel.
# ------------------------------------------------------------

ABAS = ["Panorama", "Evolução", "Investigar", "Planejamento", "Método"]
PADROES = {"aba": "Panorama", "medida": "Internações",
           "ver_estado": True, "ver_fora": True, "ver_projecao": False}
for chave, valor in PADROES.items():
    st.session_state.setdefault(chave, valor)


def definir(chave, valor):
    st.session_state[chave] = valor


def chave_widget(chave):
    return f"w_{chave}_{st.session_state[chave]}"


def sincronizar(chave, chave_do_widget):
    st.session_state[chave] = st.session_state[chave_do_widget]


def seletor(onde, rotulo, chave, opcoes, **kwargs):
    """st.radio preso à chave persistente (ver ESTADO DA TELA)."""
    k = chave_widget(chave)
    return onde.radio(rotulo, opcoes, index=opcoes.index(st.session_state[chave]), key=k,
                      on_change=sincronizar, args=(chave, k), **kwargs)


def chave_liga(onde, rotulo, chave, **kwargs):
    """st.toggle preso à chave persistente (ver ESTADO DA TELA)."""
    k = chave_widget(chave)
    return onde.toggle(rotulo, value=st.session_state[chave], key=k,
                       on_change=sincronizar, args=(chave, k), **kwargs)


# Câncer em foco: começa pelo maior; se trocar de cidade e ele não
# existir lá, volta para o maior. Vale para todas as abas.
codigos = resumo["tipo_cancer"].tolist()
if st.session_state.get("doenca") not in codigos:
    definir("doenca", codigos[0])
    st.session_state.pop("ultimo_clique", None)
doenca = st.session_state["doenca"]
nome = nome_doenca(doenca)

ctx_lia = Contexto(serie=serie, cidade=nome_cidade, faixas=faixas_municipio(ORIGEM),
                   duplicados=tuple(duplicados_municipio(ORIGEM)))
st.session_state.setdefault("lia", {"cidade": None, "atual": None, "pilha": []})
lia_estado = st.session_state["lia"]
if lia_estado["cidade"] != ORIGEM:  # trocou de cidade: a Lia recomeça
    lia_estado.update({"cidade": ORIGEM, "atual": lia_responder(ctx_lia, INICIO), "pilha": []})


def lia_mostrar(resposta):
    """Guarda a resposta e leva o painel até o gráfico dela."""
    if lia_estado["atual"] is not None:
        lia_estado["pilha"].append(lia_estado["atual"])
    lia_estado["atual"] = resposta
    st.session_state["lia_fechada"] = True
    destino = resposta.destino or {}
    if destino.get("aba") in ABAS:
        definir("aba", destino["aba"])
    if destino.get("cancer") in codigos:
        definir("doenca", destino["cancer"])
        st.session_state["ultimo_clique"] = destino["cancer"]
    if destino.get("medida"):
        definir("medida", destino["medida"])
    for camada, valor in (destino.get("camadas") or {}).items():
        definir(camada, valor)


def lia_clicar(acao):
    lia_mostrar(lia_responder(ctx_lia, acao))


def recarregar():
    """st.rerun nas versões novas do Streamlit; experimental_rerun nas antigas."""
    (getattr(st, "rerun", None) or st.experimental_rerun)()


def lia_voltar():
    if lia_estado["pilha"]:
        lia_estado["atual"] = lia_estado["pilha"].pop()


# ------------------------------------------------------------
# BOAS-VINDAS DA LIA (primeiro acesso)
# ------------------------------------------------------------

if not st.session_state.get("lia_fechada"):
    boas_vindas = lia_responder(ctx_lia, INICIO)
    st.markdown('<div class="lia-boasvindas">', unsafe_allow_html=True)
    c_rosto, c_fala = st.columns([1, 4.2])
    with c_rosto:
        st.markdown(rosto_lia("acolhedora", 150), unsafe_allow_html=True)
    with c_fala:
        st.markdown(f'<div class="lia-nome">Lia <span>· pesquisadora do Escudo Feminino</span></div>'
                    f'<div class="lia-fala-grande">{boas_vindas.fala.replace("**", "")}</div>',
                    unsafe_allow_html=True)
        # 4 portas de entrada (docs/LIA.md); os 8 caminhos ficam na lateral
        principais = {"mais_aparece", "aumentando", "atencao", "futuro"}
        colunas = st.columns(4)
        for i, (rotulo, acao) in enumerate(a for a in boas_vindas.botoes if a[1].get("id") in principais):
            colunas[i].button(rotulo, key=f"bv_{i}", on_click=lia_clicar, args=(acao,),
                              use_container_width=True)
        st.button("Prefiro explorar sozinha", key="bv_fechar",
                  on_click=lambda: st.session_state.update(lia_fechada=True))
    st.markdown('</div>', unsafe_allow_html=True)

aba = seletor(st, "Navegação", "aba", ABAS, horizontal=True, label_visibility="collapsed")


# ============================================================
# PANORAMA — o que está acontecendo?
# ============================================================

MEDIDAS = {
    "Internações": ("internacoes", "Quais cânceres mais levam as mulheres de {c} ao hospital?", formatar_numero),
    "Valor hospitalar registrado": ("valor_total", "Em quais cânceres se concentram os valores hospitalares registrados em {c}?",
                                    lambda v: reais(v, compacto=True)),
    "Óbitos na internação": ("obitos", "Em quais cânceres mais mulheres de {c} morrem durante a internação?", formatar_numero),
    "Dias de internação": ("dias_permanencia", "Quais cânceres ocupam mais dias de internação em {c}?", formatar_numero),
}

if aba == "Panorama":
    medida = seletor(st, "Medir por", "medida", list(MEDIDAS), horizontal=True)
    coluna, titulo, formato = MEDIDAS[medida]
    pergunta(titulo.format(c=nome_cidade))
    st.markdown('<div class="escudo-dica">Total no período. Clique numa barra para pôr aquele câncer em foco.'
                + (' Valor hospitalar registrado = o que as AIHs registraram no SIH/SUS; não é o orçamento '
                   'do município nem o custo total do tratamento.' if coluna == "valor_total" else "")
                + '</div>', unsafe_allow_html=True)

    barras = resumo.sort_values(coluna)  # o maior fica em cima
    fig = go.Figure(go.Bar(
        x=barras[coluna], y=barras["doenca"], orientation="h",
        text=[formato(v) for v in barras[coluna]],
        textposition="outside", cliponaxis=False,
        marker={"color": [AZUL if c == doenca else CINZA for c in barras["tipo_cancer"]],
                "line": {"width": 0}},
        customdata=barras[["tipo_cancer"]].values,
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
        showlegend=False,
    ))
    fig.update_xaxes(visible=False, range=[0, max(barras[coluna].max(), 1) * 1.15])
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
    # "ligada" nas próximas execuções, e sem isso ela desfaria uma
    # troca feita depois pelo seletor.
    pontos = (evento or {}).get("selection", {}).get("points", []) if evento else []
    if pontos:
        clicado = (pontos[0].get("customdata", [None])[0]
                   or dict(zip(resumo["doenca"], resumo["tipo_cancer"])).get(pontos[0].get("y")))
        if clicado and clicado != st.session_state.get("ultimo_clique"):
            st.session_state["ultimo_clique"] = clicado
            definir("doenca", clicado)
            recarregar()

    seletor(st, "Câncer em foco", "doenca", codigos, format_func=nome_doenca, horizontal=True)
    ficha = ficha_cancer(serie, doenca)

    pergunta(f"O que chama atenção no {cancer_de(doenca)}?")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Internações", formatar_numero(ficha["internacoes"]),
              help=f"{formatar_numero(ficha['pct_internacoes'], 1)}% das internações por câncer acompanhadas")
    k2.metric("Óbitos na internação", formatar_numero(ficha["obitos"]),
              help=f"Letalidade hospitalar {formatar_numero(ficha['letalidade'], 1)}% "
                   f"(Estado: {formatar_numero(ficha['letalidade_estado'], 1)}%)")
    k3.metric("Valor hospitalar registrado", reais(ficha["valor"], compacto=True),
              help=f"{reais(ficha['valor'])} no SIH/SUS; média de {reais(ficha['valor_medio'])} por internação "
                   f"(Estado: {reais(ficha['valor_medio_estado'])})")
    k4.metric("Dias de internação", formatar_numero(ficha["dias"]),
              help=f"Média de {formatar_numero(ficha['permanencia'], 1)} dias por internação "
                   f"(Estado: {formatar_numero(ficha['permanencia_estado'], 1)})")
    leitura("O que chama atenção", destaques_cancer(serie, doenca))
    st.caption(f"Para a história ano a ano e a projeção, veja a aba Evolução. Período: {ano_ini}–{ano_fim}.")


# ============================================================
# EVOLUÇÃO — como mudou e para onde vai?
# ============================================================

mun = serie_doenca(serie, doenca)

if aba == "Evolução":
    pergunta(f"Como as internações por {cancer_de(doenca)} mudaram de {ano_ini} a {ano_fim}?")
    st.markdown(f'<div class="escudo-dica">Câncer em foco: {nome}. Troque na aba Panorama.</div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    ver_estado = chave_liga(c1, "Comparar com o Estado de SP", "ver_estado",
                           help="Linha cinza: o ritmo do Estado redimensionado para o tamanho da cidade.")
    ver_fora = chave_liga(c2, "Destacar anos fora do padrão", "ver_fora",
                         help="Anos que ficaram longe do esperado pela tendência dos outros anos.")
    ver_projecao = chave_liga(c3, "Projeção de tendência até " + str(ano_fim + 3), "ver_projecao",
                             help="Continuação da tendência histórica, com faixa de incerteza. "
                                  "Não é previsão clínica nem IA preditiva.")

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
            marker={"size": 8, "symbol": "circle-open"}, name="Projeção de tendência",
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
            fig.add_annotation(x=linha["ano"], y=linha["observado"], text=f"{linha['direcao']} do esperado",
                               showarrow=False, yshift=20 if linha["direcao"] == "acima" else -20,
                               font={"size": 11, "color": LARANJA})
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(rangemode="tozero")
    estilizar(fig, altura=430)
    st.plotly_chart(fig, use_container_width=True, theme=None, config=CONFIG_GRAFICO)

    leitura("O que o gráfico mostra", leitura_evolucao(serie, doenca))

    if ver_projecao:
        teste = testar_projecao(mun)
        if teste:
            melhor = teste["erro_tendencia"] <= teste["erro_media"]
            st.caption(
                f"Projeção de tendência: continua a reta de {ano_ini}–{ano_fim}, se nada mudar. "
                f"Teste de acerto: calculada só até {ano_fim - 3} e comparada com {ano_fim - 2}–{ano_fim}, errou em média "
                f"{formatar_numero(teste['erro_tendencia'], 1)} internações por ano, "
                f"{'menos' if melhor else 'mais'} do que repetir a média dos anos anteriores "
                f"({formatar_numero(teste['erro_media'], 1)}). Não é previsão clínica nem indica causa. "
                f"A pressão projetada em dias e valores está na aba Planejamento."
            )

    # Confiabilidade: a casa dos avisos é aqui, junto da tendência.
    avisos = confiabilidade(serie, doenca, duplicados_municipio(ORIGEM))
    st.markdown(
        '<div class="escudo-info"><b>Confiabilidade desta informação</b><ul>'
        + "".join(f"<li>{'⚠️ ' if nivel == 'atencao' else ''}{texto}</li>" for nivel, texto in avisos)
        + "</ul></div>",
        unsafe_allow_html=True,
    )


# ============================================================
# INVESTIGAR — o que merece ser pesquisado?
# ============================================================

if aba == "Investigar":
    pergunta(f"Em que anos algum câncer saiu do padrão em {nome_cidade}?")
    st.markdown('<div class="escudo-dica">Todos os cânceres de uma vez. "Esperado" = tendência calculada com os '
                'outros anos. Detectar não explica a causa.</div>', unsafe_allow_html=True)
    fora_todos = anos_fora_todos(serie)
    f1, f2 = st.columns([1, 1])
    direcao = f1.radio("Direção", ["Todos", "Acima do esperado", "Abaixo do esperado"], horizontal=True, key="direcao")
    incluir_pequenos = f2.toggle("Incluir números pequenos", value=True,
                                 help="Cânceres com média abaixo de 10 internações por ano, onde o acaso pesa mais.")
    tabela = fora_todos
    if direcao != "Todos":
        tabela = tabela[tabela["direcao"] == ("acima" if direcao.startswith("Acima") else "abaixo")]
    if not incluir_pequenos:
        tabela = tabela[~tabela["numeros_pequenos"]]
    if tabela.empty:
        st.info("Nenhum ano fora do padrão com esses filtros.")
    else:
        st.dataframe(
            tabela.assign(
                observado=tabela["observado"].round(0).astype(int),
                esperado=[formatar_numero(v, 1) for v in tabela["esperado"]],
                diferenca_pct=[f"{'+' if v > 0 else ''}{formatar_numero(v)}%" for v in tabela["diferenca_pct"]],
                numeros_pequenos=tabela["numeros_pequenos"].map({True: "sim", False: "não"}),
            ).rename(columns={"doenca": "Câncer", "ano": "Ano", "observado": "Internações",
                              "esperado": "Esperado", "direcao": "Direção",
                              "numeros_pequenos": "Números pequenos", "diferenca_pct": "Diferença"}),
            use_container_width=True, hide_index=True,
        )
        contagem = tabela["ano"].value_counts()
        if contagem.iloc[0] >= 2:
            st.caption(f"{contagem.index[0]} aparece para {contagem.iloc[0]} cânceres ao mesmo tempo — quando "
                       f"vários mudam juntos, vale checar o registro antes de concluir.")

    pergunta("Quando cada câncer aparece?")
    st.markdown('<div class="escudo-dica">Primeiro ano com internação, persistência (em quantos anos aparece), '
                'ano de pico e ritmo médio de crescimento.</div>', unsafe_allow_html=True)
    aparece = quando_aparece(serie)
    aparece["ritmo_anual_pct"] = [f"{formatar_numero(v, 1)}%" for v in aparece["ritmo_anual_pct"]]
    st.dataframe(aparece.rename(columns={
        "doenca": "Câncer", "primeiro_ano": "Primeiro ano", "anos_com_internacao": "Anos com internação",
        "persistencia": "Persistência", "ano_de_pico": "Ano de pico", "internacoes_no_pico": "Internações no pico",
        "ritmo_anual_pct": "Ritmo ao ano"}), use_container_width=True, hide_index=True)

    pergunta(f"A idade das mulheres internadas por {cancer_de(doenca)} mudou?")
    faixas = faixas_municipio(ORIGEM)
    tabela_faixas, periodos = comparar_faixas(faixas, doenca)
    if periodos is None:
        st.info("Não há idade registrada para esta seleção.")
    else:
        fig = go.Figure()
        for periodo, cor in zip(periodos, [CINZA, AZUL]):
            parte = tabela_faixas[tabela_faixas["periodo"] == periodo]
            fig.add_trace(go.Bar(
                x=parte["faixa"], y=parte["pct"], name=periodo, marker={"color": cor, "line": {"width": 0}},
                text=[f"{formatar_numero(v)}%" for v in parte["pct"]], textposition="outside", cliponaxis=False,
                customdata=parte[["internacoes"]].values,
                hovertemplate="%{x}: %{y:.1f}% (%{customdata[0]} internações)<extra>" + periodo + "</extra>",
            ))
        fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
        fig.update_yaxes(ticksuffix="%", rangemode="tozero")
        estilizar(fig, altura=340)
        st.plotly_chart(fig, use_container_width=True, theme=None, config=CONFIG_GRAFICO)
        leitura("O que o gráfico mostra", leitura_faixas(tabela_faixas, periodos)
                + ["A faixa de 50 a 69 anos é a do rastreamento de câncer de mama recomendado pelo INCA."
                   if doenca == "MAMA" else "Percentual de cada faixa dentro de cada período."])

    pergunta("Comparar cidades")
    st.markdown('<div class="escudo-info">Para dizer quais cidades estão acima do padrão é preciso dividir pela '
                'população feminina de cada uma (internações por 100 mil mulheres). A população do IBGE ainda '
                'não está no banco — é a próxima etapa desta área.</div>', unsafe_allow_html=True)

    st.download_button(
        "Baixar a série anual desta cidade (CSV)",
        serie.assign(doenca=serie["tipo_cancer"].map(nome_doenca))
             .to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name=f"escudo_{ORIGEM.lower()}_serie_anual.csv", mime="text/csv",
    )


# ============================================================
# PLANEJAMENTO — que evidências entram na discussão?
# ============================================================

if aba == "Planejamento":
    pergunta(f"Que evidências de {nome_cidade} merecem entrar na discussão de planejamento?")
    st.markdown('<div class="escudo-dica">O Escudo reúne evidências e a pressão projetada se a tendência continuar. '
                'Não define quanto investir: a decisão é da gestão, que conhece orçamento, filas e capacidade.</div>',
                unsafe_allow_html=True)
    lista = evidencias(ORIGEM)

    pontos_q = [e for e in lista if e["letalidade_relativa"] is not None]
    if pontos_q:
        pergunta("Onde olhar primeiro?")
        fig = go.Figure(go.Scatter(
            x=[e["crescimento"] for e in pontos_q], y=[e["letalidade_relativa"] for e in pontos_q],
            mode="markers+text", text=[e["doenca"] for e in pontos_q], textposition="top center",
            marker={"size": [max(12, min(46, e["internacoes"] ** 0.5 * 1.6)) for e in pontos_q],
                    "color": AZUL, "opacity": 0.75, "line": {"color": "#ffffff", "width": 2}},
            customdata=[[e["internacoes"]] for e in pontos_q],
            hovertemplate="<b>%{text}</b><br>cresce %{x:.1f}% ao ano<br>letalidade %{y:.2f}× a do Estado"
                          "<br>%{customdata[0]:,.0f} internações<extra></extra>",
            showlegend=False,
        ))
        fig.add_hline(y=1, line={"color": CINZA, "width": 1})
        fig.add_vline(x=0, line={"color": CINZA, "width": 1})
        # rótulo na própria linha de referência, longe dos pontos
        fig.add_annotation(xref="paper", x=0.01, y=1, xanchor="left", yanchor="bottom", showarrow=False,
                           text="letalidade igual à do Estado", font={"size": 11, "color": TINTA_SUAVE})
        ys = [e["letalidade_relativa"] for e in pontos_q]
        xs = [e["crescimento"] for e in pontos_q]
        fig.update_yaxes(range=[min(min(ys), 1) - 0.1, max(max(ys), 1) + 0.12])
        fig.update_xaxes(range=[min(min(xs), 0) - 1, max(xs) + 1.5])
        fig.update_xaxes(title="Crescimento das internações (% ao ano)", ticksuffix="%", zeroline=False)
        fig.update_yaxes(title="Letalidade hospitalar ÷ a do Estado", zeroline=False)
        estilizar(fig, altura=420)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, theme=None, config=CONFIG_GRAFICO)
        fora_q = [e["doenca"] for e in lista if e["letalidade_relativa"] is None]
        st.caption("Tamanho da bolha = número de internações. Linha horizontal = letalidade igual à do Estado."
                   + (f" Fora do gráfico por ter menos de 5 óbitos: {', '.join(fora_q)}." if fora_q else ""))

    pergunta("Evidências por câncer")
    for e in lista:
        p = e["pressao"]
        ano_p = p["internacoes"]["ano"]
        sinais = "".join(f"<li>{s}</li>" for s in e["sinais"]) or "<li>Sem sinal de alerta pelos critérios do Escudo.</li>"
        fragil = [nomecol for nomecol, chave in (("internações", "internacoes"), ("dias", "dias_permanencia"),
                                                  ("valor", "valor_total")) if not p[chave]["tendencia_acerta_mais"]]
        pressao = (
            f"<li>Internações: cerca de {formatar_numero(p['internacoes']['previsto'])} "
            f"(entre {formatar_numero(p['internacoes']['minimo'])} e {formatar_numero(p['internacoes']['maximo'])}; "
            f"em {ano_fim}: {formatar_numero(p['internacoes']['atual'])})</li>"
            f"<li>Dias de internação: cerca de {formatar_numero(p['dias_permanencia']['previsto'])} "
            f"(entre {formatar_numero(p['dias_permanencia']['minimo'])} e {formatar_numero(p['dias_permanencia']['maximo'])})</li>"
            f"<li>Valor hospitalar registrado: cerca de {reais(p['valor_total']['previsto'])} "
            f"(entre {reais(p['valor_total']['minimo'])} e {reais(p['valor_total']['maximo'])})</li>"
        )
        st.markdown(
            f'<div class="escudo-cartao"><h4>{e["doenca"]}</h4>'
            f'<b>Sinais nos dados</b><ul>{sinais}</ul>'
            f'<b>Se a tendência continuar, em {ano_p}</b><ul>{pressao}</ul>'
            + (f'<div class="acao">Baixa confiança na projeção de {", ".join(fragil)}: no teste de acerto, a '
               f'tendência não errou menos que repetir a média.</div>' if fragil else "")
            + (f'<div class="acao">Linha de ação conhecida (INCA): {e["linha_de_acao"]}.</div>' if e["linha_de_acao"] else "")
            + '</div>',
            unsafe_allow_html=True,
        )
    st.caption(f"Valores em R$ nominais registrados no SIH/SUS, sem correção de inflação. {ano_fim} está em "
               f"investigação e entra na tendência; leia a projeção como ordem de grandeza.")


# ============================================================
# MÉTODO
# ============================================================

if aba == "Método":
    pergunta("Como ler estes dados")
    st.markdown(f"""
- **Fonte:** internações do SUS (SIH/SUS, DATASUS) de mulheres residentes em {nome_cidade}, {ano_ini}–{ano_fim}, para 7 tipos de câncer.
- **Internação não é caso novo.** Uma mesma mulher pode ser internada mais de uma vez; quem se trata só em
  ambulatório ou por plano privado não aparece aqui.
- **Valor hospitalar registrado** é o valor das AIHs no SIH/SUS. Não é o orçamento do município nem o custo
  total do tratamento (quimioterapia e radioterapia ambulatoriais ficam fora). Valores nominais, sem inflação.
- **O ano é o de processamento da internação** (competência da AIH), que pode não coincidir com o ano em que
  ela aconteceu.
- **Linha cinza (Estado de SP):** a série do Estado redimensionada para o tamanho de {nome_cidade}. Compara o
  *ritmo*, não o volume.
- **Fora do padrão:** o ano ficou longe do esperado pela tendência dos *outros* anos, além da oscilação normal
  e com diferença de pelo menos 3 internações. Aponta onde olhar; não explica a causa.
- **Projeção de tendência:** a reta histórica prolongada, com a faixa onde o valor deve cair em 9 de cada 10
  cenários se o passado se repetir, e um teste de acerto em anos já conhecidos. Não é "IA preditiva" nem
  previsão clínica. Óbitos não são projetados: são poucos por ano.
- **Uma fonte por cidade:** se o banco tiver a mesma internação vinda de duas fontes, o Escudo usa só uma.

**O que estes dados não permitem responder:** causas, incidência (casos novos), orçamento ideal, efeito de uma
política, e — até a população do IBGE entrar no banco — comparação justa entre cidades de tamanhos diferentes.
""")


# ============================================================
# LIA NA LATERAL (atravessa todas as abas)
# ============================================================

with st.sidebar:
    atual = lia_estado["atual"]
    c_rosto, c_nome = st.columns([1, 2.6])
    with c_rosto:
        st.markdown(rosto_lia(atual.expressao, 76), unsafe_allow_html=True)
    with c_nome:
        st.markdown('<div class="lia-nome">Lia</div><div class="lia-cargo">Pesquisadora do Escudo Feminino'
                    f'<br>{nome_cidade}</div>', unsafe_allow_html=True)

    boas_vindas_aberta = not st.session_state.get("lia_fechada")
    if boas_vindas_aberta:
        # a saudação já está no centro da tela: aqui não se repete
        st.markdown("Escolha um caminho ali no centro da tela.")
    if not boas_vindas_aberta:
        st.markdown(atual.fala)
    if atual.destino and atual.destino.get("aba") and lia_estado["pilha"]:
        st.caption(f"O painel foi para a aba {atual.destino['aba']}"
                   + (f" · {nome_doenca(atual.destino['cancer'])}" if atual.destino.get("cancer") else "") + ".")
    if atual.numeros:
        with st.expander("Os números por trás"):
            st.markdown("\n".join(f"- {n}" for n in atual.numeros))

    for i, (rotulo, acao) in enumerate([] if boas_vindas_aberta else atual.botoes):
        st.button(rotulo, key=f"lia_{i}_{rotulo}", on_click=lia_clicar, args=(acao,), use_container_width=True)
    if lia_estado["pilha"]:
        st.button("← Voltar", key="lia_voltar", on_click=lia_voltar)

st.caption("Escudo Feminino · dados públicos do SIH/SUS · internações não equivalem a casos novos.")
