
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
# a série anual de internações (serie_temporal_anual).
#
# A validação continua sendo temporal e contra um baseline simples.
# A novidade desta versão é somente permitir escolher um ano futuro
# para a extrapolação. A lógica do modelo e a régua de validação não
# mudam.
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

ANOS_MINIMOS_PARA_PREVISAO = 3
ANOS_MINIMOS_PARA_VALIDACAO = 4
MAX_DOBRAS_VALIDACAO = 4
LIMITE_ERRO_BAIXA_CONFIABILIDADE_PCT = 30.0


def calcular_previsao_serie(anos, internacoes, ano_alvo=None):
    """
    Ajusta uma reta sobre internações x ano e projeta um ano futuro.

    ano_alvo=None mantém o comportamento original: projeta o ano
    imediatamente seguinte ao último ano observado.

    Quando ano_alvo é informado, ele precisa ser posterior ao último
    ano da série. A validação histórica continua exatamente a mesma;
    o parâmetro só altera o ponto futuro em que a reta é avaliada.

    Para transparência, a função também devolve o horizonte em anos.
    """

    anos = np.asarray(anos, dtype=float)
    internacoes = np.asarray(internacoes, dtype=float)

    ultimo_ano = int(anos.max())
    proximo_ano = ultimo_ano + 1
    ano_previsto = (
        proximo_ano if ano_alvo is None else int(ano_alvo)
    )

    if ano_previsto <= ultimo_ano:
        raise ValueError(
            f"ano_alvo deve ser posterior ao último ano observado ({ultimo_ano})"
        )

    horizonte_anos = ano_previsto - ultimo_ano

    if len(anos) < ANOS_MINIMOS_PARA_PREVISAO:
        return {
            "ano_previsto": ano_previsto,
            "horizonte_anos": horizonte_anos,
            "internacoes_previstas": None,
            "erro_validacao_pct": None,
            "erro_baseline_pct": None,
            "supera_baseline": False,
            "dobras_validacao": 0,
            "confiabilidade": (
                f"AMOSTRA_INSUFICIENTE ({len(anos)} ano(s) de "
                f"histórico, mínimo {ANOS_MINIMOS_PARA_PREVISAO})"
            ),
        }

    inclinacao, intercepto = np.polyfit(anos, internacoes, 1)
    internacoes_previstas = max(
        0.0,
        inclinacao * ano_previsto + intercepto
    )

    erro_validacao_pct = None
    erro_baseline_pct = None
    dobras_testadas = 0

    if len(anos) >= ANOS_MINIMOS_PARA_VALIDACAO:
        ordem = np.argsort(anos)
        anos_ord = anos[ordem]
        internacoes_ord = internacoes[ordem]

        n = len(anos_ord)
        num_dobras = min(
            MAX_DOBRAS_VALIDACAO,
            n - ANOS_MINIMOS_PARA_PREVISAO
        )

        erros_dobras = []
        erros_dobras_baseline = []

        for corte in range(n - num_dobras, n):
            anos_treino = anos_ord[:corte]
            internacoes_treino = internacoes_ord[:corte]
            ano_teste = anos_ord[corte]
            internacoes_teste = internacoes_ord[corte]

            inclinacao_val, intercepto_val = np.polyfit(
                anos_treino, internacoes_treino, 1
            )
            previsto_teste = max(
                0.0,
                inclinacao_val * ano_teste + intercepto_val
            )
            previsto_baseline = internacoes_treino[-1]

            if internacoes_teste > 0:
                erros_dobras.append(
                    abs(previsto_teste - internacoes_teste)
                    / internacoes_teste * 100
                )
                erros_dobras_baseline.append(
                    abs(previsto_baseline - internacoes_teste)
                    / internacoes_teste * 100
                )

        dobras_testadas = len(erros_dobras)

        if erros_dobras:
            erro_validacao_pct = float(np.mean(erros_dobras))
            erro_baseline_pct = float(np.mean(erros_dobras_baseline))

    supera_baseline = (
        erro_validacao_pct is not None
        and erro_validacao_pct < erro_baseline_pct
    )

    if erro_validacao_pct is None:
        confiabilidade = (
            f"NAO_VALIDADO (histórico com {len(anos)} ano(s), mínimo "
            f"{ANOS_MINIMOS_PARA_VALIDACAO} para rodar ao menos uma "
            f"dobra de validação temporal)"
        )
    elif not supera_baseline:
        # A regressão não bateu a regra "repete o último ano".
        # Mantemos o baseline como previsão usada.
        internacoes_previstas = internacoes_ord[-1]
        confiabilidade = (
            f"SEM_GANHO_PREDITIVO (regressão errou {erro_validacao_pct:.1f}% "
            f"em média, baseline simples errou {erro_baseline_pct:.1f}% -- "
            f"usando o baseline como previsão)"
        )
    elif erro_validacao_pct > LIMITE_ERRO_BAIXA_CONFIABILIDADE_PCT:
        confiabilidade = (
            f"BAIXA_CONFIABILIDADE (erro médio de "
            f"{erro_validacao_pct:.1f}% em {dobras_testadas} dobra(s) "
            f"de validação temporal, contra {erro_baseline_pct:.1f}% "
            f"do baseline)"
        )
    else:
        confiabilidade = "OK"

    return {
        "ano_previsto": ano_previsto,
        "horizonte_anos": horizonte_anos,
        "internacoes_previstas": round(float(internacoes_previstas), 1),
        "erro_validacao_pct": (
            round(erro_validacao_pct, 1)
            if erro_validacao_pct is not None else None
        ),
        "erro_baseline_pct": (
            round(erro_baseline_pct, 1)
            if erro_baseline_pct is not None else None
        ),
        "supera_baseline": supera_baseline,
        "dobras_validacao": dobras_testadas,
        "confiabilidade": confiabilidade,
    }


def gerar_previsao_municipio(serie_df, ano_alvo=None):
    """
    Recebe série temporal já filtrada pelo município e devolve uma
    linha de previsão por tipo de câncer.

    ano_alvo=None preserva o comportamento original (próximo ano).
    Quando informado, todas as séries são projetadas para esse mesmo
    ano futuro.
    """

    linhas = []

    municipio_df = serie_df[serie_df["grupo"] == "MUNICIPIO"]

    for cancer, grupo_df in municipio_df.groupby("tipo_cancer"):
        grupo_df = grupo_df.sort_values("ano")

        resultado = calcular_previsao_serie(
            grupo_df["ano"].tolist(),
            grupo_df["internacoes"].tolist(),
            ano_alvo=ano_alvo,
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
        "extrapolação da tendência histórica, validada contra vários "
        "dos últimos anos reais (não só o mais recente) sempre que "
        "há histórico suficiente para isso.\n"
    )
    print(previsao.to_string(index=False))

    salvar_tabela_municipio(
        previsao, "previsao_temporal", conn, municipio=MUNICIPIO
    )

    print("\nTabela previsao_temporal criada com sucesso.")

    conn.close()
