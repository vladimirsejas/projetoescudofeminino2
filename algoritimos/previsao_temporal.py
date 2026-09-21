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
            "erro_baseline_pct": None,
            "supera_baseline": False,
            "dobras_validacao": 0,
            "confiabilidade": (
                f"AMOSTRA_INSUFICIENTE ({len(anos)} ano(s) de "
                f"histórico, mínimo {ANOS_MINIMOS_PARA_PREVISAO})"
            ),
        }

    inclinacao, intercepto = np.polyfit(anos, internacoes, 1)
    internacoes_previstas = max(0.0, inclinacao * proximo_ano + intercepto)

    erro_validacao_pct = None
    erro_baseline_pct = None
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
        #
        # Em cada dobra, também mede o baseline ingênuo ("o próximo
        # ano repete o último valor conhecido") -- é a régua para
        # responder se a regressão realmente ajuda ou é só maquiagem:
        # com ~13 pontos por câncer, um modelo que não bate uma regra
        # trivial não demonstrou capacidade preditiva nenhuma.
        ordem = np.argsort(anos)
        anos_ord = anos[ordem]
        internacoes_ord = internacoes[ordem]

        n = len(anos_ord)
        num_dobras = min(MAX_DOBRAS_VALIDACAO, n - ANOS_MINIMOS_PARA_PREVISAO)

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
                0.0, inclinacao_val * ano_teste + intercepto_val
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
        # a regressão não bateu nem a regra "repete o último ano" --
        # não demonstrou ganho preditivo, então a previsão que vale é
        # o próprio baseline, não a extrapolação da reta
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
        # "OK" fica exato (sem detalhe embutido) para se comportar
        # como o mesmo sinalizador usado em tendencia_estadual.py e
        # anomalias.py (checado com "!= OK" nesses outros arquivos) --
        # o detalhe da validação já está em erro_validacao_pct,
        # erro_baseline_pct e dobras_testadas, como colunas próprias.
        confiabilidade = "OK"

    return {
        "ano_previsto": proximo_ano,
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


HORIZONTES_FUTUROS = 3


def calcular_projecoes_futuras(anos, internacoes, horizontes=HORIZONTES_FUTUROS):
    """
    Estende a MESMA reta usada em calcular_previsao_serie() para os
    anos SEGUINTES ao já validado -- ex.: histórico até 2025,
    calcular_previsao_serie() já valida 2026 (guardado em
    previsao_temporal); esta função cobre 2027, 2028 e 2029 (padrão:
    3 anos além do validado), nunca repete o ano já validado.

    Diferença importante em relação a calcular_previsao_serie(): a
    validação rolling-origin que já existe testa só a previsão de UM
    ano à frente -- não temos evidência real de quão bem o mesmo
    modelo acerta 2, 3 ou 4 anos à frente, e fingir isso seria o
    exato overclaim que a comparação com baseline foi construída pra
    evitar. Por isso esta função não devolve confiabilidade nem erro
    de validação nenhum -- só o ponto extrapolado. Nenhum ano aqui é
    validado; o único ano validado vive em previsao_temporal.
    """

    anos = np.asarray(anos, dtype=float)
    internacoes = np.asarray(internacoes, dtype=float)

    if len(anos) < ANOS_MINIMOS_PARA_PREVISAO:
        return []

    ano_validado = int(anos.max()) + 1
    inclinacao, intercepto = np.polyfit(anos, internacoes, 1)

    projecoes = []

    for passo in range(1, horizontes + 1):
        ano_alvo = ano_validado + passo
        valor = max(0.0, inclinacao * ano_alvo + intercepto)

        projecoes.append({
            "ano_previsto": ano_alvo,
            "horizonte": passo + 1,
            "internacoes_previstas": round(float(valor), 1),
        })

    return projecoes


def gerar_projecoes_futuras_municipio(serie_df, horizontes=HORIZONTES_FUTUROS):
    """
    Mesma varredura por câncer de gerar_previsao_municipio(), mas
    devolve formato longo (uma linha por câncer x ano) para alimentar
    a escolha de ano na interface -- ao contrário de
    gerar_previsao_municipio(), que devolve só o ano seguinte.
    """

    linhas = []

    municipio_df = serie_df[serie_df["grupo"] == "MUNICIPIO"]

    for cancer, grupo_df in municipio_df.groupby("tipo_cancer"):

        grupo_df = grupo_df.sort_values("ano")

        for projecao in calcular_projecoes_futuras(
            grupo_df["ano"].tolist(),
            grupo_df["internacoes"].tolist(),
            horizontes=horizontes,
        ):
            linhas.append({"tipo_cancer": cancer, **projecao})

    return pd.DataFrame(linhas)


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

    projecoes = gerar_projecoes_futuras_municipio(serie)

    print(
        f"\n=== PROJEÇÃO ESTENDIDA -- {HORIZONTES_FUTUROS} ANOS "
        f"({MUNICIPIO}) ===\n"
    )
    print(
        "Nenhum ano aqui tem validação rolling-origin -- o único ano "
        "validado de verdade é o de previsao_temporal (o seguinte ao "
        "fim do histórico). Estes anos estendem a mesma reta mais "
        "adiante; trate como indicação de tendência, não como número "
        "validado.\n"
    )
    print(projecoes.to_string(index=False))

    salvar_tabela_municipio(
        projecoes, "previsao_temporal_horizontes", conn, municipio=MUNICIPIO
    )

    print("\nTabela previsao_temporal_horizontes criada com sucesso.")

    conn.close()
