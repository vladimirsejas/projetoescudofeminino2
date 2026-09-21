import streamlit as st

from dashboard.state import obter
from dashboard.styles import marca


CONCEITOS = [
    (
        "Internação registrada no SUS",
        "Registro de atendimento hospitalar usado nesta base. Não deve ser lido automaticamente como incidência de câncer.",
    ),
    (
        "Tendência",
        "Uma forma de descrever o comportamento de uma série ao longo do tempo ou em comparação com uma referência.",
    ),
    (
        "Anomalia",
        "Um comportamento que se afasta do padrão histórico observado e merece investigação.",
    ),
    (
        "Previsão",
        "Uma extrapolação baseada no comportamento histórico dos dados disponíveis.",
    ),
    (
        "Confiabilidade",
        "Um sinal de transparência sobre o quanto uma estimativa ou comparação pode ser sustentada pelos dados e pela validação realizada.",
    ),
    (
        "Associação não é causalidade",
        "Quando dois indicadores aparecem relacionados, isso não prova que um causou o outro.",
    ),
    (
        "SUS não é incidência",
        "A base hospitalar utilizada pelo projeto registra internações. Ela não substitui um sistema de incidência populacional.",
    ),
]


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
    marca(f"{cidade} · {doenca} · Biblioteca")

    st.markdown(
        """
        <div class="ef-hero">
            <div class="ef-overline">Conhecimento</div>
            <div class="ef-title">Biblioteca do Escudo</div>
            <div class="ef-subtitle">
                Conceitos que ajudam a interpretar os indicadores sem transformar
                um número em uma conclusão maior do que os dados permitem.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for titulo, texto in CONCEITOS:
        with st.expander(titulo):
            st.write(texto)

    st.info(
        "Primeira versão da Biblioteca: conceitos usados diretamente na interpretação "
        "do motor. O catálogo de doenças e indicadores específicos entra na etapa editorial."
    )


renderizar()
