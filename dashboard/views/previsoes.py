
import html

import pandas as pd
import streamlit as st

from dashboard.data_context import construir_contexto, fechar_contexto
from dashboard.state import obter
from dashboard.styles import marca


def _anos_disponiveis(previsoes_horizontes):
    if previsoes_horizontes.empty or "ano_previsto" not in previsoes_horizontes.columns:
        return []

    anos = sorted(
        int(ano)
        for ano in previsoes_horizontes["ano_previsto"].dropna().unique()
        if int(ano) in (2027, 2028, 2029)
    )
    return anos


def _nome_cancer(tipo_cancer):
    nomes = {
        "MAMA": "Câncer de mama",
        "COLORRETAL": "Câncer colorretal",
        "COLO_UTERO": "Câncer do colo do útero",
        "OVARIO": "Câncer de ovário",
        "PELE_NAO_MELANOMA": "Pele não melanoma",
        "PULMAO": "Câncer de pulmão",
        "TIREOIDE": "Câncer de tireoide",
    }
    return nomes.get(str(tipo_cancer), str(tipo_cancer).replace("_", " ").title())


def _cartoes_previsao(df, ano_escolhido, ultimo_ano):
    cartoes = []

    for _, linha in df.sort_values("tipo_cancer").iterrows():
        cancer = html.escape(_nome_cancer(linha["tipo_cancer"]))
        valor = linha.get("internacoes_previstas")

        if pd.isna(valor):
            valor_formatado = "—"
        else:
            valor_formatado = f"{float(valor):.1f}".replace(".", ",")

        cartoes.append(
            f"""
            <div class="ef-forecast-card">
                <div class="ef-forecast-cancer">{cancer}</div>
                <div class="ef-forecast-value">{valor_formatado}</div>
                <div class="ef-forecast-unit">internações estimadas</div>
                <div class="ef-forecast-meta">
                    {ano_escolhido} · extrapolação a partir de {ultimo_ano}
                </div>
            </div>
            """
        )

    st.markdown(
        '<div class="ef-forecast-grid">'
        + "".join(cartoes)
        + "</div>",
        unsafe_allow_html=True,
    )


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

        horizontes = ctx.get("previsoes_horizontes", pd.DataFrame())
        serie = ctx["serie_temporal"]

        if horizontes.empty:
            st.info(
                "As projeções de 2027 a 2029 ainda não estão registradas para "
                "este município. Rode algoritimos\\previsao_temporal.py para "
                "gerar a tabela de horizontes futuros."
            )
            return

        anos = _anos_disponiveis(horizontes)

        if not anos:
            st.info(
                "Não há projeções disponíveis para o triênio 2027–2029."
            )
            return

        ano_escolhido = st.selectbox(
            "Escolha o ano",
            anos,
            index=0,
            key="ano_previsao_interface",
            help="Selecione uma das três estimativas futuras do Escudo Feminino.",
        )

        df = horizontes[
            horizontes["ano_previsto"].astype(int) == int(ano_escolhido)
        ].copy()

        if df.empty:
            st.info("Não há projeções registradas para este ano.")
            return

        ultimo_ano = (
            int(serie["ano"].max())
            if not serie.empty and "ano" in serie.columns
            else 2025
        )

        st.markdown(f"### O que o histórico sugere para {ano_escolhido}?")


        _cartoes_previsao(df, ano_escolhido, ultimo_ano)

        st.markdown(
            """
            <div class="ef-note">
                Estas três janelas futuras são <strong>extrapolações lúdicas</strong>
                da tendência histórica das internações registradas. Não são previsão
                de novos casos de câncer e não têm validação própria para 2027, 2028 ou
                2029. O ponto validado do motor fica separado como referência técnica.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Ver dados técnicos"):
            tecnicas = [
                coluna
                for coluna in [
                    "tipo_cancer",
                    "ano_previsto",
                    "horizonte",
                    "internacoes_previstas",
                ]
                if coluna in df.columns
            ]
            st.dataframe(
                df[tecnicas].sort_values("tipo_cancer"),
                use_container_width=True,
                hide_index=True,
            )
    finally:
        fechar_contexto(ctx)


renderizar()
