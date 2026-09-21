import streamlit as st

from dashboard.state import obter, definir


NOMES_CANCER = {
    "MAMA": "Câncer de mama",
    "COLORRETAL": "Câncer colorretal",
    "COLO_UTERO": "Câncer do colo do útero",
    "OVARIO": "Câncer de ovário",
    "PELE_NAO_MELANOMA": "Pele não melanoma",
    "PULMAO": "Câncer de pulmão",
    "TIREOIDE": "Câncer de tireoide",
}


def nome_cancer(tipo_cancer):
    return NOMES_CANCER.get(
        str(tipo_cancer),
        str(tipo_cancer).replace("_", " ").title(),
    )


def renderizar(cancers):
    if not cancers:
        st.info("Não há doenças com dados carregados para este município.")
        return None

    atual = obter("cancer_selecionado")
    if atual not in cancers:
        atual = cancers[0]
        definir("cancer_selecionado", atual)

    escolha = st.selectbox(
        "Doença",
        cancers,
        index=cancers.index(atual),
        format_func=nome_cancer,
        key="cancer_global",
        help="Escolha qual doença você quer acompanhar no Escudo Feminino.",
    )

    if escolha != obter("cancer_selecionado"):
        definir("cancer_selecionado", escolha)

    return escolha
