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
# rolling-origin (testa contra cada um dos últimos anos disponíveis,
# nunca só o mais recente -- um holdout único pode acertar por sorte
# e esconder erro real nos anos anteriores) -> previsão do próximo
# ano. A explicação em linguagem natural (Gemini) fica para depois --
# esta camada só produz o número e a confiabilidade dele.
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

ANOS_MINIMOS_PARA_PREVISAO = 3
ANOS_MINIMOS_PARA_VALIDACAO = 4
MAX_DOBRAS_VALIDACAO = 4
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
            "dobras_validacao": 0,
            "confiabilidade": (
                f"AMOSTRA_INSUFICIENTE ({len(anos)} ano(s) de "
                f"histórico, mínimo {ANOS_MINIMOS_PARA_PREVISAO})"
            ),
        }

    inclinacao, intercepto = np.polyfit(anos, internacoes, 1)
    internacoes_previstas = max(0.0, inclinacao * proximo_ano + intercepto)

    erro_validacao_pct = None
    dobras_testadas = 0

    if len(anos) >= ANOS_MINIMOS_PARA_VALIDACAO:
        # validação temporal por múltiplas dobras (rolling-origin):
        # testar só contra o último ano é um único ponto de sorte --
        # provado com o próprio dado real do projeto, câncer que
        # acerta o último ano por acaso passa como "OK" mesmo errando
        # feio nos anos anteriores. Em vez disso, testa contra cada
        # um dos últimos anos disponíveis (até MAX_DOBRAS_VALIDACAO),
        # sempre treinando só com anos anteriores ao testado -- nunca
        # embaralhar, isso vazaria dado do "futuro" para o treino.
        ordem = np.argsort(anos)
        anos_ord = anos[ordem]
        internacoes_ord = internacoes[ordem]

        n = len(anos_ord)
        num_dobras = min(MAX_DOBRAS_VALIDACAO, n - ANOS_MINIMOS_PARA_PREVISAO)

        erros_dobras = []

        for corte in range(n - num_dobras, n):
            anos_treino = anos_ord[:corte]
            internacoes_treino = internacoes_ord[:corte]
            ano_teste = anos_ord[corte]
            internacoes_teste = internacoes_ord[corte]

            inclinacao_val, intercepto_val = np.polyfit(
                anos_treino, internacoes_treino, 1
            )
            previsto_teste = max(
                0.0, inclinacao_val * ano_teste + intercepto_val
            )

            if internacoes_teste > 0:
                erros_dobras.append(
                    abs(previsto_teste - internacoes_teste)
                    / internacoes_teste * 100
                )

        dobras_testadas = len(erros_dobras)

        if erros_dobras:
            erro_validacao_pct = float(np.mean(erros_dobras))

    if erro_validacao_pct is None:
        confiabilidade = (
            f"NAO_VALIDADO (histórico com {len(anos)} ano(s), mínimo "
            f"{ANOS_MINIMOS_PARA_VALIDACAO} para rodar ao menos uma "
            f"dobra de validação temporal)"
        )
    elif erro_validacao_pct > LIMITE_ERRO_BAIXA_CONFIABILIDADE_PCT:
        confiabilidade = (
            f"BAIXA_CONFIABILIDADE (erro médio de "
            f"{erro_validacao_pct:.1f}% em {dobras_testadas} dobra(s) "
            f"de validação temporal)"
        )
    else:
        # "OK" fica exato (sem detalhe embutido) para se comportar
        # como o mesmo sinalizador usado em tendencia_estadual.py e
        # anomalias.py (checado com "!= OK" nesses outros arquivos) --
        # o detalhe da validação já está em erro_validacao_pct e
        # dobras_testadas, como colunas próprias.
        confiabilidade = "OK"

    return {
        "ano_previsto": proximo_ano,
        "internacoes_previstas": round(internacoes_previstas, 1),
        "erro_validacao_pct": (
            round(erro_validacao_pct, 1)
            if erro_validacao_pct is not None else None
        ),
        "dobras_validacao": dobras_testadas,
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
        "extrapolação da tendência histórica, validada contra vários "
        "dos últimos anos reais (não só o mais recente) sempre que "
        "há histórico suficiente para "
        "isso.\n"
    )
    print(previsao.to_string(index=False))

    salvar_tabela_municipio(
        previsao, "previsao_temporal", conn, municipio=MUNICIPIO
    )

    print("\nTabela previsao_temporal criada com sucesso.")

    conn.close()
