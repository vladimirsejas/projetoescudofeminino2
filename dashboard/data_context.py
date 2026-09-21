
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


def construir_contexto(origem, tipo_cancer=None):
    conexao = conectar()
    try:
        filtros = ["municipio = ?"]
        parametros = [origem]

        if tipo_cancer:
            filtros.append("tipo_cancer = ?")
            parametros.append(tipo_cancer)

        where = " AND ".join(filtros)

        resumo = pd.read_sql(
            f"""
            SELECT
                COUNT(*) AS internacoes,
                COALESCE(SUM(obito), 0) AS obitos,
                COALESCE(SUM(valor_total), 0) AS valor_total,
                COALESCE(AVG(dias_permanencia), 0) AS permanencia_media
            FROM internacoes
            WHERE {where}
            """,
            conexao,
            params=parametros,
        ).iloc[0]

        ranking = pd.read_sql(
            f"""
            SELECT
                tipo_cancer,
                COUNT(*) AS total
            FROM internacoes
            WHERE {where}
            GROUP BY tipo_cancer
            ORDER BY total DESC
            """,
            conexao,
            params=parametros,
        )

        previsoes = _ler_tabela(conexao, "previsao_temporal", origem, tipo_cancer)
        previsoes_horizontes = _ler_tabela(
            conexao, "previsao_temporal_horizontes", origem, tipo_cancer
        )
        serie_temporal = _ler_tabela(conexao, "serie_temporal_anual", origem, tipo_cancer)
        if "grupo" in serie_temporal.columns:
            serie_temporal = serie_temporal[
                serie_temporal["grupo"] == "MUNICIPIO"
            ].copy()
        tendencias = _ler_tabela(conexao, "tendencia_estadual", origem, tipo_cancer)
        base = _ler_tabela(conexao, "base_conhecimento", origem, tipo_cancer)

        return {
            "conexao": conexao,
            "origem": origem,
            "tipo_cancer": tipo_cancer,
            "internacoes": int(resumo["internacoes"] or 0),
            "obitos": int(resumo["obitos"] or 0),
            "mortalidade_pct": (
                round(int(resumo["obitos"] or 0) / int(resumo["internacoes"] or 1) * 100, 1)
                if int(resumo["internacoes"] or 0) > 0
                else 0.0
            ),
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


def _ler_tabela(conexao, tabela, origem, tipo_cancer=None):
    try:
        df = pd.read_sql(
            f"SELECT * FROM {tabela} WHERE municipio = ?",
            conexao,
            params=(origem,),
        )
        if tipo_cancer and "tipo_cancer" in df.columns:
            df = df[df["tipo_cancer"] == tipo_cancer].copy()
        return df
    except Exception:
        return pd.DataFrame()


def fechar_contexto(ctx):
    conexao = ctx.get("conexao")
    if conexao is not None:
        conexao.close()
