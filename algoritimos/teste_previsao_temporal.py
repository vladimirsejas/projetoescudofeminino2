
import os
import sqlite3
import sys
import tempfile

import pandas as pd

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ORIGINAL = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

sys.path.insert(0, DIRETORIO_ATUAL)

from previsao_temporal import (  # noqa: E402
    calcular_previsao_serie,
    gerar_previsao_municipio,
)


def testar_calculo_isolado(checar):

    r = calcular_previsao_serie([2023, 2024], [10, 12])
    checar(
        "menos anos que o mínimo -> AMOSTRA_INSUFICIENTE, sem previsão",
        r["internacoes_previstas"] is None
        and r["confiabilidade"].startswith("AMOSTRA_INSUFICIENTE")
    )

    r = calcular_previsao_serie([2023, 2024, 2025], [10, 12, 14])
    checar(
        "3 anos -> prevê, mas confiabilidade é NAO_VALIDADO",
        r["internacoes_previstas"] is not None
        and r["confiabilidade"].startswith("NAO_VALIDADO")
    )

    anos = [2020, 2021, 2022, 2023, 2024, 2025]
    internacoes = [10, 20, 30, 40, 50, 60]
    r = calcular_previsao_serie(anos, internacoes)
    checar(
        "tendência linear perfeita -> confiabilidade OK",
        r["confiabilidade"] == "OK"
    )
    checar(
        "tendência linear perfeita -> previsão 2026 é 70",
        r["ano_previsto"] == 2026
        and abs(r["internacoes_previstas"] - 70) < 0.01
    )

    r = calcular_previsao_serie(anos, internacoes, ano_alvo=2028)
    checar(
        "ano alvo 2028 -> extrapola a mesma reta para 2028 (90)",
        r["ano_previsto"] == 2028
        and r["horizonte_anos"] == 3
        and abs(r["internacoes_previstas"] - 90) < 0.01
    )

    anos = [2020, 2021, 2022, 2023, 2024, 2025]
    internacoes = [10, 12, 11, 13, 12, 80]
    r = calcular_previsao_serie(anos, internacoes)
    checar(
        "quebra abrupta no último ano -> BAIXA_CONFIABILIDADE",
        r["confiabilidade"].startswith("BAIXA_CONFIABILIDADE")
    )

    anos = [2021, 2022, 2023, 2024, 2025]
    internacoes = [50, 40, 30, 20, 10]
    r = calcular_previsao_serie(anos, internacoes)
    checar(
        "tendência de queda acentuada -> previsão nunca negativa",
        r["internacoes_previstas"] >= 0
    )

    anos = list(range(2018, 2026))
    internacoes = [50, 50, 50, 50, 50, 10, 10, 10]
    r = calcular_previsao_serie(anos, internacoes)
    checar(
        "mudança de patamar -> reta não supera baseline -> "
        "SEM_GANHO_PREDITIVO, previsão vira o baseline",
        not r["supera_baseline"]
        and r["confiabilidade"].startswith("SEM_GANHO_PREDITIVO")
        and r["internacoes_previstas"] == internacoes[-1]
    )

    try:
        calcular_previsao_serie(anos, internacoes, ano_alvo=2025)
    except ValueError:
        erro_rejeitado = True
    else:
        erro_rejeitado = False

    checar(
        "ano alvo no passado/último ano -> rejeitado",
        erro_rejeitado
    )


def testar_agrupamento_por_cancer(checar):

    serie_df = pd.DataFrame([
        {
            "tipo_cancer": "MAMA",
            "grupo": "MUNICIPIO",
            "ano": ano,
            "internacoes": 10 + ano - 2020,
        }
        for ano in range(2020, 2026)
    ] + [
        {
            "tipo_cancer": "MAMA",
            "grupo": "SP",
            "ano": ano,
            "internacoes": 1000 + ano,
        }
        for ano in range(2020, 2026)
    ] + [
        {
            "tipo_cancer": "COLO_UTERO",
            "grupo": "MUNICIPIO",
            "ano": ano,
            "internacoes": 5,
        }
        for ano in range(2020, 2026)
    ])

    resultado = gerar_previsao_municipio(serie_df, ano_alvo=2028)

    checar(
        "gera uma linha por câncer no mesmo ano-alvo, ignorando a série de SP",
        set(resultado["tipo_cancer"]) == {"MAMA", "COLO_UTERO"}
        and len(resultado) == 2
        and set(resultado["ano_previsto"]) == {2028}
        and set(resultado["horizonte_anos"]) == {3}
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

        conexao.execute(
            "CREATE TABLE previsao_temporal ("
            "tipo_cancer TEXT, anos_historico INTEGER, ano_previsto INTEGER, "
            "horizonte_anos INTEGER, internacoes_previstas REAL, "
            "erro_validacao_pct REAL, erro_baseline_pct REAL, "
            "supera_baseline INTEGER, dobras_validacao INTEGER, "
            "confiabilidade TEXT, municipio TEXT)"
        )
        conexao.execute(
            "INSERT INTO previsao_temporal VALUES "
            "('MAMA', 13, 2026, 1, 99.0, 5.0, 20.0, 1, 4, 'OK', 'LIMEIRA')"
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
            "RIO_CLARO/MAMA foi gravado com confiabilidade OK",
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
        "roda sem quebrar sobre os 7 cânceres reais de Rio Claro 2013-2025",
        len(resultado) == df[df["territorio"] == "Rio Claro"]["cancer"].nunique()
    )

    checar(
        "com 13 anos reais por câncer, todas as séries têm previsão",
        resultado["internacoes_previstas"].notna().all()
    )

    checar(
        "nenhuma previsão negativa",
        (resultado["internacoes_previstas"] >= 0).all()
    )

    checar(
        "com 13 anos reais, todas as séries passaram pela validação temporal",
        resultado["erro_validacao_pct"].notna().all()
    )

    checar(
        "todas as dobras usam o máximo disponível (4)",
        (resultado["dobras_validacao"] == 4).all()
    )

    pulmao = resultado[resultado["tipo_cancer"] == "Pulmão"].iloc[0]
    checar(
        "Pulmão não supera o baseline com validação rolling",
        not pulmao["supera_baseline"]
        and pulmao["confiabilidade"].startswith("SEM_GANHO_PREDITIVO")
    )

    ovario = resultado[resultado["tipo_cancer"] == "Ovário"].iloc[0]
    checar(
        "Ovário não supera o baseline",
        not ovario["supera_baseline"]
        and ovario["confiabilidade"].startswith("SEM_GANHO_PREDITIVO")
    )

    mama = resultado[resultado["tipo_cancer"] == "Mama"].iloc[0]
    checar(
        "Mama supera o baseline e fica OK",
        bool(mama["supera_baseline"]) and mama["confiabilidade"] == "OK"
    )

    resultado_2028 = gerar_previsao_municipio(
        serie_df,
        ano_alvo=2028
    )
    checar(
        "ano-alvo 2028 funciona também sobre os 7 cânceres reais",
        len(resultado_2028) == len(resultado)
        and (resultado_2028["ano_previsto"] == 2028).all()
        and (resultado_2028["horizonte_anos"] >= 3).all()
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
