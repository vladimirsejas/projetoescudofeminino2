import streamlit as st

from dashboard.data_context import construir_contexto, fechar_contexto
from dashboard.state import obter, PERFIS
from dashboard.styles import marca


TEXTOS = {
    "cidada": {
        "overline": "Panorama da cidade",
        "titulo": "O que está acontecendo com {doenca} em {cidade}?",
        "subtitulo": "Uma leitura simples dos dados de internações registradas no SUS.",
    },
    "secretaria": {
        "overline": "Panorama para gestão",
        "titulo": "O que está acontecendo com {doenca} em {cidade}?",
        "subtitulo": "Indicadores observados, prioridades analíticas e sinais para acompanhamento.",
    },
    "prefeitura": {
        "overline": "Visão executiva",
        "titulo": "O que merece atenção em {doenca} em {cidade}?",
        "subtitulo": "Uma leitura executiva baseada nos indicadores observados na rede SUS.",
    },
    "operadora": {
        "overline": "Visão assistencial",
        "titulo": "Qual é o comportamento da demanda de {doenca} em {cidade}?",
        "subtitulo": "Internações, permanência, custos e distribuição observada na rede SUS.",
    },
    "investidor": {
        "overline": "Visão de mercado",
        "titulo": "Qual é o tamanho da demanda observada de {doenca} em {cidade}?",
        "subtitulo": "Os números abaixo representam internações registradas no SUS, não o mercado total.",
    },
}


def renderizar():
    cidade = obter("municipio_nome")
    perfil = obter("perfil")
    cancer = obter("cancer_selecionado")
    ctx = construir_contexto(obter("municipio_origem"), cancer)

    try:
        marca(f"{cidade} · {PERFIS[perfil]}")

        t = TEXTOS[perfil]
        nomes = {
            "MAMA": "câncer de mama",
            "COLORRETAL": "câncer colorretal",
            "COLO_UTERO": "câncer do colo do útero",
            "OVARIO": "câncer de ovário",
            "PELE_NAO_MELANOMA": "pele não melanoma",
            "PULMAO": "câncer de pulmão",
            "TIREOIDE": "câncer de tireoide",
        }
        doenca = nomes.get(cancer, "doença selecionada")

        st.markdown(
            f"""
            <div class="ef-hero">
                <div class="ef-overline">{t["overline"]}</div>
                <div class="ef-title">{t["titulo"].format(cidade=cidade, doenca=doenca)}</div>
                <div class="ef-subtitle">{t["subtitulo"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Internações", f"{ctx['internacoes']:,}")
        col2.metric("Óbitos", f"{ctx['obitos']:,}")
        col3.metric("Permanência média", f"{ctx['permanencia_media']:.1f} dias")
        col4.metric("Mortalidade hospitalar", f"{ctx['mortalidade_pct']:.1f}%")

        st.markdown("### Três coisas para saber primeiro")

        nomes = {
            "MAMA": "câncer de mama",
            "COLORRETAL": "câncer colorretal",
            "COLO_UTERO": "câncer do colo do útero",
            "OVARIO": "câncer de ovário",
            "PELE_NAO_MELANOMA": "pele não melanoma",
            "PULMAO": "câncer de pulmão",
            "TIREOIDE": "câncer de tireoide",
        }
        doenca = nomes.get(cancer, "doença selecionada")

        cards = [
            (
                "Volume observado",
                f"{ctx['internacoes']:,} internações de {doenca} estão registradas para {cidade}.",
            ),
            (
                "Mortalidade hospitalar",
                (
                    f"{ctx['mortalidade_pct']:.1f}% das internações registradas terminaram em óbito."
                    if ctx["internacoes"] > 0
                    else "Não há internações suficientes para calcular a taxa."
                ),
            ),
            (
                "Próximo passo",
                "Use Explorar, Perguntar ou Previsões para aprofundar esta análise.",
            ),
        ]

        if perfil == "investidor":
            cards[0] = (
                "Demanda observada",
                f"{ctx['internacoes']:,} internações de {doenca} registradas no SUS em {cidade}.",
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
