import os

import pandas as pd

from predicao_orcamento import (
    PESOS_PADRAO,
    calcular_prioridades,
    carregar_serie_csv,
    distribuir_orcamento,
    formatar_numero,
    potencial_prevencao,
    projetar,
    validar,
)

# =====================================
# TESTE DA PREDIÇÃO + SUGESTÃO DE ORÇAMENTO
#
# Parte com série sintética (números fáceis de conferir de cabeça),
# parte com a base pública real analises/base_preditiva_2013_2025.csv.
# Não precisa do banco do Windows.
# =====================================

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CSV_REAL = os.path.join(DIRETORIO_ATUAL, "..", "analises", "base_preditiva_2013_2025.csv")

falhas = []


def checar(nome, condicao):
    print(("OK   " if condicao else "FALHOU ") + nome)
    if not condicao:
        falhas.append(nome)


def serie_sintetica():
    """Três doenças, 2013-2025:
    - CRESCE: 10, 12, 14 ... (+2/ano), sem óbito, com rastreamento
    - ESTAVEL: sempre 10, metade morre (grave), sem rastreamento
    - SOME: 5 em 2013 e 0 depois (ano sem registro vira zero)
    SP cresce 1%/ano em todas."""
    linhas = []
    for i, ano in enumerate(range(2013, 2026)):
        linhas.append(("Mama", "MUNICIPIO", ano, 10 + 2 * i, 0, 1000.0 * (10 + 2 * i)))
        linhas.append(("Ovário", "MUNICIPIO", ano, 10, 5, 3000.0 * 10))
        if ano == 2013:
            linhas.append(("Tireoide", "MUNICIPIO", ano, 5, 0, 500.0))
        for cancer in ("Mama", "Ovário", "Tireoide"):
            linhas.append((cancer, "SP", ano, 1000 + 10 * i, 50, 1e6))
    return pd.DataFrame(linhas, columns=["tipo_cancer", "grupo", "ano", "internacoes", "obitos", "valor_total"])


# ---- A. projeção de uma reta perfeita é exata ----
serie = serie_sintetica()
proj = projetar(serie)
mama_2026 = proj[(proj["tipo_cancer"] == "Mama") & (proj["grupo"] == "MUNICIPIO") & (proj["ano"] == 2026)]
checar("A. reta perfeita: 2026 previsto = 36 (10 + 2*13)", abs(mama_2026["internacoes"].iloc[0] - 36) < 1e-6)
checar("A. reta perfeita: faixa provável sem largura",
       abs(mama_2026["internacoes_max"].iloc[0] - mama_2026["internacoes_min"].iloc[0]) < 1e-6)

# ---- B. ano sem registro entra como zero, e previsão nunca é negativa ----
tireoide = proj[(proj["tipo_cancer"] == "Tireoide") & (proj["grupo"] == "MUNICIPIO")]
checar("B. anos sem internação completados com zero",
       len(tireoide[tireoide["tipo"] == "historico"]) == 13)
checar("B. previsão e faixa nunca abaixo de zero",
       (tireoide[["internacoes", "internacoes_min"]].fillna(0) >= 0).all().all())

# ---- C. prioridades: percentuais somam 100 e seguem a lógica ----
prior = calcular_prioridades(serie)
checar("C. percentuais do orçamento somam 100%", abs(prior["pct_orcamento"].sum() - 100) < 1e-6)
checar("C. doença que cresce e tem rastreamento fica em 1º", prior.iloc[0]["tipo_cancer"] == "Mama")
checar("C. doença que sumiu fica por último", prior.iloc[-1]["tipo_cancer"] == "Tireoide")
ovario = prior[prior["tipo_cancer"] == "Ovário"].iloc[0]
checar("C. letalidade encolhida para o Estado (entre 5% de SP e 50% do município)",
       5 < ovario["letalidade_pct"] < 50)

# ---- D. pesos mudam a decisão ----
so_letalidade = {k: 0 for k in PESOS_PADRAO}
so_letalidade["letalidade"] = 1
prior_let = calcular_prioridades(serie, so_letalidade)
checar("D. só com peso em letalidade, a doença grave vira 1ª",
       prior_let.iloc[0]["tipo_cancer"] == "Ovário")

# ---- E. distribuição em reais ----
dist = distribuir_orcamento(prior, 1_000_000)
checar("E. distribuição em reais soma o orçamento", abs(dist["valor_sugerido"].sum() - 1_000_000) < 1e-3)

# ---- F. nomes do banco e ação certa (colorretal NÃO é colo do útero) ----
checar("F. 'COLORRETAL' recebe sangue oculto, não Papanicolau",
       "sangue oculto" in potencial_prevencao("COLORRETAL")[1])
checar("F. 'COLO_UTERO' recebe Papanicolau", "Papanicolau" in potencial_prevencao("COLO_UTERO")[1])
checar("F. 'Pulmão' com acento reconhecido", "tabagismo" in potencial_prevencao("Pulmão")[1])

# ---- G. formato brasileiro ----
checar("G. 1234567.891 -> '1.234.567,9'", formatar_numero(1234567.891) == "1.234.567,9")

# ---- H. base pública real 2013-2025 ----
if os.path.exists(CSV_REAL):
    real = carregar_serie_csv(CSV_REAL)
    prior_real = calcular_prioridades(real)
    checar("H. base real: 7 cânceres priorizados", len(prior_real) == 7)
    checar("H. base real: percentuais somam 100%", abs(prior_real["pct_orcamento"].sum() - 100) < 1e-6)
    checar("H. base real: 2025 atípico no Estado para todos os cânceres",
           bool(prior_real["ultimo_ano_atipico_sp"].all()))
    val = validar(real)
    checar("H. base real: backtest cobre as 7 doenças com 3 anos cada",
           len(val) == 7 and (val["anos_testados"] == 3).all())
else:
    print("(pulado) H. base real não encontrada em " + CSV_REAL)

print()
if falhas:
    print(f"{len(falhas)} checagem(ns) falharam.")
    raise SystemExit(1)
print("Todas as checagens passaram.")
