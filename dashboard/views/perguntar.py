import streamlit as st

from dashboard.state import obter
from dashboard.styles import marca


def renderizar():
    marca(f"{obter('municipio_nome')} · Perguntar")

    st.markdown(
        """
        <div class="ef-hero">
            <div class="ef-overline">Pergunte ao Escudo</div>
            <div class="ef-title">O chat entra aqui.</div>
            <div class="ef-subtitle">
                Esta é a superfície reservada para integrar o motor do
                chat_escudo.py à interface. Nesta primeira fase, o motor
                continua intacto e o painel antigo continua preservado.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Integração da conversa com o dashboard fica para a fase específica do chat; "
        "nesta etapa não duplicamos nem reescrevemos o motor."
    )


renderizar()
