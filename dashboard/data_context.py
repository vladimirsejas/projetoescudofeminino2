
import sqlite3

import pandas as pd

from configuracao_geografica import listar_municipios_disponiveis, UF_REFERENCIA

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"


def conectar():
    return sqlite3.connect(BANCO)


def listar_municipios():
    return listar_municipios_disponiveis()


def listar_cancers_disponiveis(origem):
    conexao = conectar()
    try:
        df = pd.read_sql(
            """
            SELECT DISTINCT tipo_cancer
            FROM internacoes
            WHERE municipio = ?
              AND tipo_cancer IS NOT NULL
            ORDER BY tipo_cancer
            """,
            conexao,
            params=(origem,),
        )
        return df["tipo_cancer"].tolist()
    finally:
        conexao.close()


def construir_contexto(origem):
    conexao = conectar()
    try:
        resumo = pd.read_sql(
            """
            SELECT
                COUNT(*) AS internacoes,
                COALESCE(SUM(obito), 0) AS obitos,
                COALESCE(SUM(valor_total), 0) AS valor_total,
                COALESCE(AVG(dias_permanencia), 0) AS permanencia_media
            FROM internacoes
            WHERE municipio = ?
            """,
            conexao,
            params=(origem,),
        ).iloc[0]

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
            params=(origem,),
        )

        previsoes = _ler_tabela(conexao, "previsao_temporal", origem)
        previsoes_horizontes = _ler_tabela(
            conexao, "previsao_temporal_horizontes", origem
        )
        serie_temporal = _ler_tabela(conexao, "serie_temporal_anual", origem)
        tendencias = _ler_tabela(conexao, "tendencia_estadual", origem)
        base = _ler_tabela(conexao, "base_conhecimento", origem)

        return {
            "conexao": conexao,
            "origem": origem,
            "internacoes": int(resumo["internacoes"] or 0),
            "obitos": int(resumo["obitos"] or 0),
            "valor_total": float(resumo["valor_total"] or 0),
            "permanencia_media": float(resumo["permanencia_media"] or 0),
            "ranking": ranking,
            "lider": (
                str(ranking.iloc[0]["tipo_cancer"])
                if not ranking.empty
                else "—"
            ),
            "previsoes": previsoes,
            "previsoes_horizontes": previsoes_horizontes,
            "serie_temporal": serie_temporal,
            "tendencias": tendencias,
            "base": base,
            "uf_referencia": UF_REFERENCIA,
        }
    except Exception:
        conexao.close()
        raise


def _ler_tabela(conexao, tabela, origem):
    try:
        return pd.read_sql(
            f"SELECT * FROM {tabela} WHERE municipio = ?",
            conexao,
            params=(origem,),
        )
    except Exception:
        return pd.DataFrame()


def fechar_contexto(ctx):
    conexao = ctx.get("conexao")
    if conexao is not None:
        conexao.close()
