import os
import sqlite3
import sys
import tempfile

# =====================================
# TESTE DA SÉRIE TEMPORAL ANUAL
#
# Roda serie_temporal.py de verdade, mas contra um banco sqlite
# temporário e sintético, provando duas coisas:
#   - a série cobre corretamente vários anos espalhados (não só
#     2024/2025, como tendencia_estadual.py faz);
#   - salvar_tabela_municipio() não apaga dados de outro município
#     já processado (regra multi-tenant do projeto).
# =====================================

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ORIGINAL = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"


def _montar_banco(caminho):

    conexao = sqlite3.connect(caminho)

    conexao.execute("""
        CREATE TABLE internacoes (
            tipo_cancer TEXT, origem TEXT, municipio TEXT, codigo_ibge INTEGER,
            ano INTEGER, idade INTEGER, dias_permanencia INTEGER,
            obito INTEGER, valor_total REAL
        )
    """)

    linhas = []

    # RIO_CLARO/MAMA em 3 anos espalhados no tempo (2013, 2020, 2025),
    # simulando a série ampliada que motivou este script -- 2
    # internações/1 óbito em cada ano, números fáceis de conferir.
    for ano in (2013, 2020, 2025):
        linhas.append(
            ("MAMA", "RIO_CLARO", "RIO_CLARO", 3543907, ano, 55, 5, 1, 1000.0)
        )
        linhas.append(
            ("MAMA", "RIO_CLARO", "RIO_CLARO", 3543907, ano, 60, 5, 0, 1000.0)
        )

    # referência estadual só existe em 2020 neste banco sintético,
    # sem óbito -- prova que a série não inventa linhas para anos
    # sem dado de SP.
    linhas.append(("MAMA", "SP", "ESTADO_SP", None, 2020, 50, 5, 0, 1000.0))
    linhas.append(("MAMA", "SP", "ESTADO_SP", None, 2020, 50, 5, 0, 1000.0))

    conexao.executemany(
        "INSERT INTO internacoes VALUES (?,?,?,?,?,?,?,?,?)", linhas
    )

    # tabela derivada já existente com uma linha de outro município,
    # para provar que rodar para RIO_CLARO não apaga LIMEIRA.
    conexao.execute("""
        CREATE TABLE serie_temporal_anual (
            tipo_cancer TEXT, grupo TEXT, ano INTEGER,
            internacoes INTEGER, obitos INTEGER, taxa_mortalidade REAL,
            municipio TEXT
        )
    """)
    conexao.execute(
        "INSERT INTO serie_temporal_anual VALUES "
        "('MAMA', 'MUNICIPIO', 2020, 9, 0, 0.0, 'LIMEIRA')"
    )

    conexao.commit()
    conexao.close()


def _rodar_script(caminho_banco, municipio_env):

    caminho_script = os.path.join(DIRETORIO_ATUAL, "serie_temporal.py")
    codigo_fonte = open(caminho_script, encoding="utf-8-sig").read()

    codigo_fonte = codigo_fonte.replace(
        CAMINHO_ORIGINAL, caminho_banco.replace("\\", "\\\\")
    )

    os.environ["ESCUDO_MUNICIPIO"] = municipio_env

    if "configuracao_geografica" in sys.modules:
        sys.modules["configuracao_geografica"].BANCO = caminho_banco

    exec(
        compile(codigo_fonte, "serie_temporal.py", "exec"),
        {"__name__": "__teste_serie_temporal__"}
    )


def testar():

    falhas = []

    def checar(descricao, condicao):
        status = "OK" if condicao else "FALHOU"
        print(f"[{status}] {descricao}")
        if not condicao:
            falhas.append(descricao)

    fd, banco = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        _montar_banco(banco)
        _rodar_script(banco, "RIO_CLARO")

        conexao = sqlite3.connect(banco)
        linhas = conexao.execute(
            "SELECT tipo_cancer, grupo, ano, internacoes, obitos, "
            "round(taxa_mortalidade, 2), municipio "
            "FROM serie_temporal_anual ORDER BY municipio, grupo, ano"
        ).fetchall()
        conexao.close()

        checar(
            "linha de outro município (LIMEIRA) sobrevive à gravação",
            ("MAMA", "MUNICIPIO", 2020, 9, 0, 0.0, "LIMEIRA") in linhas
        )

        anos_rio_claro = {
            linha[2] for linha in linhas
            if linha[6] == "RIO_CLARO" and linha[1] == "MUNICIPIO"
        }
        checar(
            "série de RIO_CLARO cobre os 3 anos espalhados "
            "(2013, 2020, 2025)",
            anos_rio_claro == {2013, 2020, 2025}
        )

        checar(
            "RIO_CLARO/MAMA/2025 tem 2 internações, 1 óbito, taxa 50%",
            ("MAMA", "MUNICIPIO", 2025, 2, 1, 50.0, "RIO_CLARO") in linhas
        )

        checar(
            "grupo SP aparece no ano com dado (2020), 2 internações, "
            "0 óbito",
            ("MAMA", "SP", 2020, 2, 0, 0.0, "RIO_CLARO") in linhas
        )

        checar(
            "grupo SP não aparece em anos sem dado estadual "
            "(2013 e 2025)",
            not any(
                linha[1] == "SP" and linha[2] in (2013, 2025)
                for linha in linhas
                if linha[6] == "RIO_CLARO"
            )
        )

    finally:
        os.remove(banco)

    if falhas:
        raise SystemExit(f"{len(falhas)} checagem(ns) falharam: {falhas}")

    print("\nTodas as checagens da série temporal anual passaram.")


if __name__ == "__main__":
    testar()
