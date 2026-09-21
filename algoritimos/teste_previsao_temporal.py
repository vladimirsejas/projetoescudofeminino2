import os
import sqlite3
import sys
import tempfile

import pandas as pd

# =====================================
# TESTE DA PREVISÃO TEMPORAL SIMPLES
#
# Três camadas de checagem:
#   1. calcular_previsao_serie() isolada, com séries fabricadas --
#      prova a lógica de validação/confiabilidade em casos que não
#      aparecem naturalmente no banco (amostra mínima, erro alto).
#   2. Execução real do script contra um banco sqlite temporário,
#      provando que ele lê serie_temporal_anual, grava
#      previsao_temporal e respeita a regra multi-tenant.
#   3. Sanidade contra dado histórico real (não sintético) --
#      analises/base_preditiva_2013_2025.csv, 13 anos por câncer em
#      Rio Claro -- para garantir que a função não quebra nem produz
#      número absurdo quando alimentada com ruído de verdade, não só
#      com série fabricada e bem-comportada.
# =====================================

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ORIGINAL = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

sys.path.insert(0, DIRETORIO_ATUAL)

from previsao_temporal import (  # noqa: E402
    calcular_previsao_serie,
    gerar_previsao_municipio,
)


def testar_calculo_isolado(checar):

    # menos anos que o mínimo para prever
    r = calcular_previsao_serie([2023, 2024], [10, 12])
    checar(
        "menos anos que o mínimo -> AMOSTRA_INSUFICIENTE, sem previsão",
        r["internacoes_previstas"] is None
        and r["confiabilidade"].startswith("AMOSTRA_INSUFICIENTE")
    )

    # 3 anos: dá para prever, mas não dá para validar (mínimo é 4)
    r = calcular_previsao_serie([2023, 2024, 2025], [10, 12, 14])
    checar(
        "3 anos -> prevê, mas confiabilidade é NAO_VALIDADO",
        r["internacoes_previstas"] is not None
        and r["confiabilidade"].startswith("NAO_VALIDADO")
    )

    # tendência linear perfeita e crescente -> validação deve acertar
    # em cheio (erro ~0%) e confiabilidade OK
    anos = [2020, 2021, 2022, 2023, 2024, 2025]
    internacoes = [10, 20, 30, 40, 50, 60]
    r = calcular_previsao_serie(anos, internacoes)
    checar(
        "tendência linear perfeita -> confiabilidade OK",
        r["confiabilidade"] == "OK"
    )
    checar(
        "tendência linear perfeita -> previsão 2026 é 70",
        r["ano_previsto"] == 2026 and abs(r["internacoes_previstas"] - 70) < 0.01
    )

    # série com quebra abrupta no último ano -> a reta ajustada nos
    # anos anteriores erra feio o holdout -> BAIXA_CONFIABILIDADE
    anos = [2020, 2021, 2022, 2023, 2024, 2025]
    internacoes = [10, 12, 11, 13, 12, 80]
    r = calcular_previsao_serie(anos, internacoes)
    checar(
        "quebra abrupta no último ano -> BAIXA_CONFIABILIDADE",
        r["confiabilidade"].startswith("BAIXA_CONFIABILIDADE")
    )

    # previsão nunca é negativa mesmo com tendência de queda acentuada
    anos = [2021, 2022, 2023, 2024, 2025]
    internacoes = [50, 40, 30, 20, 10]
    r = calcular_previsao_serie(anos, internacoes)
    checar(
        "tendência de queda acentuada -> previsão nunca negativa",
        r["internacoes_previstas"] >= 0
    )


def testar_agrupamento_por_cancer(checar):

    serie_df = pd.DataFrame([
        {"tipo_cancer": "MAMA", "grupo": "MUNICIPIO", "ano": ano,
         "internacoes": 10 + ano - 2020}
        for ano in range(2020, 2026)
    ] + [
        {"tipo_cancer": "MAMA", "grupo": "SP", "ano": ano,
         "internacoes": 1000 + ano}
        for ano in range(2020, 2026)
    ] + [
        {"tipo_cancer": "COLO_UTERO", "grupo": "MUNICIPIO", "ano": ano,
         "internacoes": 5}
        for ano in range(2020, 2026)
    ])

    resultado = gerar_previsao_municipio(serie_df)

    checar(
        "gera uma linha por câncer, ignorando a série de SP",
        set(resultado["tipo_cancer"]) == {"MAMA", "COLO_UTERO"}
        and len(resultado) == 2
    )


