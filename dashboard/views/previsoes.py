
import streamlit as st

from algoritimos.previsao_temporal import gerar_previsao_municipio

from dashboard.data_context import construir_contexto, fechar_contexto
from dashboard.state import obter
from dashboard.styles import marca


def _anos_disponiveis(serie_temporal):
    if serie_temporal.empty:
        return []

    ultimo_ano = int(serie_temporal["ano"].max())
    return list(range(ultimo_ano + 1, ultimo_ano + 6))


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

        if ctx["serie_temporal"].empty:
            if ctx["previsoes"].empty:
                st.info(
                    "A série histórica necessária para calcular previsões "
                    "ainda não está disponível para este município."
                )
                return

            st.warning(
                "A série histórica não está disponível para recalcular "
                "outros horizontes. Exibindo a previsão já registrada."
            )
            df = ctx["previsoes"].copy()
            ano_escolhido = None
        else:
            anos = _anos_disponiveis(ctx["serie_temporal"])

            ano_escolhido = st.selectbox(
                "Ano da previsão",
                anos,
                index=0,
                key="ano_previsao_interface",
                help=(
                    "Escolha um ano futuro. O sistema recalcula a "
                    "extrapolação usando a mesma série histórica."
                ),
            )

            df = gerar_previsao_municipio(
                ctx["serie_temporal"],
                ano_alvo=int(ano_escolhido),
            )

        if df.empty:
            st.info("Não há dados suficientes para gerar uma previsão.")
            return

        if ano_escolhido is not None:
            st.markdown(
                f"### Estimativas para {ano_escolhido}"
            )

        colunas = [
            "tipo_cancer",
            "anos_historico",
            "ano_previsto",
            "horizonte_anos",
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
                observado nas internações do SUS. A validação mostrada é histórica e
                de curto prazo; projeções mais distantes têm incerteza maior. Quando a
                regressão não demonstra ganho sobre o baseline simples, o sistema usa
                o último valor observado como referência.
            </div>
            """,
            unsafe_allow_html=True,
        )
    finally:
        fechar_contexto(ctx)


renderizar()
