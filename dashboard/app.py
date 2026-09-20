import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "algoritimos")
)

from configuracao_geografica import (
    listar_municipios_disponiveis,
    ler_tabela_municipio,
    UF_REFERENCIA
)

# ==================================================
# CONFIGURAÇÃO
# ==================================================

st.set_page_config(
    page_title="Escudo Feminino",
    page_icon="🎗️",
    layout="wide"
)

# ==================================================
# BANCO
# ==================================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(BANCO)

# ==================================================
# SELEÇÃO DE MUNICÍPIO
#
# A lista vem do banco (municipios ∩ internacoes), nunca de uma
# lista fixa no código -- assim que outro município tiver dados
# carregados, ele aparece aqui automaticamente.
# ==================================================

municipios_disponiveis = listar_municipios_disponiveis()

if not municipios_disponiveis:
    st.error(
        "Nenhum município cadastrado em `municipios` com dados "
        "carregados em `internacoes`. Rode "
        "etl\\criar_tabela_municipios.py e confira o ETL antes de "
        "abrir o dashboard."
    )
    st.stop()

nomes_disponiveis = [m["nome"] for m in municipios_disponiveis]

nome_escolhido = st.sidebar.selectbox("Município", nomes_disponiveis)

municipio_escolhido = next(
    m for m in municipios_disponiveis if m["nome"] == nome_escolhido
)

ORIGEM = municipio_escolhido["origem"]
NOME_MUNICIPIO = municipio_escolhido["nome"]

# ==================================================
# SELEÇÃO DE PERFIL
#
# Mesma base de dados para todo mundo -- o que muda por perfil é
# só vocabulário, o que aparece primeiro e o que fica escondido.
# Nunca recalcula nada aqui, cada renderizar_* só decide como
# mostrar o que já foi buscado do banco abaixo.
# ==================================================

PERFIS_LABELS = {
    "cidada": "🙋 Cidadã / população em geral",
    "secretaria": "🏛️ Secretaria da Saúde da Mulher",
    "prefeitura": "🏙️ Prefeitura / gestor municipal",
    "operadora": "🏥 Operadora de plano de saúde",
    "investidor": "💰 Investidor",
}

perfil_atual = st.sidebar.selectbox(
    "Você é...",
    list(PERFIS_LABELS.keys()),
    format_func=lambda chave: PERFIS_LABELS[chave],
    index=1,  # secretaria como padrão -- é a visão técnica original
)

# ==================================================
# KPIs PRINCIPAIS
#
# Total de Registros continua sendo a soma geral (município +
# referência estadual), como visão de conjunto. As demais métricas
# nomeadas pelo município (Câncer Líder, custos, permanência,
# óbitos) são filtradas por origem -- sem isso, ficam diluídas pelo
# volume do Estado (o mesmo problema já corrigido nos indicadores
# em algoritimos/).
# ==================================================

total = pd.read_sql(
    """
    SELECT COUNT(*) AS total
    FROM internacoes
    """,
    conexao
).iloc[0]["total"]

ranking = pd.read_sql(
    """
    SELECT
        tipo_cancer,
        COUNT(*) AS total
    FROM internacoes
    WHERE municipio = ?
    GROUP BY tipo_cancer
    ORDER BY total DESC
    """,
    conexao,
    params=(ORIGEM,)
)

origens = pd.read_sql(
    """
    SELECT
        origem,
        COUNT(*) AS total
    FROM internacoes
    GROUP BY origem
    """,
    conexao
)

lider = ranking.iloc[0]["tipo_cancer"] if not ranking.empty else "—"

total_municipio = int(
    pd.read_sql(
        "SELECT COUNT(*) AS total FROM internacoes WHERE municipio = ?",
        conexao,
        params=(ORIGEM,)
    ).iloc[0]["total"]
)

sp_vals = origens.loc[
    origens["origem"] == UF_REFERENCIA,
    "total"
].values

sp = int(sp_vals[0]) if len(sp_vals) > 0 else 0

# ==================================================
# KPIs AVANÇADOS (filtrados pelo município selecionado)
# ==================================================

valor_total = pd.read_sql(
    """
    SELECT SUM(valor_total) AS valor
    FROM internacoes
    WHERE municipio = ?
    """,
    conexao,
    params=(ORIGEM,)
).iloc[0]["valor"] or 0