def testar_execucao_real_multi_tenant(checar):

    fd, banco = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        conexao = sqlite3.connect(banco)

        conexao.execute("""
            CREATE TABLE serie_temporal_anual (
                tipo_cancer TEXT, grupo TEXT, ano INTEGER,
                internacoes INTEGER, obitos INTEGER,
                taxa_mortalidade REAL, municipio TEXT
            )
        """)

        for ano in range(2013, 2026):
            conexao.execute(
                "INSERT INTO serie_temporal_anual VALUES "
                "('MAMA', 'MUNICIPIO', ?, ?, 1, 5.0, 'RIO_CLARO')",
                (ano, 30 + (ano - 2013) * 2)
            )

        # linha de outro município já processado -- prova que rodar
        # para RIO_CLARO não apaga LIMEIRA
        conexao.execute(
            "CREATE TABLE previsao_temporal ("
            "tipo_cancer TEXT, anos_historico INTEGER, ano_previsto INTEGER, "
            "internacoes_previstas REAL, erro_validacao_pct REAL, "
            "confiabilidade TEXT, municipio TEXT)"
        )
        conexao.execute(
            "INSERT INTO previsao_temporal VALUES "
            "('MAMA', 13, 2026, 99.0, 5.0, 'OK', 'LIMEIRA')"
        )

        conexao.commit()
        conexao.close()

        caminho_script = os.path.join(
            DIRETORIO_ATUAL, "previsao_temporal.py"
        )
        codigo_fonte = open(caminho_script, encoding="utf-8-sig").read()
        codigo_fonte = codigo_fonte.replace(
            CAMINHO_ORIGINAL, banco.replace("\\", "\\\\")
        )

        os.environ["ESCUDO_MUNICIPIO"] = "RIO_CLARO"

        if "configuracao_geografica" in sys.modules:
            sys.modules["configuracao_geografica"].BANCO = banco

        # previsao_temporal.py, ao contrário de serie_temporal.py, usa
        # "if __name__ == '__main__':" para deixar suas funções
        # importáveis sem efeito colateral -- por isso o exec aqui
        # precisa simular __main__ de verdade, senão o bloco principal
        # nunca roda
        exec(
            compile(codigo_fonte, "previsao_temporal.py", "exec"),
            {"__name__": "__main__"}
        )

        conexao = sqlite3.connect(banco)
        linhas = conexao.execute(
            "SELECT tipo_cancer, municipio, confiabilidade "
            "FROM previsao_temporal ORDER BY municipio"
        ).fetchall()
        conexao.close()

        checar(
            "linha de outro município (LIMEIRA) sobrevive à gravação",
            ("MAMA", "LIMEIRA", "OK") in linhas
        )

        checar(
            "RIO_CLARO/MAMA foi gravado com confiabilidade OK "
            "(tendência linear limpa e crescente)",
            ("MAMA", "RIO_CLARO", "OK") in linhas
        )

    finally:
        os.remove(banco)


def testar_com_dado_historico_real(checar):

    caminho_csv = os.path.join(
        DIRETORIO_ATUAL, "..", "analises", "base_preditiva_2013_2025.csv"
    )

    if not os.path.exists(caminho_csv):
        print(
            "[PULADO] dado histórico real não encontrado neste "
            "checkout -- teste de sanidade contra 2013-2025 ignorado"
        )
        return

    df = pd.read_csv(caminho_csv, sep=";")

    serie_df = df[df["territorio"] == "Rio Claro"].rename(columns={
        "cancer": "tipo_cancer",
    })[["tipo_cancer", "ano", "internacoes"]]

    serie_df["grupo"] = "MUNICIPIO"

    resultado = gerar_previsao_municipio(serie_df)

    checar(
        "roda sem quebrar sobre os 7 cânceres reais de Rio Claro "
        "2013-2025",
        len(resultado) == df[df["territorio"] == "Rio Claro"][
            "cancer"
        ].nunique()
    )

    checar(
        "com 13 anos reais por câncer, todas as séries têm previsão "
        "(nunca AMOSTRA_INSUFICIENTE)",
        resultado["internacoes_previstas"].notna().all()
    )

    checar(
        "nenhuma previsão negativa, mesmo com a variação real de "
        "internação ano a ano",
        (resultado["internacoes_previstas"] >= 0).all()
    )

    checar(
        "com 13 anos reais, todas as séries passaram pela validação "
        "temporal (nenhuma ficou NAO_VALIDADO)",
        resultado["erro_validacao_pct"].notna().all()
    )

    print("\nPrévia da previsão sobre dado histórico real (Rio Claro):\n")
    print(resultado.to_string(index=False))


def testar():

    falhas = []

    def checar(descricao, condicao):
        status = "OK" if condicao else "FALHOU"
        print(f"[{status}] {descricao}")
        if not condicao:
            falhas.append(descricao)

    testar_calculo_isolado(checar)
    testar_agrupamento_por_cancer(checar)
    testar_execucao_real_multi_tenant(checar)
    testar_com_dado_historico_real(checar)

    if falhas:
        raise SystemExit(f"{len(falhas)} checagem(ns) falharam: {falhas}")

    print("\nTodas as checagens da previsão temporal passaram.")


if __name__ == "__main__":
    testar()
