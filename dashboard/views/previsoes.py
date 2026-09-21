import pandas as pd
import streamlit as st

from dashboard.data_context import construir_contexto, fechar_contexto
from dashboard.state import definir, obter
from dashboard.styles import marca


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
    return nomes.get(
        str(tipo_cancer),
        str(tipo_cancer).replace("_", " ").title(),
    )


def _anos_disponiveis(previsoes_horizontes):
    if previsoes_horizontes.empty or "ano_previsto" not in previsoes_horizontes.columns:
        return []

    return [
        ano
        for ano in (2027, 2028, 2029)
        if ano in set(previsoes_horizontes["ano_previsto"].dropna().astype(int))
    ]


def _valor_formatado(valor):
    if pd.isna(valor):
        return "—"
    return f"{float(valor):.1f}".replace(".", ",")


def _cartao_ano(ano, valor):
    valor_texto = _valor_formatado(valor)

    st.markdown(
        f"""
        <div class="ef-card">
            <div class="ef-card-title">{ano}</div>
            <div class="ef-forecast-value">{valor_texto}</div>
            <div class="ef-card-text">internações estimadas</div>
            <div class="ef-forecast-meta">Extrapolação histórica</div>
        </div>
        """,
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
                    Uma leitura lúdica de 2027 a 2029, baseada no comportamento
                    histórico das internações registradas no SUS.
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
        if len(anos) < 3:
            st.warning(
                "A base disponível não contém o triênio completo 2027–2029."
            )
            return

        tipos = sorted(horizontes["tipo_cancer"].dropna().unique().tolist())

        atual_cancer = obter("cancer_selecionado")
        if atual_cancer not in tipos:
            atual_cancer = tipos[0]
            definir("cancer_selecionado", atual_cancer)

        cancer_escolhido = st.selectbox(
            "Escolha o câncer",
            tipos,
            index=tipos.index(atual_cancer),
            format_func=_nome_cancer,
            key="cancer_previsao_interface",
            help="Escolha qual câncer deseja acompanhar nas estimativas de 2027 a 2029.",
        )

        if cancer_escolhido != obter("cancer_selecionado"):
            definir("cancer_selecionado", cancer_escolhido)

        st.markdown(
            f"### {_nome_cancer(cancer_escolhido)} · projeção 2027–2029"
        )

        df = horizontes[
            (horizontes["tipo_cancer"] == cancer_escolhido)
            & (horizontes["ano_previsto"].astype(int).isin(anos))
        ].copy()

        df = df.sort_values("ano_previsto")

        if df.empty:
            st.info("Não há projeções para o câncer selecionado.")
            return

        colunas = st.columns(3)

        for coluna, ano in zip(colunas, anos):
            with coluna:
                linha = df[df["ano_previsto"].astype(int) == ano]

                if linha.empty:
                    st.markdown(
                        f"""
                        <div class="ef-card">
                            <div class="ef-card-title">{ano}</div>
                            <div class="ef-card-text">
                                Sem projeção disponível.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    continue

                _cartao_ano(ano, linha.iloc[0]["internacoes_previstas"])

        st.markdown(
            """
            <div class="ef-note">
                <strong>Como ler:</strong> 2027, 2028 e 2029 são extrapolações
                lúdicas da tendência histórica das internações registradas.
                Não representam novos casos de câncer e não têm validação própria
                para esses três anos. O ano seguinte ao histórico (2026) permanece
                separado como referência técnica validada.
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
                df[tecnicas].sort_values("ano_previsto"),
                use_container_width=True,
                hide_index=True,
            )
    finally:
        fechar_contexto(ctx)


renderizar()
