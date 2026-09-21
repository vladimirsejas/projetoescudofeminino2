import os
import sqlite3
import tempfile
import sys

import pandas as pd

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(DIRETORIO_ATUAL)
ALG_DIR = os.path.join(PROJECT_DIR, "algoritimos")

for caminho in (PROJECT_DIR, ALG_DIR):
    if caminho not in sys.path:
        sys.path.insert(0, caminho)

from dashboard import data_context  # noqa: E402


def testar():
    fd, banco = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        conexao = sqlite3.connect(banco)

        conexao.execute(
            """
            CREATE TABLE internacoes (
                municipio TEXT,
                tipo_cancer TEXT,
                obito INTEGER,
                valor_total REAL,
                dias_permanencia REAL
            )
            """
        )
        conexao.executemany(
            "INSERT INTO internacoes VALUES (?, ?, ?, ?, ?)",
            [
                ("RIO_CLARO", "MAMA", 1, 100.0, 5.0),
                ("RIO_CLARO", "MAMA", 0, 200.0, 7.0),
                ("RIO_CLARO", "COLORRETAL", 0, 300.0, 4.0),
                ("LIMEIRA", "MAMA", 0, 500.0, 8.0),
            ],
        )

        for tabela in [
            "previsao_temporal",
            "previsao_temporal_horizontes",
            "serie_temporal_anual",
            "tendencia_estadual",
            "base_conhecimento",
        ]:
            if tabela == "serie_temporal_anual":
                conexao.execute(
                    """
                    CREATE TABLE serie_temporal_anual (
                        tipo_cancer TEXT,
                        grupo TEXT,
                        ano INTEGER,
                        internacoes INTEGER,
                        obitos INTEGER,
                        taxa_mortalidade REAL,
                        municipio TEXT
                    )
                    """
                )
                conexao.executemany(
                    "INSERT INTO serie_temporal_anual VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        ("MAMA", "MUNICIPIO", 2024, 1, 0, 0.0, "RIO_CLARO"),
                        ("MAMA", "MUNICIPIO", 2025, 2, 1, 50.0, "RIO_CLARO"),
                        ("COLORRETAL", "MUNICIPIO", 2025, 1, 0, 0.0, "RIO_CLARO"),
                        ("MAMA", "SP", 2025, 999, 20, 2.0, "RIO_CLARO"),
                        ("MAMA", "MUNICIPIO", 2025, 9, 0, 0.0, "LIMEIRA"),
                    ],
                )
            elif tabela in ("previsao_temporal", "previsao_temporal_horizontes"):
                conexao.execute(
                    f"""
                    CREATE TABLE {tabela} (
                        tipo_cancer TEXT,
                        ano_previsto INTEGER,
                        internacoes_previstas REAL,
                        municipio TEXT
                    )
                    """
                )
            elif tabela == "tendencia_estadual":
                conexao.execute(
                    """
                    CREATE TABLE tendencia_estadual (
                        tipo_cancer TEXT,
                        desvio REAL,
                        evento TEXT,
                        municipio TEXT
                    )
                    """
                )
            else:
                conexao.execute(
                    """
                    CREATE TABLE base_conhecimento (
                        tipo_cancer TEXT,
                        nivel_prioridade TEXT,
                        motivo TEXT,
                        impacto TEXT,
                        recomendacao TEXT,
                        municipio TEXT
                    )
                    """
                )

        conexao.commit()
        conexao.close()

        data_context.BANCO = banco

        doencas = data_context.listar_cancers_disponiveis("RIO_CLARO")
        assert doencas == ["COLORRETAL", "MAMA"]

        ctx = data_context.construir_contexto("RIO_CLARO", "MAMA")

        assert ctx["internacoes"] == 2
        assert ctx["obitos"] == 1
        assert ctx["mortalidade_pct"] == 50.0
        assert round(ctx["valor_total"], 1) == 300.0
        assert round(ctx["permanencia_media"], 1) == 6.0

        assert set(ctx["ranking"]["tipo_cancer"]) == {"MAMA"}
        assert set(ctx["serie_temporal"]["tipo_cancer"]) == {"MAMA"}
        assert set(ctx["serie_temporal"]["grupo"]) == {"MUNICIPIO"}
        assert ctx["serie_temporal"]["internacoes"].sum() == 3

        ctx_limeira = data_context.construir_contexto("LIMEIRA", "MAMA")
        assert ctx_limeira["internacoes"] == 1

        print("11/11 checagens do contexto da interface passaram.")

    finally:
        if os.path.exists(banco):
            os.remove(banco)


if __name__ == "__main__":
    testar()
