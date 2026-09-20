import sqlite3

from padroes_analiticos import (
    gerar_padroes_analiticos,
    formatar_contexto_padroes,
)


def criar_banco_teste():
    conn = sqlite3.connect(":memory:")

    conn.execute(
        """
        CREATE TABLE internacoes (
            tipo_cancer TEXT,
            municipio TEXT,
            obito INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE tendencia_estadual (
            tipo_cancer TEXT,
            municipio TEXT,
            variacao_municipio REAL,
            variacao_sp REAL,
            desvio REAL,
            evento TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE anomalias (
            tipo_cancer TEXT,
            municipio TEXT,
            valor_2025 INTEGER,
            desvio_percentual REAL,
            situacao TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE priorizacao_executiva (
            tipo_cancer TEXT,
            municipio TEXT,
            nivel_prioridade TEXT,
            pontuacao_final REAL
        )
        """
    )

    conn.executemany(
        "INSERT INTO internacoes VALUES (?, ?, ?)",
        [
            ("MAMA", "RIO_CLARO", 0),
            ("MAMA", "RIO_CLARO", 0),
            ("MAMA", "RIO_CLARO", 0),
            ("MAMA", "RIO_CLARO", 1),
            ("PULMAO", "RIO_CLARO", 1),
            ("PULMAO", "RIO_CLARO", 1),
            ("COLORRETAL", "RIO_CLARO", 0),
            ("COLORRETAL", "RIO_CLARO", 0),
        ],
    )

    conn.execute(
        """
        INSERT INTO tendencia_estadual VALUES
        ('PULMAO', 'RIO_CLARO', 40.0, 10.0, 30.0,
         'ACIMA_DA_TENDENCIA_ESTADUAL')
        """
    )
    conn.execute(
        """
        INSERT INTO anomalias VALUES
        ('MAMA', 'RIO_CLARO', 20, 60.0, 'ANOMALIA_POSITIVA')
        """
    )
    conn.execute(
        """
        INSERT INTO priorizacao_executiva VALUES
        ('PULMAO', 'RIO_CLARO', 'ALTA', 75.0)
        """
    )
    conn.commit()
    return conn


def main():
    conn = criar_banco_teste()

    resultado = gerar_padroes_analiticos(
        conn, "RIO_CLARO", "Rio Claro"
    )

    tipos = {p["tipo"] for p in resultado["padroes"]}

    assert "MAIOR_VOLUME" in tipos
    assert "MAIOR_MORTALIDADE_HOSPITALAR" in tipos
    assert "CRUZAMENTO_VOLUME_MORTALIDADE" in tipos
    assert "ACIMA_DA_TENDENCIA_ESTADUAL" in tipos
    assert "ANOMALIA" in tipos
    assert "PRIORIDADE_ALTA_OU_CRITICA" in tipos

    maior_volume = next(
        p for p in resultado["padroes"]
        if p["tipo"] == "MAIOR_VOLUME"
    )
    assert maior_volume["cancer"] == "MAMA"

    assert resultado["evidencias"]

    contexto = formatar_contexto_padroes(resultado)

    assert "CAMADA DE PADRÕES ANALÍTICOS" in contexto
    assert "Rio Claro" in contexto
    assert "mortalidade hospitalar" in contexto
    assert "Não representam causalidade" in contexto

    conn.close()
    print("TESTE PADROES ANALITICOS: TODAS AS CHECAGENS PASSARAM.")


if __name__ == "__main__":
    main()
