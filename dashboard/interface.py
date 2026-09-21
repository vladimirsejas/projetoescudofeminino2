import os
import sys
from pathlib import Path

import streamlit as st

DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_DIR = DASHBOARD_DIR.parent
ALG_DIR = PROJECT_DIR / "algoritimos"

for caminho in (PROJECT_DIR, ALG_DIR):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

from dashboard import state
from dashboard.styles import aplicar_estilos


st.set_page_config(
    page_title="Escudo Feminino",
    page_icon=":material/shield:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

state.inicializar_estado()
aplicar_estilos()

inicio = st.Page(
    "views/inicio.py",
    title="Início",
    icon=":material/home:",
    default=True,
)
home = st.Page(
    "views/home.py",
    title="Panorama",
    icon=":material/dashboard:",
)
perguntar = st.Page(
    "views/perguntar.py",
    title="Perguntar",
    icon=":material/chat:",
)
explorar = st.Page(
    "views/explorar.py",
    title="Explorar",
    icon=":material/search:",
)
previsoes = st.Page(
    "views/previsoes.py",
    title="Previsões",
    icon=":material/insights:",
)
comparar = st.Page(
    "views/comparar.py",
    title="Comparar",
    icon=":material/compare_arrows:",
)
biblioteca = st.Page(
    "views/biblioteca.py",
    title="Biblioteca",
    icon=":material/local_library:",
)

paginas = [
    inicio,
    home,
    perguntar,
    explorar,
    previsoes,
    comparar,
    biblioteca,
]


def navegar():
    """
    Usa a navegação oficial do Streamlit quando disponível.

    Em versões mais antigas que ainda tenham st.navigation, tenta
    posicionar a navegação no topo; se a assinatura não aceitar
    position="top", cai para a navegação padrão da sidebar em vez
    de quebrar a aplicação.
    """
    if hasattr(st, "navigation"):
        try:
            return st.navigation(paginas, position="top")
        except TypeError:
            return st.navigation(paginas, position="sidebar")

    # Compatibilidade de último recurso para versões sem st.navigation.
    # A interface antiga continua sendo a alternativa executável.
    st.warning(
        "Esta interface nova precisa de uma versão recente do Streamlit. "
        "Atualize o Streamlit para usar a navegação final."
    )
    st.stop()


pagina = navegar()

if (
    not state.obter("onboarding_concluido")
    and pagina.title != "Início"
):
    st.info("Primeiro escolha município e perfil na tela de Início.")
    if st.button("Ir para Início", type="primary"):
        st.switch_page("views/inicio.py")
    st.stop()

pagina.run()
