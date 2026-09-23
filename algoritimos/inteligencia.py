import math
import sqlite3
import unicodedata

import numpy as np
import pandas as pd

# =====================================
# INTELIGÊNCIA CENTRAL DO ESCUDO
#
# Um lugar só para calcular o que a tela e o chat mostram. Antes,
# cada aba do dashboard fazia a sua própria consulta a `internacoes`
# e a mesma informação aparecia (e podia divergir) em vários lugares.
# Aqui cada conta é feita uma vez; quem exibe só lê o resultado.
#
# Funções puras (recebem DataFrame, devolvem DataFrame/dict), para
# poderem ser testadas sem o banco do Windows -- ver
# teste_inteligencia.py.
#
# Regras que valem para tudo daqui:
#   - SIH/SUS registra internações (AIH), não casos novos.
#   - O ano é o de competência/processamento da AIH (ANO_CMPT),
#     não necessariamente o ano em que a internação aconteceu.
#   - Detectar um comportamento fora do padrão NÃO explica a causa.
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

GRUPO_MUNICIPIO = "MUNICIPIO"
GRUPO_ESTADO = "SP"

# No banco os cânceres vêm como códigos (MAMA, COLO_UTERO ...).
NOMES_DOENCAS = {
    "MAMA": "Mama",
    "COLO_UTERO": "Colo do útero",
    "COLORRETAL": "Colorretal",
    "OVARIO": "Ovário",
    "PELE_NAO_MELANOMA": "Pele não melanoma",
    "PULMAO": "Pulmão",
    "TIREOIDE": "Tireoide",
}

# Anos fora do padrão: a diferença para o esperado precisa passar
# de LIMIAR_DESVIOS "desvios" E ser de pelo menos DIFERENCA_MINIMA
# internações. A segunda regra existe para cidades pequenas, onde
# 1 -> 3 internações seria "+200%" sem significar nada.
LIMIAR_DESVIOS = 2.5
DIFERENCA_MINIMA = 3

# Abaixo desta média anual, qualquer leitura da série leva o aviso
# de "números pequenos".
MEDIA_PEQUENA = 10

Z_90 = 1.645  # faixa provável de ~90% da projeção


# =====================================
# FORMATAÇÃO
# =====================================

def _sem_acento(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c))


def nome_doenca(codigo):
    """'COLO_UTERO' -> 'Colo do útero'. Nome desconhecido vira
    'Primeira maiúscula' em vez de sumir."""
    chave = _sem_acento(codigo).upper().replace(" ", "_")
    if chave in NOMES_DOENCAS:
        return NOMES_DOENCAS[chave]
    texto = str(codigo).replace("_", " ").strip().lower()
    return texto[:1].upper() + texto[1:]


def formatar_numero(valor, casas=0):
    """1234.5 -> '1.234,5' (padrão brasileiro)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


# =====================================
# CARREGAMENTO (única consulta a `internacoes`)
# =====================================

SQL_MUNICIPIO = """
SELECT tipo_cancer, origem, ano,
       COUNT(*) AS internacoes,
       COALESCE(SUM(obito), 0) AS obitos,
       COALESCE(SUM(valor_total), 0) AS valor_total,
       COALESCE(SUM(dias_permanencia), 0) AS dias_permanencia
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer, origem, ano
"""

SQL_ESTADO = """
SELECT tipo_cancer, 'SP' AS grupo, ano,
       COUNT(*) AS internacoes,
       COALESCE(SUM(obito), 0) AS obitos,
       COALESCE(SUM(valor_total), 0) AS valor_total,
       COALESCE(SUM(dias_permanencia), 0) AS dias_permanencia
