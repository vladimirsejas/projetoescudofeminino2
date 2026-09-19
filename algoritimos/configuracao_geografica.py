import os
import sqlite3

import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

MUNICIPIO_PADRAO = "RIO_CLARO"
UF_REFERENCIA = "SP"


def _conectar():
    return sqlite3.connect(BANCO)


def _buscar_origem_por_codigo_ibge(codigo_ibge):
    conexao = _conectar()
    try:
        linha = conexao.execute(
            "SELECT origem FROM municipios WHERE codigo_ibge = ?",
            (codigo_ibge,)
        ).fetchone()
        return linha[0] if linha else None
    except sqlite3.OperationalError:
        return None
    finally:
        conexao.close()


def obter_municipio():
    valor = os.getenv("ESCUDO_MUNICIPIO", MUNICIPIO_PADRAO).strip()
    if valor.isdigit():
        origem = _buscar_origem_por_codigo_ibge(int(valor))
        return (origem or MUNICIPIO_PADRAO).upper()
    return valor.upper()


def _buscar_metadados_municipio(origem=None):
    origem = origem or obter_municipio()
    conexao = _conectar()
    try:
        return conexao.execute(
            "SELECT codigo_ibge, nome, uf FROM municipios WHERE origem = ?",
            (origem,)
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    finally:
        conexao.close()


def obter_codigo_ibge():
    linha = _buscar_metadados_municipio()
    return linha[0] if linha else None


def obter_nome_municipio():
    linha = _buscar_metadados_municipio()
    if linha:
        return linha[1]
    return obter_municipio().replace("_", " ").title()


def obter_uf():
    linha = _buscar_metadados_municipio()
    return linha[2] if linha else UF_REFERENCIA


def listar_municipios_disponiveis():
    conexao = _conectar()
    try:
        linhas = conexao.execute("""
            SELECT DISTINCT
                m.codigo_ibge,
                m.origem,
                m.nome,
                m.uf
            FROM municipios AS m
            INNER JOIN internacoes AS i
                ON i.municipio = m.origem
            WHERE m.uf = ?
            ORDER BY m.nome
        """, (UF_REFERENCIA,)).fetchall()
        return [
            {
                "codigo_ibge": linha[0],
                "origem": linha[1],
                "nome": linha[2],
                "uf": linha[3]
            }
            for linha in linhas
        ]
    except sqlite3.OperationalError:
        return []
    finally:
        conexao.close()


def nome_coluna_municipio(df):
    municipio = obter_municipio()
    if municipio in df.columns:
        return municipio
    if MUNICIPIO_PADRAO in df.columns:
        return MUNICIPIO_PADRAO
    return None


def salvar_tabela_municipio(df, nome_tabela, conexao, municipio=None):
    municipio = municipio or obter_municipio()
    df = df.copy()
    df["municipio"] = municipio
    cursor = conexao.cursor()
    tabela_existe = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (nome_tabela,)
    ).fetchone()
    if tabela_existe:
        colunas_existentes = [
            linha[1] for linha in cursor.execute(f"PRAGMA table_info({nome_tabela})")
        ]
        if "municipio" not in colunas_existentes:
            cursor.execute(f"ALTER TABLE {nome_tabela} ADD COLUMN municipio TEXT")
        cursor.execute(
            f"DELETE FROM {nome_tabela} WHERE municipio = ? OR municipio IS NULL",
            (municipio,)
        )
        conexao.commit()
    df.to_sql(nome_tabela, conexao, if_exists="append", index=False)


def ler_tabela_municipio(nome_tabela, conexao, municipio=None, colunas="*"):
    municipio = municipio or obter_municipio()
    try:
        return pd.read_sql(
            f"SELECT {colunas} FROM {nome_tabela} WHERE municipio = ?",
            conexao,
            params=(municipio,)
        )
    except Exception:
        return pd.DataFrame()
