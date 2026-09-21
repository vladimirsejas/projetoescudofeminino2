import streamlit as st

from dashboard.data_context import construir_contexto, fechar_contexto
from dashboard.state import obter
from dashboard.styles import marca


def renderizar():
    cidade = obter("municipio_nome")
    ctx = construir_contexto(obter("municipio_origem"))

    try:
        marca(f"{cidade} · Previsões")
        st.markdown(
            """
            <div class="ef-hero">
                <div class="ef-overline">Camada preditiva</div>
                <div class="ef-title">Previsões</div>
                <div class="ef-subtitle">
                    Estimativas baseadas no comportamento histórico das internações registradas no SUS.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if ctx["previsoes"].empty:
            st.info(
                "A tabela de previsões ainda não está disponível para este município."
            )
            return

        df = ctx["previsoes"].copy()

        colunas = [
            "tipo_cancer",
            "ano_previsto",
            "internacoes_previstas",
            "erro_validacao_pct",
            "erro_baseline_pct",
            "supera_baseline",
            "confiabilidade",
        ]
        disponiveis = [c for c in colunas if c in df.columns]

        st.dataframe(
            df[disponiveis],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(
            """
            <div class="ef-note">
                Esta camada não prevê novos casos de câncer. Ela extrapola o comportamento
                observado nas internações do SUS e mostra também a validação e o ganho em
                relação ao baseline simples.
            </div>
            """,
            unsafe_allow_html=True,
        )
    finally:
        fechar_contexto(ctx)
