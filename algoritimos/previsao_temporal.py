import sqlite3

import numpy as np
import pandas as pd

from configuracao_geografica import (
    obter_municipio,
    ler_tabela_municipio,
    salvar_tabela_municipio,
)

# =====================================
# FUNDAÇÃO DA CAMADA PREDITIVA
#
# Propositalmente simples: regressão linear por tipo de câncer sobre
# a série anual de internações (serie_temporal_anual). Com ~13 anos
# de histórico por câncer, um modelo mais complexo (random forest
# etc.) tende a decorar ruído em vez de aprender tendência -- por
# isso nenhuma biblioteca de machine learning nova entra aqui, só
# numpy (já é dependência indireta de pandas).
#
# Cadeia: serie_temporal_anual -> regressão -> validação temporal
# (treina sem o último ano, testa nele) -> previsão do próximo ano.
# A explicação em linguagem natural (Gemini) fica para depois --
# esta camada só produz o número e a confiabilidade dele.
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

ANOS_MINIMOS_PARA_PREVISAO = 3
ANOS_MINIMOS_PARA_VALIDACAO = 4
LIMITE_ERRO_BAIXA_CONFIABILIDADE_PCT = 30.0


def calcular_previsao_serie(anos, internacoes):
    """
    Ajusta uma reta sobre internações x ano e projeta o próximo ano.

    Nunca devolve só o número -- sempre vem acompanhado de uma
    avaliação honesta da confiabilidade, seguindo o mesmo princípio
    já usado em anomalias.py/tendencia_estadual.py para bases
    pequenas.
    """

    anos = np.asarray(anos, dtype=float)
    internacoes = np.asarray(internacoes, dtype=float)

    proximo_ano = int(anos.max()) + 1

    if len(anos) < ANOS_MINIMOS_PARA_PREVISAO:
        return {
            "ano_previsto": proximo_ano,
            "internacoes_previstas": None,
            "erro_validacao_pct": None,
            "confiabilidade": (
                f"AMOSTRA_INSUFICIENTE ({len(anos)} ano(s) de "
                f"histórico, mínimo {ANOS_MINIMOS_PARA_PREVISAO})"
            ),
        }

    inclinacao, intercepto = np.polyfit(anos, internacoes, 1)
    internacoes_previstas = max(0.0, inclinacao * proximo_ano + intercepto)

    erro_validacao_pct = None

    if len(anos) >= ANOS_MINIMOS_PARA_VALIDACAO:
        # validação temporal: treina sem o último ano e testa nele --
        # nunca embaralhar os anos, isso vazaria dado do "futuro"
        # para o treino
        ordem = np.argsort(anos)
        anos_ord = anos[ordem]
        internacoes_ord = internacoes[ordem]

        anos_treino, ano_teste = anos_ord[:-1], anos_ord[-1]
        internacoes_treino, internacoes_teste = (
            internacoes_ord[:-1], internacoes_ord[-1]
        )

        inclinacao_val, intercepto_val = np.polyfit(
            anos_treino, internacoes_treino, 1
        )
        previsto_teste = max(
            0.0, inclinacao_val * ano_teste + intercepto_val
        )

        if internacoes_teste > 0:
            erro_validacao_pct = (
                abs(previsto_teste - internacoes_teste)
                / internacoes_teste
            ) * 100

    if erro_validacao_pct is None:
        confiabilidade = (
            f"NAO_VALIDADO (histórico com {len(anos)} ano(s), mínimo "
            f"{ANOS_MINIMOS_PARA_VALIDACAO} para testar o modelo "
            f"contra um ano real)"
        )
    elif erro_validacao_pct > LIMITE_ERRO_BAIXA_CONFIABILIDADE_PCT:
        confiabilidade = (
            f"BAIXA_CONFIABILIDADE (erro de {erro_validacao_pct:.1f}% "
            f"ao testar o modelo contra o último ano real)"
        )
    else:
        confiabilidade = "OK"

    return {
        "ano_previsto": proximo_ano,
        "internacoes_previstas": round(internacoes_previstas, 1),
        "erro_validacao_pct": (
            round(erro_validacao_pct, 1)
            if erro_validacao_pct is not None else None
        ),
        "confiabilidade": confiabilidade,
    }


def gerar_previsao_municipio(serie_df):
    """
    Recebe serie_temporal_anual já filtrada pelo município e devolve
    uma linha de previsão por tipo_cancer -- só a série do próprio
    município (grupo == 'MUNICIPIO'), a referência estadual (SP) não
    é prevista aqui.
    """

    linhas = []

    municipio_df = serie_df[serie_df["grupo"] == "MUNICIPIO"]

    for cancer, grupo_df in municipio_df.groupby("tipo_cancer"):

        grupo_df = grupo_df.sort_values("ano")

        resultado = calcular_previsao_serie(
            grupo_df["ano"].tolist(), grupo_df["internacoes"].tolist()
        )

        linhas.append({
            "tipo_cancer": cancer,
            "anos_historico": len(grupo_df),
            **resultado,
        })

    return pd.DataFrame(linhas)


if __name__ == "__main__":

    conn = sqlite3.connect(BANCO)

    MUNICIPIO = obter_municipio()

    serie = ler_tabela_municipio(
        "serie_temporal_anual", conn, municipio=MUNICIPIO
    )

    if serie.empty:
        print(
            f"\n{MUNICIPIO} ainda não tem 'serie_temporal_anual' "
            f"processada. Rode algoritimos\\serie_temporal.py antes "
            f"deste script."
        )
        conn.close()
        raise SystemExit(1)

    previsao = gerar_previsao_municipio(serie)

    print(f"\n=== PREVISÃO TEMPORAL SIMPLES ({MUNICIPIO}) ===\n")
    print(
        "Regressão linear por tipo de câncer sobre a série anual de "
        "internações. Não é previsão epidemiológica precisa -- é uma "
        "extrapolação da tendência histórica, validada contra o "
        "último ano real sempre que há histórico suficiente para "
        "isso.\n"
    )
    print(previsao.to_string(index=False))

    salvar_tabela_municipio(
        previsao, "previsao_temporal", conn, municipio=MUNICIPIO
    )

    print("\nTabela previsao_temporal criada com sucesso.")

    conn.close()
