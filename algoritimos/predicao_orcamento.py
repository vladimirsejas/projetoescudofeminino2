import sqlite3
import unicodedata

import numpy as np
import pandas as pd

# =====================================
# PREDIÇÃO + SUGESTÃO DE ORÇAMENTO
#
# Pedido da Secretaria da Mulher: a predição não deve dizer só "como
# cada doença vai evoluir", mas indicar ONDE colocar o orçamento.
#
# O script faz isso em três camadas, todas determinísticas (a IA
# generativa só explica o resultado, nunca calcula):
#
#   1. PROJEÇÃO: para cada câncer, uma reta de tendência (mínimos
#      quadrados) sobre toda a série anual 2013-2025, projetada para
#      os próximos anos, com intervalo de previsão de ~90%. Os
#      números de um município pequeno são baixos e oscilam muito --
#      por isso o intervalo é sempre mostrado junto, nunca só o ponto.
#   2. VALIDAÇÃO (backtest): o mesmo método é treinado só até 2022 e
#      testado em 2023-2025, comparado com um palpite ingênuo (média
#      dos 3 últimos anos). Assim dá pra dizer, com número, se a
#      tendência acerta mais do que "repetir o passado".
#   3. PRIORIDADE DE ORÇAMENTO: um índice de 0 a 100 por câncer,
#      soma ponderada de seis critérios (carga futura, crescimento,
#      crescimento acima do Estado, letalidade, custo futuro e
#      potencial de prevenção). O percentual sugerido do orçamento
#      é a participação de cada câncer na soma dos índices. Os pesos
#      ficam expostos (PESOS_PADRAO) e o dashboard deixa a gestora
#      mudá-los -- a decisão continua sendo dela.
#
# Limites que precisam aparecer junto do resultado:
#   - SIH/SUS registra internações (AIH), não casos novos.
#   - O "custo" é o valor pago pela AIH, não o custo total do
#     tratamento (quimioterapia/radioterapia ambulatorial ficam fora).
#   - A sugestão é um ponto de partida para a discussão, não uma
#     regra de alocação.
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

HORIZONTE_PADRAO = 3
Z_90 = 1.645  # aproximação normal do intervalo de previsão de ~90%

# Quanto o município "empresta" da taxa estadual ao calcular a
# letalidade (encolhimento bayesiano empírico). Com poucas
# internações, 1 óbito a mais muda a taxa em vários pontos; somar
# K internações "virtuais" com a taxa de SP estabiliza a estimativa
# sem apagar a diferença real quando o município tem volume.
K_ENCOLHIMENTO = 20

PESOS_PADRAO = {
    "carga_futura": 0.25,
    "crescimento": 0.15,
    "excesso_estadual": 0.10,
    "letalidade": 0.20,
    "custo_futuro": 0.15,
    "prevencao": 0.15,
}

NOMES_CRITERIOS = {
    "carga_futura": "Internações previstas",
    "crescimento": "Ritmo de crescimento",
    "excesso_estadual": "Cresce mais que o Estado",
    "letalidade": "Letalidade",
    "custo_futuro": "Custo hospitalar previsto",
    "prevencao": "Potencial de prevenção",
}

# Potencial de prevenção/detecção precoce com ação municipal
# conhecida (referência: diretrizes do INCA/Ministério da Saúde).
# 1.0 = há rastreamento ou prevenção primária de eficácia
# estabelecida que o município executa na atenção básica;
# 0.5 = prevenção indireta (ex.: controle do tabagismo);
# 0.2 = sem rastreamento populacional recomendado.
# A ordem importa: "colorretal" contém "colo", então precisa ser
# testado antes de "colo" (colo do útero).
POTENCIAL_PREVENCAO = {
    "colorretal": (1.0, "Pesquisa de sangue oculto nas fezes e colonoscopia"),
    "colo": (1.0, "Rastreamento (Papanicolau / teste de DNA-HPV) e vacina HPV"),
    "mama": (1.0, "Mamografia de rastreamento (50-69 anos) e acesso rápido à biópsia"),
    "pele": (0.8, "Fotoproteção e exame de lesões na atenção básica"),
    "pulmao": (0.5, "Programa de cessação do tabagismo"),
    "ovario": (0.2, "Sem rastreamento recomendado: foco em diagnóstico e referência rápida"),
    "tireoide": (0.2, "Sem rastreamento recomendado: evitar sobrediagnóstico"),
}


