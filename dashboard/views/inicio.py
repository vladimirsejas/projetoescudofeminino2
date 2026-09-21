import streamlit as st

from dashboard.components.municipio_selector import renderizar as selecionar_municipio
from dashboard.components.profile_selector import renderizar as selecionar_perfil
from dashboard.components.cancer_selector import renderizar as selecionar_cancer
from dashboard.data_context import listar_municipios, listar_cancers_disponiveis
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
                Escolha a cidade e a doença que você quer analisar. Depois,
                defina para quem a informação será apresentada. A base analítica
                continua sendo a mesma.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 1. Defina o foco da análise")

    col_municipio, col_doenca = st.columns(2)

    with col_municipio:
        st.markdown("**Município**")
        selecionar_municipio(municipios)

    cancers = listar_cancers_disponiveis(obter("municipio_origem"))

    with col_doenca:
        st.markdown("**Doença**")
        selecionar_cancer(cancers)

    st.markdown("### 2. Escolha como você quer enxergar os dados")
    selecionar_perfil()

    st.markdown(
        """
        <div class="ef-note">
            A seleção de doença define o foco inicial da análise. A seleção de perfil
            muda a linguagem, a ordem e a ênfase da interface.
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


renderizar()
