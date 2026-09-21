import streamlit as st

from dashboard.state import selecionar_municipio, obter


def renderizar(municipios):
    atual = obter("municipio_origem")
    origens = [m["origem"] for m in municipios]

    if atual not in origens:
        selecionar_municipio(municipios[0])
        atual = municipios[0]["origem"]

    indice = origens.index(atual)

    escolha = st.selectbox(
        "Município",
        municipios,
        index=indice,
        format_func=lambda item: item["nome"],
        key="municipio_global",
        help="Digite parte do nome para localizar rapidamente um município.",
    )

    if escolha["origem"] != atual:
        selecionar_municipio(escolha)
        st.rerun()

    return escolha
