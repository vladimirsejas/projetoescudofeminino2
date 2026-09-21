import streamlit as st
import plotly.express as px

from dashboard.data_context import construir_contexto, fechar_contexto
from dashboard.state import obter
from dashboard.styles import marca


def renderizar():
    cidade = obter("municipio_nome")
    ctx = construir_contexto(obter("municipio_origem"))

    try:
        marca(f"{cidade} · Explorar")
        st.markdown(
            """
            <div class="ef-hero">
                <div class="ef-overline">Exploração</div>
                <div class="ef-title">Aprofunde o panorama</div>
                <div class="ef-subtitle">
                    A camada de exploração começa pelos dados que já existem,
                    sem recalcular a cadeia analítica.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if ctx["ranking"].empty:
            st.info("Não há dados de internações para este município.")
            return

        st.markdown("### Internações por tipo de câncer")
        fig = px.bar(
            ctx["ranking"],
            x="tipo_cancer",
            y="total",
            text="total",
            title=f"Internações registradas — {cidade}",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Tendências e sinais")
        if ctx["tendencias"].empty:
            st.info("A tabela de tendências ainda não está disponível.")
        else:
            colunas = [
                c for c in
                ["tipo_cancer", "evento", "desvio", "confiabilidade"]
                if c in ctx["tendencias"].columns
            ]
            st.dataframe(
                ctx["tendencias"][colunas],
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("### Base de conhecimento")
        if ctx["base"].empty:
            st.info("A base de conhecimento ainda não está disponível.")
        else:
            colunas = [
                c for c in
                ["tipo_cancer", "nivel_prioridade", "motivo", "impacto", "recomendacao"]
                if c in ctx["base"].columns
            ]
            st.dataframe(
                ctx["base"][colunas],
                use_container_width=True,
                hide_index=True,
            )
    finally:
        fechar_contexto(ctx)


renderizar()
