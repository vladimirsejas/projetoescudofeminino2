import streamlit as st

PERFIS = {
    "cidada": "Cidadã / população",
    "secretaria": "Secretaria da Saúde da Mulher",
    "prefeitura": "Prefeitura / gestor",
    "operadora": "Operadora de plano de saúde",
    "investidor": "Investidor",
}

PAGINAS = {
    "inicio": "Início",
    "home": "Panorama",
    "perguntar": "Perguntar",
    "explorar": "Explorar",
    "previsoes": "Previsões",
    "comparar": "Comparar",
    "biblioteca": "Biblioteca",
}

DEFAULTS = {
    "perfil": "secretaria",
    "municipio_origem": "RIO_CLARO",
    "municipio_nome": "Rio Claro",
    "onboarding_concluido": False,
    "cancer_selecionado": None,
    "indicador_selecionado": None,
    "cesta_comparacao": [],
    "historico_chat": [],
}


def inicializar_estado():
    for chave, valor in DEFAULTS.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def obter(chave):
    inicializar_estado()
    return st.session_state[chave]


def definir(chave, valor):
    inicializar_estado()
    st.session_state[chave] = valor


def selecionar_perfil(perfil):
    if perfil not in PERFIS:
        raise ValueError(f"Perfil inválido: {perfil}")
    definir("perfil", perfil)


def selecionar_municipio(municipio):
    definir("municipio_origem", municipio["origem"])
    definir("municipio_nome", municipio["nome"])


def concluir_onboarding():
    definir("onboarding_concluido", True)
