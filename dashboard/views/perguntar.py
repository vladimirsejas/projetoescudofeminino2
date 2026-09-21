import streamlit as st

from dashboard.state import obter
from dashboard.styles import marca


def renderizar():
    cidade = obter("municipio_nome")
    cancer = obter("cancer_selecionado")
    nomes = {
        "MAMA": "Câncer de mama",
        "COLORRETAL": "Câncer colorretal",
        "COLO_UTERO": "Câncer do colo do útero",
        "OVARIO": "Câncer de ovário",
        "PELE_NAO_MELANOMA": "Pele não melanoma",
        "PULMAO": "Câncer de pulmão",
        "TIREOIDE": "Câncer de tireoide",
    }
    doenca = nomes.get(cancer, "Doença selecionada")
    marca(f"{cidade} · {doenca} · Perguntar")

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
