import streamlit as st
import pandas as pd

from dashboard.data_context import conectar, listar_municipios
from dashboard.state import obter
from dashboard.styles import marca


def renderizar():
    cidade = obter("municipio_nome")
    origem = obter("municipio_origem")
    municipios = listar_municipios()

    marca(f"{cidade} · Comparar")

    st.markdown(
        """
        <div class="ef-hero">
            <div class="ef-overline">Comparação</div>
            <div class="ef-title">Dois municípios, a mesma régua.</div>
            <div class="ef-subtitle">
                A comparação usa os mesmos indicadores disponíveis na base de internações.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    alternativas = [m for m in municipios if m["origem"] != origem]

    if not alternativas:
        st.info("Não há outro município com dados carregados para comparação.")
        return

    nomes = [m["nome"] for m in alternativas]
    nome_padrao = nomes[0]
    escolhido_nome = st.selectbox(
        "Comparar {0} com".format(cidade),
        nomes,
        index=0,
        key="municipio_comparado_interface",
    )
    escolhido = next(m for m in alternativas if m["nome"] == escolhido_nome)

    conexao = conectar()
    try:
        resumo = pd.read_sql(
            """
            SELECT
                municipio,
                COUNT(*) AS internacoes,
                COALESCE(SUM(obito), 0) AS obitos,
                COALESCE(SUM(valor_total), 0) AS valor_total,
                COALESCE(AVG(dias_permanencia), 0) AS permanencia_media
            FROM internacoes
            WHERE municipio IN (?, ?)
            GROUP BY municipio
            """,
            conexao,
            params=(origem, escolhido["origem"]),
        )

        nomes_map = {
            origem: cidade,
            escolhido["origem"]: escolhido_nome,
        }
        resumo["municipio"] = resumo["municipio"].map(nomes_map)
        resumo = resumo.rename(
            columns={
                "municipio": "Município",
                "internacoes": "Internações",
                "obitos": "Óbitos",
                "valor_total": "Valor Total (R$)",
                "permanencia_media": "Permanência Média (dias)",
            }
        )

        st.dataframe(
            resumo,
            use_container_width=True,
            hide_index=True,
        )
    finally:
        conexao.close()


renderizar()