permanencia_media = pd.read_sql(
    """
    SELECT AVG(dias_permanencia) AS media
    FROM internacoes
    WHERE municipio = ?
    """,
    conexao,
    params=(ORIGEM,)
).iloc[0]["media"] or 0

obitos = pd.read_sql(
    """
    SELECT SUM(obito) AS total
    FROM internacoes
    WHERE municipio = ?
    """,
    conexao,
    params=(ORIGEM,)
).iloc[0]["total"] or 0

# ==================================================
# PRIORIZAÇÃO / EXPLICAÇÃO (base_conhecimento) E ALERTAS
# (tendencia_estadual) -- usados por várias personas, buscados
# uma única vez aqui.
# ==================================================

base = pd.DataFrame()
erro_base = None

try:
    base = pd.read_sql(
        """
        SELECT *
        FROM base_conhecimento
        WHERE municipio = ?
        ORDER BY pontuacao_final DESC
        """,
        conexao,
        params=(ORIGEM,)
    )
except Exception as e:
    erro_base = e

eventos = pd.read_sql(
    """
    SELECT *
    FROM tendencia_estadual
    WHERE municipio = ?
    ORDER BY desvio DESC
    """,
    conexao,
    params=(ORIGEM,)
)

# ==================================================
# CONTEXTO COMPARTILHADO
#
# Todo perfil recebe o mesmo dicionário -- nenhuma função
# renderizar_* faz sua própria query de KPI, só decide o que
# mostrar e como explicar.
# ==================================================

ctx = {
    "conexao": conexao,
    "ORIGEM": ORIGEM,
    "NOME_MUNICIPIO": NOME_MUNICIPIO,
    "UF_REFERENCIA": UF_REFERENCIA,
    "municipios_disponiveis": municipios_disponiveis,
    "total": total,
    "total_municipio": total_municipio,
    "sp": sp,
    "lider": lider,
    "ranking": ranking,
    "valor_total": valor_total,
    "permanencia_media": permanencia_media,
    "obitos": obitos,
    "base": base,
    "erro_base": erro_base,
    "eventos": eventos,
}

CORES_PRIORIDADE = {
    "CRITICA": "🔴",
    "ALTA": "🟠",
    "MEDIA": "🟡",
    "BAIXA": "🟢",
}


# ==================================================
# PERFIL: CIDADÃ / POPULAÇÃO EM GERAL
#
# Linguagem simples, sem número técnico solto (pontuação, desvio
# percentual, "confiabilidade estatística") -- mesma regra que já
# vale para o modo "Simples" do chat_escudo.py.
# ==================================================

def renderizar_cidada(ctx):

    st.title("🎗️ Escudo Feminino")

    st.markdown(
        f"### Saúde da mulher em {ctx['NOME_MUNICIPIO']}"
    )

    st.write(
        f"O câncer que mais afeta as mulheres internadas pelo SUS em "
        f"**{ctx['NOME_MUNICIPIO']}** é: **{ctx['lider']}**."
    )

    st.divider()

    st.subheader("💡 O que fazer")

    if ctx["erro_base"] is not None or ctx["base"].empty:
        st.info(
            f"{ctx['NOME_MUNICIPIO']} ainda não tem essa análise "
            f"pronta. Volte mais tarde."
        )
    else:
        prioritarios = ctx["base"][
            ctx["base"]["nivel_prioridade"].isin(["CRITICA", "ALTA"])
        ]

        if prioritarios.empty:
            st.success(
                "Nenhum alerta de prioridade alta no momento para "
                f"{ctx['NOME_MUNICIPIO']}."
            )

        for _, row in prioritarios.iterrows():
            st.markdown(f"**{row['tipo_cancer']}**")
            st.write(row["recomendacao"])

    st.divider()

    st.info(
        "Quer perguntar algo específico? Abra o chat do Escudo "
        "Feminino (`python algoritimos\\chat_escudo.py`) e escolha "
        "o modo **Simples**."
    )


# ==================================================
# PERFIL: SECRETARIA DA SAÚDE DA MULHER
#
# É a visão técnica completa -- o dashboard como já existia antes
# dos perfis: indicadores, tendência, anomalias, priorização,
# comparação com o Estado e com outros municípios.
# ==================================================

