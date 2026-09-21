import streamlit as st

from dashboard.components.municipio_selector import renderizar as selecionar_municipio
from dashboard.components.profile_selector import renderizar as selecionar_perfil
from dashboard.data_context import listar_municipios
from dashboard.state import concluir_onboarding, obter
from dashboard.styles import marca


def renderizar():
    municipios = listar_municipios()

    if not municipios:
        st.error(
            "Nenhum município com dados carregados está disponível para a interface."
        )
        st.stop()

    st.session_state.setdefault("municipio_origem", municipios[0]["origem"])
    marca()

    st.markdown(
        """
        <div class="ef-hero">
            <div class="ef-overline">Entrada</div>
            <div class="ef-title">Transformar dados em entendimento.</div>
            <div class="ef-subtitle">
                Escolha para quem a informação será apresentada e qual município
                você quer analisar. A base analítica continua sendo a mesma.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 1. Escolha o município")
    selecionar_municipio(municipios)

    st.markdown("### 2. Escolha como você quer enxergar os dados")
    selecionar_perfil()

    st.markdown(
        """
        <div class="ef-note">
            A seleção de perfil muda a linguagem, a ordem e a ênfase da interface.
            Ela não cria uma base de dados diferente.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "Entrar no Escudo Feminino",
        type="primary",
        use_container_width=True,
    ):
        concluir_onboarding()
        st.switch_page("views/home.py")