# =====================================
# UTILITÁRIOS
# =====================================

def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower().replace("_", " ")


def potencial_prevencao(tipo_cancer):
    """Devolve (nota 0-1, ação sugerida) para o nome do câncer,
    tolerando as grafias usadas no banco ("MAMA", "COLO_UTERO",
    "Colo do útero" ...)."""
    nome = _normalizar(tipo_cancer)
    for chave, valor in POTENCIAL_PREVENCAO.items():
        if chave in nome:
            return valor
    return (0.5, "Diagnóstico precoce e referência rápida")


def formatar_numero(valor, casas=1):
    """1234.5 -> '1.234,5' (padrão brasileiro)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _escala_0_1(serie):
    serie = serie.astype(float)
    minimo, maximo = serie.min(), serie.max()
    if maximo - minimo < 1e-12:
        return pd.Series(0.5, index=serie.index)
    return (serie - minimo) / (maximo - minimo)


# =====================================
# 1. PROJEÇÃO
# =====================================

def ajustar_tendencia(anos, valores):
    """Reta de mínimos quadrados. Devolve dict com inclinação,
    intercepto e o necessário para o intervalo de previsão."""
    x = np.asarray(anos, dtype=float)
    y = np.asarray(valores, dtype=float)
    n = len(x)
    if n < 3:
        media = float(y.mean()) if n else 0.0
        return {"inclinacao": 0.0, "intercepto": media, "x_medio": float(x.mean()) if n else 0.0,
                "sxx": 1.0, "s": float(y.std()) if n else 0.0, "n": n}
    x_medio = x.mean()
    sxx = float(((x - x_medio) ** 2).sum())
    inclinacao = float(((x - x_medio) * (y - y.mean())).sum() / sxx)
    intercepto = float(y.mean() - inclinacao * x_medio)
    residuos = y - (intercepto + inclinacao * x)
    s = float(np.sqrt((residuos ** 2).sum() / (n - 2)))
    return {"inclinacao": inclinacao, "intercepto": intercepto,
            "x_medio": float(x_medio), "sxx": sxx, "s": s, "n": n}


def prever(modelo, anos_futuros):
    """Ponto previsto e intervalo de ~90% (nunca abaixo de zero)."""
    x0 = np.asarray(anos_futuros, dtype=float)
    ponto = modelo["intercepto"] + modelo["inclinacao"] * x0
    n = max(modelo["n"], 1)
    erro = modelo["s"] * np.sqrt(1 + 1 / n + (x0 - modelo["x_medio"]) ** 2 / modelo["sxx"])
    return (np.clip(ponto, 0, None),
            np.clip(ponto - Z_90 * erro, 0, None),
            np.clip(ponto + Z_90 * erro, 0, None))


def completar_anos(serie):
    """Garante uma linha por (tipo_cancer, grupo, ano) no intervalo
    completo, com zero onde não houve internação -- ano sem registro
    é informação (zero), não dado faltante."""
    anos = range(int(serie["ano"].min()), int(serie["ano"].max()) + 1)
    indice = pd.MultiIndex.from_product(
        [serie["tipo_cancer"].unique(), serie["grupo"].unique(), anos],
        names=["tipo_cancer", "grupo", "ano"],
    )
    return (serie.set_index(["tipo_cancer", "grupo", "ano"])
                 .reindex(indice, fill_value=0)
                 .reset_index())


def projetar(serie, horizonte=HORIZONTE_PADRAO):
    """Recebe a série anual (tipo_cancer, grupo, ano, internacoes,
    obitos, valor_total; grupo = 'MUNICIPIO' ou 'SP') e devolve uma
    tabela longa com histórico + projeção de internações e custo."""
    serie = completar_anos(serie)
    ultimo_ano = int(serie["ano"].max())
    anos_futuros = list(range(ultimo_ano + 1, ultimo_ano + 1 + horizonte))
    linhas = []

    for (cancer, grupo), dados in serie.groupby(["tipo_cancer", "grupo"]):
        dados = dados.sort_values("ano")
        for _, r in dados.iterrows():
            linhas.append({"tipo_cancer": cancer, "grupo": grupo, "ano": int(r["ano"]),
                           "tipo": "historico", "internacoes": float(r["internacoes"]),
                           "internacoes_min": np.nan, "internacoes_max": np.nan,
                           "valor_total": float(r["valor_total"])})

        modelo = ajustar_tendencia(dados["ano"], dados["internacoes"])
        ponto, minimo, maximo = prever(modelo, anos_futuros)

        # custo por internação: média dos 3 últimos anos com internação
        recentes = dados[dados["internacoes"] > 0].tail(3)
        custo_medio = (recentes["valor_total"].sum() / recentes["internacoes"].sum()
                       if not recentes.empty else 0.0)

        for ano, p, lo, hi in zip(anos_futuros, ponto, minimo, maximo):
            linhas.append({"tipo_cancer": cancer, "grupo": grupo, "ano": ano,
                           "tipo": "projecao", "internacoes": float(p),
                           "internacoes_min": float(lo), "internacoes_max": float(hi),
                           "valor_total": float(p * custo_medio)})

    return pd.DataFrame(linhas)


# =====================================
# 2. VALIDAÇÃO (BACKTEST)
# =====================================

def validar(serie, anos_teste=3):
    """Treina até (último ano - anos_teste) e mede o erro absoluto
    médio nos anos de teste, contra o palpite ingênuo (média dos 3
    últimos anos de treino). Só o grupo MUNICIPIO."""
    serie = completar_anos(serie)
    serie = serie[serie["grupo"] == "MUNICIPIO"]
    ultimo = int(serie["ano"].max())
    corte = ultimo - anos_teste
    linhas = []
    for cancer, dados in serie.groupby("tipo_cancer"):
        treino = dados[dados["ano"] <= corte]
        teste = dados[dados["ano"] > corte].sort_values("ano")
        if len(treino) < 3 or teste.empty:
            continue
        ponto, lo, hi = prever(ajustar_tendencia(treino["ano"], treino["internacoes"]), teste["ano"])
        ingenuo = treino.sort_values("ano")["internacoes"].tail(3).mean()
        real = teste["internacoes"].to_numpy(dtype=float)
        linhas.append({
            "tipo_cancer": cancer,
            "erro_medio_tendencia": float(np.abs(real - ponto).mean()),
            "erro_medio_ingenuo": float(np.abs(real - ingenuo).mean()),
            "anos_dentro_intervalo": int(((real >= lo) & (real <= hi)).sum()),
            "anos_testados": len(real),
        })
    return pd.DataFrame(linhas)


# =====================================
# 3. PRIORIDADE DE ORÇAMENTO
# =====================================

def _crescimento_relativo(dados):
    """Inclinação da reta em % da média anual (ritmo, sem depender do
    tamanho da doença -- senão a maior doença sempre 'cresce mais')."""
    media = dados["internacoes"].mean()
    if media <= 0:
        return 0.0
    return ajustar_tendencia(dados["ano"], dados["internacoes"])["inclinacao"] / media * 100


def ultimo_ano_atipico(dados):
    """True quando o último ano ficou acima da faixa de ~90% prevista
    pela tendência dos anos anteriores. Em 2025, por exemplo, o Estado
    inteiro saltou ~50% de uma vez -- a gestora precisa saber que a
    previsão não parte desse pico, e por quê."""
    dados = dados.sort_values("ano")
    if len(dados) < 5:
        return False
    anteriores, ultimo = dados.iloc[:-1], dados.iloc[-1]
    _, _, maximo = prever(ajustar_tendencia(anteriores["ano"], anteriores["internacoes"]), [ultimo["ano"]])
    return bool(ultimo["internacoes"] > maximo[0])


def calcular_prioridades(serie, pesos=None, horizonte=HORIZONTE_PADRAO, anos_letalidade=5):
    """Uma linha por câncer com os critérios, o índice 0-100 e o
    percentual sugerido do orçamento."""
    pesos = dict(PESOS_PADRAO if pesos is None else pesos)
    soma_pesos = sum(pesos.values()) or 1.0
    pesos = {k: v / soma_pesos for k, v in pesos.items()}

    serie = completar_anos(serie)
    projecao = projetar(serie, horizonte)
    ultimo = int(serie["ano"].max())
    linhas = []

    for cancer in sorted(serie["tipo_cancer"].unique()):
        mun = serie[(serie["tipo_cancer"] == cancer) & (serie["grupo"] == "MUNICIPIO")]
        est = serie[(serie["tipo_cancer"] == cancer) & (serie["grupo"] == "SP")]
        fut = projecao[(projecao["tipo_cancer"] == cancer) & (projecao["grupo"] == "MUNICIPIO")
                       & (projecao["tipo"] == "projecao")]

        recente_mun = mun[mun["ano"] > ultimo - anos_letalidade]
        recente_est = est[est["ano"] > ultimo - anos_letalidade]
        taxa_sp = (recente_est["obitos"].sum() / recente_est["internacoes"].sum()
                   if recente_est["internacoes"].sum() > 0 else 0.0)
        letalidade = ((recente_mun["obitos"].sum() + K_ENCOLHIMENTO * taxa_sp)
                      / (recente_mun["internacoes"].sum() + K_ENCOLHIMENTO))

        cresc_mun = _crescimento_relativo(mun)
        atipico_mun = ultimo_ano_atipico(mun)
        atipico_sp = ultimo_ano_atipico(est) if not est.empty else False
        cresc_sp = _crescimento_relativo(est) if not est.empty else 0.0
        nota_prev, acao_prev = potencial_prevencao(cancer)

        linhas.append({
            "tipo_cancer": cancer,
            "internacoes_ultimo_ano": int(mun[mun["ano"] == ultimo]["internacoes"].sum()),
            "internacoes_previstas": float(fut["internacoes"].sum()),
            "internacoes_previstas_min": float(fut["internacoes_min"].sum()),
            "internacoes_previstas_max": float(fut["internacoes_max"].sum()),
            "custo_previsto": float(fut["valor_total"].sum()),
            "crescimento_anual_pct": cresc_mun,
            "crescimento_anual_sp_pct": cresc_sp,
            "letalidade_pct": letalidade * 100,
            "letalidade_sp_pct": taxa_sp * 100,
            "nota_prevencao": nota_prev,
            "acao_prevencao": acao_prev,
            "ultimo_ano_atipico": atipico_mun,
            "ultimo_ano_atipico_sp": atipico_sp,
        })

    tabela = pd.DataFrame(linhas)
    if tabela.empty:
        return tabela

    tabela["c_carga_futura"] = _escala_0_1(tabela["internacoes_previstas"])
    tabela["c_crescimento"] = _escala_0_1(tabela["crescimento_anual_pct"].clip(lower=0))
    tabela["c_excesso_estadual"] = _escala_0_1(
        (tabela["crescimento_anual_pct"] - tabela["crescimento_anual_sp_pct"]).clip(lower=0))
    tabela["c_letalidade"] = _escala_0_1(tabela["letalidade_pct"])
    tabela["c_custo_futuro"] = _escala_0_1(tabela["custo_previsto"])
    tabela["c_prevencao"] = tabela["nota_prevencao"]

    tabela["indice"] = sum(tabela[f"c_{k}"] * pesos.get(k, 0) for k in PESOS_PADRAO) * 100
    total = tabela["indice"].sum()
    tabela["pct_orcamento"] = tabela["indice"] / total * 100 if total > 0 else 100 / len(tabela)

    # contribuição de cada critério em pontos do índice (para explicar)
    for k in PESOS_PADRAO:
        tabela[f"pontos_{k}"] = tabela[f"c_{k}"] * pesos.get(k, 0) * 100

    tabela["acao_sugerida"] = tabela.apply(_acao_sugerida, axis=1)
    tabela["justificativa"] = tabela.apply(_justificativa, axis=1)
    return tabela.sort_values("pct_orcamento", ascending=False).reset_index(drop=True)


def _acao_sugerida(linha):
    """Em que tipo de ação o recurso rende mais, dado o perfil."""
    if linha["nota_prevencao"] >= 0.8:
        return "Prevenção e rastreamento — " + linha["acao_prevencao"]
    if linha["letalidade_pct"] >= max(linha["letalidade_sp_pct"], 1) * 1.2:
        return "Diagnóstico precoce e acesso rápido a tratamento (letalidade acima do Estado)"
    if linha["crescimento_anual_pct"] > 5:
        return "Ampliar capacidade de atendimento (demanda em alta) — " + linha["acao_prevencao"]
    return linha["acao_prevencao"]


def _justificativa(linha):
    motivos = []
    if linha["c_carga_futura"] >= 0.6:
        motivos.append(f"deve gerar cerca de {formatar_numero(linha['internacoes_previstas'], 0)} internações no período projetado")
    if linha["crescimento_anual_pct"] > 3:
        motivos.append(f"cresce {formatar_numero(linha['crescimento_anual_pct'])}% ao ano")
    if linha["crescimento_anual_pct"] - linha["crescimento_anual_sp_pct"] > 2:
        motivos.append(f"cresce mais rápido que o Estado ({formatar_numero(linha['crescimento_anual_sp_pct'])}% ao ano)")
    if linha["letalidade_pct"] > linha["letalidade_sp_pct"] * 1.2 and linha["letalidade_pct"] >= 1:
        motivos.append(f"letalidade hospitalar de {formatar_numero(linha['letalidade_pct'])}%, acima do Estado "
                       f"({formatar_numero(linha['letalidade_sp_pct'])}%)")
    elif linha["c_letalidade"] >= 0.6:
        motivos.append(f"letalidade hospitalar de {formatar_numero(linha['letalidade_pct'])}%, entre as mais altas")
    if linha["nota_prevencao"] >= 0.8:
        motivos.append("tem prevenção/rastreamento eficaz que o município pode executar")
    if not motivos:
        motivos.append("volume, crescimento e letalidade abaixo dos demais cânceres")
    texto = "; ".join(motivos)
    return texto[0].upper() + texto[1:] + "."


def distribuir_orcamento(prioridades, valor_total):
    """Aplica o percentual sugerido a um valor em reais."""
    tabela = prioridades[["tipo_cancer", "pct_orcamento", "acao_sugerida"]].copy()
    tabela["valor_sugerido"] = tabela["pct_orcamento"] / 100 * float(valor_total)
    return tabela


# =====================================
# CARREGAMENTO
# =====================================

SQL_SERIE = """
SELECT tipo_cancer, 'MUNICIPIO' AS grupo, ano,
       COUNT(*) AS internacoes,
       COALESCE(SUM(obito), 0) AS obitos,
       COALESCE(SUM(valor_total), 0) AS valor_total
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer, ano