def renderizar_secretaria(ctx):

    conexao = ctx["conexao"]
    ORIGEM = ctx["ORIGEM"]
    NOME_MUNICIPIO = ctx["NOME_MUNICIPIO"]
    UF_REFERENCIA = ctx["UF_REFERENCIA"]
    ranking = ctx["ranking"]

    st.title("🎗️ Escudo Feminino")

    st.markdown(f"""
    ### Sistema de Apoio à Decisão para Saúde Pública

    **{NOME_MUNICIPIO} x Estado de {UF_REFERENCIA}**
    """)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total de Registros", f"{int(ctx['total']):,}")
    col2.metric(NOME_MUNICIPIO, f"{ctx['total_municipio']:,}")
    col3.metric(f"Estado ({UF_REFERENCIA})", f"{ctx['sp']:,}")
    col4.metric("Câncer Líder", ctx["lider"])

    st.divider()

    col5, col6, col7 = st.columns(3)

    col5.metric("Valor Total", f"R$ {ctx['valor_total']:,.2f}")
    col6.metric("Permanência Média", f"{ctx['permanencia_media']:.1f} dias")
    col7.metric("Óbitos", f"{int(ctx['obitos']):,}")

    st.divider()

    st.subheader("🎯 Priorização e Recomendações")

    if ctx["erro_base"] is not None:
        st.warning(
            f"Não foi possível carregar 'base_conhecimento': "
            f"{ctx['erro_base']}. Rode "
            f"algoritimos\\base_conhecimento.py antes de abrir o "
            f"dashboard."
        )
    elif ctx["base"].empty:
        st.info(
            f"{NOME_MUNICIPIO} ainda não foi processado pela cadeia "
            f"determinística. Rode os scripts em algoritimos\\*.py com "
            f"ESCUDO_MUNICIPIO={ORIGEM} (ou o código IBGE correspondente) "
            f"para gerar esta análise."
        )
    else:
        for _, row in ctx["base"].iterrows():

            emoji = CORES_PRIORIDADE.get(row["nivel_prioridade"], "⚪")

            titulo = (
                f"{emoji} {row['tipo_cancer']} — "
                f"{row['nivel_prioridade']} "
                f"(pontuação {row['pontuacao_final']:.2f})"
            )

            with st.expander(titulo):

                st.markdown("**Por que acontece:**")
                st.write(row["motivo"])

                st.markdown("**Impacto:**")
                st.write(row["impacto"])

                st.markdown("**Recomendação:**")
                st.write(row["recomendacao"])

                avisos = []

                if row.get("confiabilidade", "OK") != "OK":
                    avisos.append(
                        f"Tendência estadual: {row['confiabilidade']}"
                    )

                if row.get("confiabilidade_anomalia", "OK") not in (
                    "OK", None
                ) and pd.notna(row.get("confiabilidade_anomalia")):
                    avisos.append(
                        f"Anomalia: {row['confiabilidade_anomalia']}"
                    )

                for aviso in avisos:
                    st.warning(aviso)

    st.divider()

    st.subheader("📋 Relatório Executivo")

    try:
        with open(
            "relatorio_executivo.txt", "r", encoding="utf-8"
        ) as arquivo:
            texto_relatorio = arquivo.read()

        with st.expander("Ver relatório executivo completo"):
            st.text(texto_relatorio)

        st.download_button(
            label="Baixar relatório executivo (.txt)",
            data=texto_relatorio,
            file_name="relatorio_executivo.txt",
            mime="text/plain"
        )

    except FileNotFoundError:
        st.info(
            "Relatório executivo ainda não foi gerado. Rode "
            "algoritimos\\relatorio_executivo.py na raiz do projeto."
        )

    st.divider()

    st.subheader("📊 Ranking dos Cânceres")

    fig_ranking = px.bar(
        ranking,
        x="tipo_cancer",
        y="total",
        color="total",
        text="total",
        title="Ranking de Internações por Tipo de Câncer"
    )

    st.plotly_chart(fig_ranking, use_container_width=True)

    comparativo = pd.read_sql(
        """
        SELECT tipo_cancer, ? AS origem, COUNT(*) AS total
        FROM internacoes
        WHERE municipio = ?
        GROUP BY tipo_cancer

        UNION ALL

        SELECT tipo_cancer, ? AS origem, COUNT(*) AS total
        FROM internacoes
        WHERE origem = ?
        GROUP BY tipo_cancer

        ORDER BY tipo_cancer
        """,
        conexao,
        params=(NOME_MUNICIPIO, ORIGEM, UF_REFERENCIA, UF_REFERENCIA)
    )

    st.subheader(f"🏥 {NOME_MUNICIPIO} x {UF_REFERENCIA}")

    fig_comparativo = px.bar(
        comparativo,
        x="tipo_cancer",
        y="total",
        color="origem",
        barmode="group"
    )

    st.plotly_chart(fig_comparativo, use_container_width=True)

    st.subheader("🏙️ Comparação direta entre municípios")

    municipios_comparacao = [
        m for m in ctx["municipios_disponiveis"]
        if m["origem"] != ORIGEM
    ]

    if not municipios_comparacao:
        st.info(
            "Não há outro município com dados carregados para "
            "comparação."
        )
    else:
        origens_comparacao = [m["origem"] for m in municipios_comparacao]

        origem_padrao = (
            "SAO_JOSE_DO_RIO_PRETO"
            if ORIGEM == "RIO_CLARO"
            and "SAO_JOSE_DO_RIO_PRETO" in origens_comparacao
            else origens_comparacao[0]
        )

        indice_padrao = origens_comparacao.index(origem_padrao)

        municipio_comparado_nome = st.selectbox(
            "Comparar com",
            [m["nome"] for m in municipios_comparacao],
            index=indice_padrao,
            key="municipio_comparacao"
        )

        municipio_comparado = next(
            m for m in municipios_comparacao
            if m["nome"] == municipio_comparado_nome
        )

        ORIGEM_COMPARADA = municipio_comparado["origem"]

        indicadores_comparacao = pd.read_sql(
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
            params=(ORIGEM, ORIGEM_COMPARADA)
        )

        nomes_municipios = {
            ORIGEM: NOME_MUNICIPIO,
            ORIGEM_COMPARADA: municipio_comparado_nome
        }

        indicadores_comparacao["municipio"] = (
            indicadores_comparacao["municipio"].map(nomes_municipios)
        )

        indicadores_comparacao["taxa_obitos_%"] = (
            indicadores_comparacao["obitos"]
            / indicadores_comparacao["internacoes"].replace(0, pd.NA)
            * 100
        ).fillna(0)

        indicadores_comparacao = indicadores_comparacao.rename(columns={
            "municipio": "Município",
            "internacoes": "Internações",
            "obitos": "Óbitos",
            "taxa_obitos_%": "Óbitos / Internações (%)",
            "valor_total": "Valor Total (R$)",
            "permanencia_media": "Permanência Média (dias)"
        })

        st.dataframe(
            indicadores_comparacao[
                [
                    "Município",
                    "Internações",
                    "Óbitos",
                    "Óbitos / Internações (%)",
                    "Valor Total (R$)",
                    "Permanência Média (dias)"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        cancer_comparacao = pd.read_sql(
            """
            SELECT
                municipio,
                tipo_cancer,
                COUNT(*) AS total
            FROM internacoes
            WHERE municipio IN (?, ?)
            GROUP BY municipio, tipo_cancer
            ORDER BY tipo_cancer
            """,
            conexao,
            params=(ORIGEM, ORIGEM_COMPARADA)
        )

        cancer_comparacao["municipio"] = cancer_comparacao["municipio"].map(
            nomes_municipios
        )

        fig_municipios = px.bar(
            cancer_comparacao,
            x="tipo_cancer",
            y="total",
            color="municipio",
            barmode="group",
            title=(
                f"Internações por tipo de câncer — "
                f"{NOME_MUNICIPIO} x {municipio_comparado_nome}"
            )
        )

        st.plotly_chart(fig_municipios, use_container_width=True)

    st.divider()

    st.subheader("📈 Evolução Temporal")

    cancer_escolhido = st.selectbox(
        "Selecione o câncer",
        ranking["tipo_cancer"].tolist()
    )

    evolucao = pd.read_sql(
        """
        SELECT
            ano,
            COUNT(*) AS internacoes
        FROM internacoes
        WHERE tipo_cancer = ? AND municipio = ?
        GROUP BY ano
        ORDER BY ano
        """,
        conexao,
        params=(cancer_escolhido, ORIGEM)
    )

    fig_evolucao = px.line(
        evolucao,
        x="ano",
        y="internacoes",
        markers=True,
        title=f"Evolução Temporal - {cancer_escolhido} ({NOME_MUNICIPIO})"
    )

    st.plotly_chart(fig_evolucao, use_container_width=True)

    st.subheader("🚨 Alertas Analíticos")

    if ctx["eventos"].empty:
        st.info(
            f"{NOME_MUNICIPIO} ainda não foi processado pela cadeia "
            f"determinística (tendencia_estadual). Rode "
            f"algoritimos\\tendencia_estadual.py com "
            f"ESCUDO_MUNICIPIO={ORIGEM} para gerar esta análise."
        )

    for _, row in ctx["eventos"].iterrows():

        mensagem = f"{row['tipo_cancer']} ({row['desvio']:.2f}%)"

        if row.get("confiabilidade", "OK") != "OK":
            mensagem += f" — ⚠️ {row['confiabilidade']}"

        if row["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL":
            st.error(mensagem)
        elif row["evento"] == "ABAIXO_DA_TENDENCIA_ESTADUAL":
            st.success(mensagem)
        else:
            st.info(mensagem)


# ==================================================
# PERFIL: PREFEITURA / GESTOR MUNICIPAL
#
# Visão executiva: quais problemas estão chamando mais atenção
# agora e o que fazer -- sem tabela crua, sem gráfico de dispersão.
# ==================================================

def renderizar_prefeitura(ctx):

    NOME_MUNICIPIO = ctx["NOME_MUNICIPIO"]

    st.title("🎗️ Escudo Feminino")

    st.markdown(f"### Visão executiva — {NOME_MUNICIPIO}")

    col1, col2, col3 = st.columns(3)

    col1.metric("Internações (total)", f"{ctx['total_municipio']:,}")
    col2.metric("Óbitos", f"{int(ctx['obitos']):,}")
    col3.metric("Câncer líder", ctx["lider"])

    st.divider()

    st.subheader("🎯 Prioridades que exigem atenção agora")

    if ctx["erro_base"] is not None or ctx["base"].empty:
        st.info(
            f"{NOME_MUNICIPIO} ainda não foi processado pela cadeia "
            f"determinística."
        )
    else:
        prioritarios = ctx["base"][
            ctx["base"]["nivel_prioridade"].isin(["CRITICA", "ALTA"])
        ]

        if prioritarios.empty:
            st.success("Nenhuma prioridade crítica ou alta no momento.")

        for _, row in prioritarios.iterrows():
            emoji = CORES_PRIORIDADE.get(row["nivel_prioridade"], "⚪")
            st.markdown(f"**{emoji} {row['tipo_cancer']} — {row['nivel_prioridade']}**")
            st.write(row["recomendacao"])

    st.divider()

    st.subheader("🚨 Alertas ativos")

    alertas_ativos = ctx["eventos"][
        ctx["eventos"]["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL"
    ] if not ctx["eventos"].empty else ctx["eventos"]

    if alertas_ativos.empty:
        st.success("Nenhum indicador acima da tendência estadual.")
    else:
        for _, row in alertas_ativos.iterrows():
            st.error(f"{row['tipo_cancer']} — {row['desvio']:.2f}% acima da tendência do Estado")

    st.divider()

    try:
        with open(
            "relatorio_executivo.txt", "r", encoding="utf-8"
        ) as arquivo:
            texto_relatorio = arquivo.read()

        st.download_button(
            label="📋 Baixar relatório executivo (.txt)",
            data=texto_relatorio,
            file_name="relatorio_executivo.txt",
            mime="text/plain"
        )

    except FileNotFoundError:
        st.info(
            "Relatório executivo ainda não foi gerado. Rode "
            "algoritimos\\relatorio_executivo.py."
        )


# ==================================================
# PERFIL: OPERADORA DE PLANO DE SAÚDE
#
# Perfil assistencial: internações, permanência, custo e
# distribuição etária -- não prioridade de política pública.
# ==================================================

def renderizar_operadora(ctx):

    conexao = ctx["conexao"]
    NOME_MUNICIPIO = ctx["NOME_MUNICIPIO"]

    st.title("🎗️ Escudo Feminino")

    st.markdown(f"### Perfil assistencial — {NOME_MUNICIPIO}")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Internações", f"{ctx['total_municipio']:,}")
    col2.metric("Permanência Média", f"{ctx['permanencia_media']:.1f} dias")
    col3.metric("Custo Total", f"R$ {ctx['valor_total']:,.2f}")
    col4.metric("Óbitos", f"{int(ctx['obitos']):,}")

    st.divider()

    st.subheader("📊 Internações por tipo de câncer")

    fig_ranking = px.bar(
        ctx["ranking"],
        x="tipo_cancer",
        y="total",
        color="total",
        text="total"
    )

    st.plotly_chart(fig_ranking, use_container_width=True)

    st.subheader("👥 Distribuição por faixa etária")

    faixa_etaria = ler_tabela_municipio(
        "faixa_etaria", conexao, municipio=ctx["ORIGEM"]
    )

    if faixa_etaria.empty:
        st.info(
            f"{NOME_MUNICIPIO} ainda não tem a tabela `faixa_etaria` "
            f"processada. Rode algoritimos\\faixa_etaria.py com "
            f"ESCUDO_MUNICIPIO={ctx['ORIGEM']}."
        )
    else:
        fig_faixa = px.bar(
            faixa_etaria,
            x="faixa_etaria",
            y="internacoes",
            color="tipo_cancer",
            barmode="group",
            title="Internações por faixa etária e tipo de câncer"
        )
        st.plotly_chart(fig_faixa, use_container_width=True)


# ==================================================
# PERFIL: INVESTIDOR
#
# Foco em mercado/demanda, não em urgência de política pública.
# Ressalva sempre visível: dados são só de internações do SUS, não
# capturam quem já usa rede privada.
# ==================================================

def renderizar_investidor(ctx):

    NOME_MUNICIPIO = ctx["NOME_MUNICIPIO"]

    st.title("🎗️ Escudo Feminino")

    st.markdown(f"### Panorama de mercado — {NOME_MUNICIPIO}")

    st.warning(
        "Esta base cobre **apenas internações pelo SUS** (sistema "
        "público). Não captura demanda de quem já usa rede privada "
        "de saúde -- trate os números abaixo como piso da demanda "
        "real, não como o mercado total."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Internações (SUS)", f"{ctx['total_municipio']:,}")
    col2.metric("Maior demanda por tipo", ctx["lider"])
    col3.metric(
        f"Comparação com {ctx['UF_REFERENCIA']}",
        f"{ctx['total_municipio']:,} / {ctx['sp']:,}"
    )

    st.divider()

    st.subheader("📊 Demanda por tipo de câncer")

    fig_ranking = px.bar(
        ctx["ranking"],
        x="tipo_cancer",
        y="total",
        color="total",
        text="total",
        title="Internações por tipo de câncer (proxy de demanda)"
    )

    st.plotly_chart(fig_ranking, use_container_width=True)

    st.subheader("📈 Tendência frente ao Estado")

    if ctx["eventos"].empty:
        st.info(
            f"{NOME_MUNICIPIO} ainda não tem a análise de tendência "
            f"processada."
        )
    else:
        crescendo = ctx["eventos"][
            ctx["eventos"]["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL"
        ]

        if crescendo.empty:
            st.info(
                "Nenhum tipo de câncer com internações crescendo "
                "acima da tendência estadual no momento."
            )
        else:
            for _, row in crescendo.iterrows():
                st.write(
                    f"📈 **{row['tipo_cancer']}**: "
                    f"{row['desvio']:.2f}% acima da tendência do "
                    f"Estado -- possível sinal de demanda em alta."
                )


# ==================================================
# DESPACHO POR PERFIL
# ==================================================

PERFIS = {
    "cidada": renderizar_cidada,
    "secretaria": renderizar_secretaria,
    "prefeitura": renderizar_prefeitura,
    "operadora": renderizar_operadora,
    "investidor": renderizar_investidor,
}

PERFIS[perfil_atual](ctx)

# ==================================================
# FECHAMENTO DA CONEXÃO
# ==================================================

conexao.close()
