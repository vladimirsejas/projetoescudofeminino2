import streamlit as st

from dashboard.data_context import construir_contexto, fechar_contexto
from dashboard.state import obter, PERFIS
from dashboard.styles import marca


TEXTOS = {
    "cidada": {
        "overline": "Panorama da cidade",
        "titulo": "O que está acontecendo em {cidade}?",
        "subtitulo": "Uma leitura simples dos dados de internações registradas no SUS.",
    },
    "secretaria": {
        "overline": "Panorama para gestão",
        "titulo": "O que está acontecendo em {cidade}?",
        "subtitulo": "Indicadores observados, prioridades analíticas e sinais para acompanhamento.",
    },
    "prefeitura": {
        "overline": "Visão executiva",
        "titulo": "O que merece atenção em {cidade}?",
        "subtitulo": "Uma leitura executiva baseada nos indicadores observados na rede SUS.",
    },
    "operadora": {
        "overline": "Visão assistencial",
        "titulo": "Qual é o comportamento da demanda em {cidade}?",
        "subtitulo": "Internações, permanência, custos e distribuição observada na rede SUS.",
    },
    "investidor": {
        "overline": "Visão de mercado",
        "titulo": "Qual é o tamanho da demanda observada em {cidade}?",
        "subtitulo": "Os números abaixo representam internações registradas no SUS, não o mercado total.",
    },
}


def renderizar():
    cidade = obter("municipio_nome")
    perfil = obter("perfil")
    ctx = construir_contexto(obter("municipio_origem"))

    try:
        marca(f"{cidade} · {PERFIS[perfil]}")

        t = TEXTOS[perfil]
        st.markdown(
            f"""
            <div class="ef-hero">
                <div class="ef-overline">{t["overline"]}</div>
                <div class="ef-title">{t["titulo"].format(cidade=cidade)}</div>
                <div class="ef-subtitle">{t["subtitulo"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Internações", f"{ctx['internacoes']:,}")
        col2.metric("Óbitos", f"{ctx['obitos']:,}")
        col3.metric("Permanência média", f"{ctx['permanencia_media']:.1f} dias")
        col4.metric("Tipo com mais internações", ctx["lider"])

        st.markdown("### Três coisas para saber primeiro")

        cards = [
            (
                "Volume observado",
                f"{ctx['internacoes']:,} internações estão registradas para {cidade}.",
            ),
            (
                "Tipo que mais aparece",
                (
                    f"{ctx['lider']} concentra o maior número de internações "
                    "entre os tipos monitorados."
                    if ctx["lider"] != "—"
                    else "Ainda não há dados suficientes para apontar um líder."
                ),
            ),
            (
                "Próximo passo",
                "Use Explorar para investigar indicadores ou Perguntar para formular uma pergunta específica.",
            ),
        ]

        if perfil == "investidor":
            cards[0] = (
                "Demanda observada",
                f"{ctx['internacoes']:,} internações registradas no SUS em {cidade}.",
            )

        colunas = st.columns(3)
        for coluna, (titulo, texto) in zip(colunas, cards):
            with coluna:
                st.markdown(
                    f"""
                    <div class="ef-card">
                        <div class="ef-card-title">{titulo}</div>
                        <div class="ef-card-text">{texto}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if perfil == "investidor":
            st.markdown(
                """
                <div class="ef-note">
                    Limite de interpretação: os números representam a demanda observada
                    nas internações do SUS e não medem todo o mercado privado.
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif perfil == "cidada":
            st.markdown(
                """
                <div class="ef-note">
                    O Escudo Feminino trabalha com registros de internações do SUS.
                    Isso não é a mesma coisa que contar casos novos de câncer.
                </div>
                """,
                unsafe_allow_html=True,
            )
    finally:
        fechar_contexto(ctx)


renderizar()
