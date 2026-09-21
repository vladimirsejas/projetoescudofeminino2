import streamlit as st

from dashboard.state import PERFIS, selecionar_perfil, obter


DESCRICOES = {
    "cidada": (
        "Linguagem simples para entender o panorama de saúde da mulher "
        "no município."
    ),
    "secretaria": (
        "Indicadores, tendências, prioridades, previsões e apoio à decisão."
    ),
    "prefeitura": (
        "Visão executiva: o que chama atenção e o que merece acompanhamento."
    ),
    "operadora": (
        "Demanda observada, permanência, custos e distribuição dos atendimentos."
    ),
    "investidor": (
        "Tamanho e comportamento da demanda observada na rede SUS, com ressalvas."
    ),
}


def renderizar():
    perfil_atual = obter("perfil")
    opcoes = list(PERFIS)

    st.markdown("### Para quem é esta visão?")

    colunas = st.columns(5)

    for coluna, perfil in zip(colunas, opcoes):
        with coluna:
            st.markdown(
                f"""
                <div class="ef-card">
                    <div class="ef-card-title">{PERFIS[perfil]}</div>
                    <div class="ef-card-text">{DESCRICOES[perfil]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            selecionado = perfil == perfil_atual
            if st.button(
                "Selecionado" if selecionado else "Usar esta visão",
                key=f"perfil_{perfil}",
                use_container_width=True,
                type="primary" if selecionado else "secondary",
            ):
                selecionar_perfil(perfil)
                st.rerun()