UNION ALL

SELECT tipo_cancer, 'SP' AS grupo, ano,
       COUNT(*) AS internacoes,
       COALESCE(SUM(obito), 0) AS obitos,
       COALESCE(SUM(valor_total), 0) AS valor_total
FROM internacoes
WHERE origem = ?
GROUP BY tipo_cancer, ano
"""


def carregar_serie_banco(conexao, municipio, uf_referencia="SP"):
    """Série anual do município + referência estadual, direto de
    `internacoes` (mesmo recorte de serie_temporal.py)."""
    return pd.read_sql(SQL_SERIE, conexao, params=(municipio, uf_referencia))


def carregar_serie_csv(caminho, territorio="Rio Claro", referencia="São Paulo"):
    """Lê analises/base_preditiva_2013_2025.csv (base pública
    versionada) no mesmo formato de carregar_serie_banco()."""
    base = pd.read_csv(caminho, sep=";")
    base = base[base["territorio"].isin([territorio, referencia])].copy()
    base["grupo"] = np.where(base["territorio"] == territorio, "MUNICIPIO", "SP")
    base = base.rename(columns={"cancer": "tipo_cancer"})
    return base[["tipo_cancer", "grupo", "ano", "internacoes", "obitos", "valor_total"]]


# =====================================
# EXECUÇÃO DIRETA (passo opcional da cadeia)
# =====================================

if __name__ == "__main__":
    from configuracao_geografica import obter_municipio, salvar_tabela_municipio, UF_REFERENCIA

    municipio = obter_municipio()
    conn = sqlite3.connect(BANCO)
    serie = carregar_serie_banco(conn, municipio, UF_REFERENCIA)

    prioridades = calcular_prioridades(serie)
    projecao = projetar(serie)
    validacao = validar(serie)

    pd.set_option("display.width", 200)
    print(f"\n=== SUGESTÃO DE ORÇAMENTO — {municipio} ===\n")
    print(prioridades[["tipo_cancer", "indice", "pct_orcamento", "acao_sugerida"]]
          .round(1).to_string(index=False))
    print("\n=== VALIDAÇÃO (treino até 3 anos antes, teste nos 3 últimos) ===\n")
    print(validacao.round(1).to_string(index=False))

    salvar_tabela_municipio(prioridades, "predicao_orcamento", conn, municipio=municipio)
    salvar_tabela_municipio(projecao, "predicao_projecao", conn, municipio=municipio)
    print("\nTabelas predicao_orcamento e predicao_projecao atualizadas.")
    conn.close()