FROM internacoes
WHERE origem = ?
GROUP BY tipo_cancer, ano
"""


def escolher_uma_fonte(linhas_municipio, uf_referencia="SP"):
    """As moradoras de Rio Claro podem estar em `internacoes` duas
    vezes com municipio = 'RIO_CLARO': vindas do arquivo de Rio
    Claro (origem RIO_CLARO) E do arquivo estadual (origem SP), que
    traz todas as cidades. Somar tudo por `municipio` contaria essas
    internações em dobro. Por isso usamos UMA fonte por cidade: a
    estadual, que é a mesma para todas as cidades (comparação
    justa); o arquivo próprio da cidade só entra se ela não estiver
    no estadual."""
    if linhas_municipio.empty:
        return linhas_municipio
    fontes = linhas_municipio["origem"].unique()
    fonte = uf_referencia if uf_referencia in fontes else fontes[0]
    return linhas_municipio[linhas_municipio["origem"] == fonte]


def carregar_serie(conexao, municipio, uf_referencia="SP"):
    """Série anual por câncer do município e da referência
    estadual. Tudo o que o dashboard mostra sai daqui."""
    mun = pd.read_sql(SQL_MUNICIPIO, conexao, params=(municipio,))
    mun = escolher_uma_fonte(mun, uf_referencia).drop(columns="origem")
    mun.insert(1, "grupo", GRUPO_MUNICIPIO)
    est = pd.read_sql(SQL_ESTADO, conexao, params=(uf_referencia,))
    serie = pd.concat([mun, est], ignore_index=True)
    serie = serie[serie["tipo_cancer"].notna()]
    return completar_anos(serie) if not serie.empty else serie


def completar_anos(serie):
    """Uma linha por (câncer, grupo, ano) no período inteiro, com
    zero onde não houve internação: ano sem registro é informação
    (zero), não dado faltante. Sem isso, uma cidade pequena com
    internação só em 2014 e 2020 ganharia uma "reta" entre os dois."""
    anos = range(int(serie["ano"].min()), int(serie["ano"].max()) + 1)
    indice = pd.MultiIndex.from_product(
        [serie["tipo_cancer"].unique(), serie["grupo"].unique(), anos],
        names=["tipo_cancer", "grupo", "ano"],
    )
    return (serie.set_index(["tipo_cancer", "grupo", "ano"])
                 .reindex(indice, fill_value=0)
                 .reset_index())


def serie_doenca(serie, cancer, grupo=GRUPO_MUNICIPIO):
    return (serie[(serie["tipo_cancer"] == cancer) & (serie["grupo"] == grupo)]
            .sort_values("ano").reset_index(drop=True))


# =====================================
# PANORAMA: quais doenças pesam mais
# =====================================

def resumo_doencas(serie):
    """Totais do município por câncer no período, maior primeiro."""
    mun = serie[serie["grupo"] == GRUPO_MUNICIPIO]
    resumo = (mun.groupby("tipo_cancer", as_index=False)
                 [["internacoes", "obitos", "valor_total"]].sum())
    resumo = resumo[resumo["internacoes"] > 0]
    resumo["doenca"] = resumo["tipo_cancer"].map(nome_doenca)
    return resumo.sort_values("internacoes", ascending=False).reset_index(drop=True)


# =====================================
# TENDÊNCIA
# =====================================

def ajustar_tendencia(anos, valores):
    """Reta de mínimos quadrados + o necessário para a faixa de
    previsão."""
    x = np.asarray(anos, dtype=float)
    y = np.asarray(valores, dtype=float)
    n = len(x)
    if n < 3:
        media = float(y.mean()) if n else 0.0
        return {"inclinacao": 0.0, "intercepto": media,
                "x_medio": float(x.mean()) if n else 0.0,
                "sxx": 1.0, "s": float(y.std()) if n else 0.0, "n": n}
    x_medio = x.mean()
    sxx = float(((x - x_medio) ** 2).sum())
    inclinacao = float(((x - x_medio) * (y - y.mean())).sum() / sxx)
    intercepto = float(y.mean() - inclinacao * x_medio)
    residuos = y - (intercepto + inclinacao * x)
    s = float(np.sqrt((residuos ** 2).sum() / (n - 2)))
    return {"inclinacao": inclinacao, "intercepto": intercepto,
            "x_medio": float(x_medio), "sxx": sxx, "s": s, "n": n}


def prever(modelo, anos):
    """Ponto e faixa de ~90%, nunca abaixo de zero."""
    x0 = np.asarray(anos, dtype=float)
    ponto = modelo["intercepto"] + modelo["inclinacao"] * x0
    erro = modelo["s"] * np.sqrt(
        1 + 1 / max(modelo["n"], 1) + (x0 - modelo["x_medio"]) ** 2 / modelo["sxx"])
    return (np.clip(ponto, 0, None),
            np.clip(ponto - Z_90 * erro, 0, None),
            np.clip(ponto + Z_90 * erro, 0, None))


def ritmo_anual_pct(dados):
    """Inclinação da tendência em % da média anual: o "ritmo",
    comparável entre cidade e Estado apesar do tamanho diferente."""
    media = dados["internacoes"].mean()
    if media <= 0:
        return 0.0
    return ajustar_tendencia(dados["ano"], dados["internacoes"])["inclinacao"] / media * 100


# =====================================
# COMPARAÇÃO COM O ESTADO
# =====================================

def ritmo_estadual_na_escala(serie, cancer):
    """A série do Estado redimensionada para o tamanho do município
    (mesmo total no período). Assim as duas linhas ficam no MESMO
    eixo, em internações, e a leitura é direta: onde a linha da
    cidade passa acima da cinza, a cidade cresceu mais que o
    Estado. Evita o gráfico de dois eixos, que engana."""
    mun = serie_doenca(serie, cancer, GRUPO_MUNICIPIO)
    est = serie_doenca(serie, cancer, GRUPO_ESTADO)
    if est.empty or est["internacoes"].sum() == 0 or mun.empty:
        return pd.DataFrame(columns=["ano", "internacoes"])
    fator = mun["internacoes"].sum() / est["internacoes"].sum()
    return pd.DataFrame({"ano": est["ano"], "internacoes": est["internacoes"] * fator})


def comparar_com_estado(serie, cancer):
    mun = serie_doenca(serie, cancer, GRUPO_MUNICIPIO)
    est = serie_doenca(serie, cancer, GRUPO_ESTADO)
    ritmo_mun = ritmo_anual_pct(mun)
    ritmo_est = ritmo_anual_pct(est) if not est.empty else None
    return {"ritmo_municipio": ritmo_mun, "ritmo_estado": ritmo_est}


# =====================================
# ANOS FORA DO PADRÃO
# =====================================

def anos_fora_do_padrao(dados):
    """Para cada ano, o "esperado" é a tendência calculada com os
    OUTROS anos (o próprio ano não entra, senão um pico puxaria a
    reta para si e se esconderia). O ano é marcado quando a
    diferença passa de LIMIAR_DESVIOS desvios -- o maior entre a
    oscilação normal da série e a oscilação natural de contagens
    (raiz do esperado) -- e tem pelo menos DIFERENCA_MINIMA
    internações. Só detecta; não explica a causa."""
    dados = dados.sort_values("ano")
    if len(dados) < 6:
        return pd.DataFrame(columns=["ano", "observado", "esperado", "direcao", "numeros_pequenos"])
    linhas = []
    for ano in dados["ano"]:
        outros = dados[dados["ano"] != ano]
        modelo = ajustar_tendencia(outros["ano"], outros["internacoes"])
        esperado = max(float(modelo["intercepto"] + modelo["inclinacao"] * ano), 0.0)
        observado = float(dados.loc[dados["ano"] == ano, "internacoes"].iloc[0])
        desvio = max(modelo["s"], math.sqrt(max(esperado, 1.0)))
        diferenca = observado - esperado
        if abs(diferenca) > LIMIAR_DESVIOS * desvio and abs(diferenca) >= DIFERENCA_MINIMA:
            linhas.append({
                "ano": int(ano),
                "observado": observado,
                "esperado": esperado,
                "direcao": "acima" if diferenca > 0 else "abaixo",
                "numeros_pequenos": esperado < MEDIA_PEQUENA,
            })
    return pd.DataFrame(linhas, columns=["ano", "observado", "esperado", "direcao", "numeros_pequenos"])


def ano_atipico_no_estado(serie, ano):
    """Quantos cânceres tiveram `ano` fora do padrão no Estado. Se
    forem todos ao mesmo tempo, é mais provável uma mudança no
    registro/processamento do que em todas as doenças juntas."""
    canceres = serie[serie["grupo"] == GRUPO_ESTADO]["tipo_cancer"].unique()
    fora = sum(
        ano in set(anos_fora_do_padrao(serie_doenca(serie, c, GRUPO_ESTADO))["ano"])
        for c in canceres
    )
    return fora, len(canceres)


# =====================================
# PROJEÇÃO EXPLORATÓRIA
# =====================================

def projetar(dados, horizonte=3):
    """Continuação da tendência histórica com faixa de ~90%.
    Exploratória: descreve o que acontece SE o comportamento
    passado continuar -- não é previsão clínica nem causal."""
    dados = dados.sort_values("ano")
    ultimo = int(dados["ano"].max())
    anos = list(range(ultimo + 1, ultimo + 1 + horizonte))
    ponto, minimo, maximo = prever(ajustar_tendencia(dados["ano"], dados["internacoes"]), anos)
    return pd.DataFrame({"ano": anos, "internacoes": ponto,
                         "minimo": minimo, "maximo": maximo})


def testar_projecao(dados, anos_teste=3):
    """Treina até (último - anos_teste) e compara o erro nos anos
    seguintes com o de simplesmente repetir a média dos 3 últimos
    anos de treino."""
    dados = dados.sort_values("ano")
    corte = int(dados["ano"].max()) - anos_teste
    treino, teste = dados[dados["ano"] <= corte], dados[dados["ano"] > corte]
    if len(treino) < 3 or teste.empty:
        return None
    ponto, minimo, maximo = prever(ajustar_tendencia(treino["ano"], treino["internacoes"]), teste["ano"])
    real = teste["internacoes"].to_numpy(dtype=float)
    return {
        "erro_tendencia": float(np.abs(real - ponto).mean()),
        "erro_media": float(np.abs(real - treino["internacoes"].tail(3).mean()).mean()),
        "dentro_da_faixa": int(((real >= minimo) & (real <= maximo)).sum()),
        "anos_testados": len(real),
    }


# =====================================
# LEITURAS (frases que acompanham os gráficos)
# =====================================

def leitura_evolucao(serie, cancer):
    """Frases curtas, calculadas, que acompanham o gráfico de
    evolução. A mesma lista pode alimentar o chat."""
    mun = serie_doenca(serie, cancer, GRUPO_MUNICIPIO)
    frases = []
    if mun.empty or mun["internacoes"].sum() == 0:
        return frases

    comp = comparar_com_estado(serie, cancer)
    ritmo = comp["ritmo_municipio"]
    if abs(ritmo) < 1:
        frases.append("As internações ficaram praticamente estáveis ao longo do período.")
    else:
        frases.append(
            f"As internações {'cresceram' if ritmo > 0 else 'caíram'} em média "
            f"{formatar_numero(abs(ritmo), 1)}% ao ano de {int(mun['ano'].min())} a {int(mun['ano'].max())}."
        )

    if comp["ritmo_estado"] is not None:
        diferenca = ritmo - comp["ritmo_estado"]
        ritmo_est = formatar_numero(comp["ritmo_estado"], 1)
        if abs(diferenca) < 1.5:
            frases.append(f"O ritmo é parecido com o do Estado de SP ({ritmo_est}% ao ano).")
        elif diferenca > 0:
            frases.append(f"O ritmo é mais rápido que o do Estado de SP ({ritmo_est}% ao ano).")
        else:
            frases.append(f"O ritmo é mais lento que o do Estado de SP ({ritmo_est}% ao ano).")

    fora = anos_fora_do_padrao(mun)
    for _, linha in fora.iterrows():
        frases.append(
            f"{linha['ano']} ficou {linha['direcao']} do esperado pela tendência "
            f"({formatar_numero(linha['observado'])} internações; o esperado era cerca de "
            f"{formatar_numero(linha['esperado'])})."
        )

    if mun["internacoes"].mean() < MEDIA_PEQUENA:
        frases.append(
            "Números pequenos: com poucas internações por ano, variações de um ano "
            "para outro podem ser acaso. Confirme antes de concluir."
        )
    return frases
