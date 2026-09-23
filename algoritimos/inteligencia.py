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


def cancer_de(codigo):
    """'MAMA' -> 'câncer de mama'; 'COLORRETAL' -> 'câncer colorretal'
    (sem o "de", que fica errado em português)."""
    nome = nome_doenca(codigo).lower()
    return "câncer colorretal" if nome == "colorretal" else f"câncer de {nome}"


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
    no estadual. A escolha é por câncer: um câncer sem arquivo
    estadual continua valendo pelo arquivo da cidade.
    (etl/carga_todas_bases.py já evita a duplicidade na carga; isto
    protege bancos carregados antes da correção.)"""
    if linhas_municipio.empty:
        return linhas_municipio
    partes = []
    for _, linhas in linhas_municipio.groupby("tipo_cancer"):
        fontes = linhas["origem"].unique()
        fonte = uf_referencia if uf_referencia in fontes else fontes[0]
        partes.append(linhas[linhas["origem"] == fonte])
    return pd.concat(partes, ignore_index=True)


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
                 [["internacoes", "obitos", "valor_total", "dias_permanencia"]].sum())
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
    """Detecta anos internos da série que se afastam da tendência.

    O ano analisado é retirado do ajuste para não "puxar" a própria
    reta. Mas o primeiro e o último ano da série NÃO são testados:
    para eles a tendência ajustada aos outros anos precisaria ser
    extrapolada para fora do intervalo observado, o que pode criar
    esperados artificialmente próximos de zero e percentuais enormes
    (por exemplo, 6 observadas contra 0,8 esperadas).

    Assim, "fora do padrão" significa uma anomalia dentro do intervalo
    histórico observado, não uma extrapolação nas pontas da série.
    Só detecta; não explica a causa."""
    dados = dados.sort_values("ano").reset_index(drop=True)
    if len(dados) < 6:
        return pd.DataFrame(columns=["ano", "observado", "esperado", "direcao", "numeros_pequenos"])

    # Precisamos de anos dos dois lados para avaliar um ponto sem
    # extrapolar. Por isso as pontas (primeiro/último) ficam fora.
    anos_avaliados = dados["ano"].iloc[1:-1]

    linhas = []
    for ano in anos_avaliados:
        outros = dados[dados["ano"] != ano]
        modelo = ajustar_tendencia(outros["ano"], outros["internacoes"])

        # Aqui o ano está dentro do intervalo dos dados usados no
        # ajuste; portanto não há extrapolação.
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

def projetar(dados, horizonte=3, coluna="internacoes"):
    """Projeção de tendência: continuação da reta histórica com faixa
    de ~90%. Descreve o que acontece SE o comportamento passado
    continuar -- não é previsão clínica nem causal, e não deve ser
    chamada de "IA preditiva". `coluna` permite projetar também os
    valores hospitalares registrados e os dias de internação."""
    dados = dados.sort_values("ano")
    ultimo = int(dados["ano"].max())
    anos = list(range(ultimo + 1, ultimo + 1 + horizonte))
    ponto, minimo, maximo = prever(ajustar_tendencia(dados["ano"], dados[coluna]), anos)
    return pd.DataFrame({"ano": anos, coluna: ponto,
                         "minimo": minimo, "maximo": maximo})


def testar_projecao(dados, anos_teste=3, coluna="internacoes"):
    """Treina até (último - anos_teste) e compara o erro nos anos
    seguintes com o de simplesmente repetir a média dos 3 últimos
    anos de treino."""
    dados = dados.sort_values("ano")
    corte = int(dados["ano"].max()) - anos_teste
    treino, teste = dados[dados["ano"] <= corte], dados[dados["ano"] > corte]
    if len(treino) < 3 or teste.empty:
        return None
    ponto, minimo, maximo = prever(ajustar_tendencia(treino["ano"], treino[coluna]), teste["ano"])
    real = teste[coluna].to_numpy(dtype=float)
    return {
        "erro_tendencia": float(np.abs(real - ponto).mean()),
        "erro_media": float(np.abs(real - treino[coluna].tail(3).mean()).mean()),
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


# =====================================
# FICHA DE UM CÂNCER: "o que chama atenção?"
#
# Dinheiro aqui é "valor hospitalar registrado no SIH/SUS" (VAL_TOT
# das AIHs): o que o SUS registrou pelas internações. NÃO é o
# orçamento municipal nem o custo total do tratamento (quimioterapia
# e radioterapia ambulatoriais ficam fora).
# =====================================

def _razao(num, den):
    return num / den if den else 0.0


def ficha_cancer(serie, cancer):
    """Os quatro números da doença (internações, óbitos, valor
    hospitalar registrado, dias), cada um com a sua referência."""
    mun = serie_doenca(serie, cancer, GRUPO_MUNICIPIO)
    est = serie_doenca(serie, cancer, GRUPO_ESTADO)
    todos = serie[serie["grupo"] == GRUPO_MUNICIPIO]
    intern, obitos = mun["internacoes"].sum(), mun["obitos"].sum()
    valor, dias = mun["valor_total"].sum(), mun["dias_permanencia"].sum()
    return {
        "internacoes": float(intern),
        "obitos": float(obitos),
        "valor": float(valor),
        "dias": float(dias),
        "pct_internacoes": _razao(intern, todos["internacoes"].sum()) * 100,
        "pct_valor": _razao(valor, todos["valor_total"].sum()) * 100,
        "letalidade": _razao(obitos, intern) * 100,
        "letalidade_estado": _razao(est["obitos"].sum(), est["internacoes"].sum()) * 100,
        "valor_medio": _razao(valor, intern),
        "valor_medio_estado": _razao(est["valor_total"].sum(), est["internacoes"].sum()),
        "permanencia": _razao(dias, intern),
        "permanencia_estado": _razao(est["dias_permanencia"].sum(), est["internacoes"].sum()),
    }


def destaques_cancer(serie, cancer):
    """Frases de "o que chama atenção", só quando o número sustenta.
    Nenhuma afirma causa."""
    f = ficha_cancer(serie, cancer)
    frases = [f"Concentra {formatar_numero(f['pct_internacoes'], 1)}% das internações e "
              f"{formatar_numero(f['pct_valor'], 1)}% do valor hospitalar registrado entre os cânceres acompanhados."]
    if f["pct_valor"] - f["pct_internacoes"] > 3:
        frases.append(f"Pesa mais no valor registrado do que no número de internações: cada internação por "
                      f"{cancer_de(cancer)} registra, em média, R$ {formatar_numero(f['valor_medio'])}.")
    if f["obitos"] >= 5 and f["letalidade"] > f["letalidade_estado"] * 1.2:
        frases.append(f"Letalidade hospitalar de {formatar_numero(f['letalidade'], 1)}%, acima da do Estado "
                      f"({formatar_numero(f['letalidade_estado'], 1)}%).")
    elif f["obitos"] >= 5 and f["letalidade"] < f["letalidade_estado"] * 0.8:
        frases.append(f"Letalidade hospitalar de {formatar_numero(f['letalidade'], 1)}%, abaixo da do Estado "
                      f"({formatar_numero(f['letalidade_estado'], 1)}%).")
    if f["permanencia_estado"] and abs(f["permanencia"] - f["permanencia_estado"]) >= 1:
        frases.append(f"Cada internação dura em média {formatar_numero(f['permanencia'], 1)} dias "
                      f"(no Estado, {formatar_numero(f['permanencia_estado'], 1)}).")
    comp = comparar_com_estado(serie, cancer)
    if comp["ritmo_estado"] is not None and comp["ritmo_municipio"] - comp["ritmo_estado"] > 1.5:
        frases.append(f"As internações crescem mais rápido que no Estado "
                      f"({formatar_numero(comp['ritmo_municipio'], 1)}% x {formatar_numero(comp['ritmo_estado'], 1)}% ao ano).")
    fora = anos_fora_do_padrao(serie_doenca(serie, cancer))
    if not fora.empty:
        anos = ", ".join(f"{a} ({d})" for a, d in zip(fora["ano"], fora["direcao"]))
        frases.append(f"Anos fora do padrão: {anos}.")
    return frases


# =====================================
# CONFIABILIDADE DA INFORMAÇÃO
#
# Antes de interpretar, dizer o que pode enganar. Cada aviso vem
# de uma checagem nos dados, não de um texto fixo.
# =====================================

SQL_DUPLICIDADE = """
SELECT tipo_cancer
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer
HAVING COUNT(DISTINCT origem) > 1
"""


def canceres_com_duplicidade(conexao, municipio):
    """Cânceres cuja cidade tem internações vindas de duas fontes no
    banco (a contagem em dobro de Rio Claro). O Escudo já usa uma
    fonte só; o aviso diz que o banco precisa ser recarregado."""
    return [linha[0] for linha in conexao.execute(SQL_DUPLICIDADE, (municipio,)).fetchall()]


def confiabilidade(serie, cancer, duplicados=()):
    """Lista de (nível, texto). nível: 'atencao' ou 'info'."""
    mun = serie_doenca(serie, cancer)
    avisos = []
    if cancer in duplicados:
        avisos.append(("atencao", "O banco deste computador ainda tem estas internações em duplicidade (arquivo "
                                  "da cidade + arquivo estadual). Os números da tela já estão certos: o Escudo "
                                  "usa só o estadual. Para o aviso sumir, recarregue os dados: "
                                  "py etl\\carga_todas_bases.py"))
    ano_fim = int(serie["ano"].max())
    fora, total = ano_atipico_no_estado(serie, ano_fim)
    if total and fora >= total / 2:
        avisos.append(("atencao", f"{ano_fim} está em investigação: {fora} dos {total} cânceres saltaram ao "
                                  f"mesmo tempo no Estado, o que sugere mudança de registro."))
    if mun["internacoes"].mean() < MEDIA_PEQUENA:
        avisos.append(("atencao", f"Números pequenos: média de {formatar_numero(mun['internacoes'].mean(), 1)} "
                                  f"internações por ano. Variações podem ser acaso."))
    if mun["obitos"].sum() < 10:
        avisos.append(("info", "Menos de 10 óbitos no período: a letalidade é pouco estável."))
    anos_com_dado = int((mun["internacoes"] > 0).sum())
    if anos_com_dado < 8:
        avisos.append(("info", f"Só {anos_com_dado} dos {len(mun)} anos têm internações: série curta para tendência."))
    avisos.append(("info", "Sem população por município no banco: comparações são de ritmo, não de taxa "
                           "por 100 mil mulheres."))
    return avisos


# =====================================
# INVESTIGAÇÃO
# =====================================

def anos_fora_todos(serie, grupo=GRUPO_MUNICIPIO):
    """Todos os anos fora do padrão, de todos os cânceres, numa
    tabela só -- para quem quer procurar, não só olhar um câncer."""
    partes = []
    for cancer in serie["tipo_cancer"].unique():
        fora = anos_fora_do_padrao(serie_doenca(serie, cancer, grupo))
        if not fora.empty:
            fora = fora.copy()
            fora.insert(0, "doenca", nome_doenca(cancer))
            fora["diferenca_pct"] = [(_razao(o - e, e) * 100 if e else float("nan"))
                                     for o, e in zip(fora["observado"], fora["esperado"])]
            partes.append(fora)
    if not partes:
        return pd.DataFrame(columns=["doenca", "ano", "observado", "esperado", "direcao",
                                     "numeros_pequenos", "diferenca_pct"])
    return pd.concat(partes, ignore_index=True).sort_values(["ano", "doenca"]).reset_index(drop=True)


def quando_aparece(serie):
    """Para cada câncer: primeiro ano com internação, ano de pico,
    em quantos anos aparece (persistência) e o ritmo. Responde
    "em que anos as doenças aparecem" nos seus vários sentidos."""
    linhas = []
    for cancer in resumo_doencas(serie)["tipo_cancer"]:
        mun = serie_doenca(serie, cancer)
        com = mun[mun["internacoes"] > 0]
        anos_com, total = len(com), len(mun)
        pico = mun.loc[mun["internacoes"].idxmax()]
        persistencia = ("todos os anos" if anos_com == total else
                        "quase todos os anos" if anos_com >= total * 0.75 else "episódica")
        linhas.append({
            "doenca": nome_doenca(cancer),
            "primeiro_ano": int(com["ano"].min()) if anos_com else None,
            "anos_com_internacao": f"{anos_com} de {total}",
            "persistencia": persistencia,
            "ano_de_pico": int(pico["ano"]),
            "internacoes_no_pico": int(pico["internacoes"]),
            "ritmo_anual_pct": round(ritmo_anual_pct(mun), 1),
        })
    return pd.DataFrame(linhas)


# Faixas escolhidas pelas diretrizes: 50-69 é a faixa do rastreamento
# de câncer de mama recomendado pelo INCA.
FAIXAS = [("até 39 anos", 0, 39), ("40 a 49", 40, 49), ("50 a 69", 50, 69), ("70 ou mais", 70, 200)]

SQL_FAIXAS = """
SELECT tipo_cancer, origem, ano,
       CASE WHEN idade < 40 THEN 'até 39 anos'
            WHEN idade < 50 THEN '40 a 49'
            WHEN idade < 70 THEN '50 a 69'
            ELSE '70 ou mais' END AS faixa,
       COUNT(*) AS internacoes
FROM internacoes
WHERE municipio = ? AND idade IS NOT NULL
GROUP BY tipo_cancer, origem, ano, faixa
"""


def carregar_faixas(conexao, municipio, uf_referencia="SP"):
    """Internações por câncer x ano x faixa etária, com a mesma regra
    de uma fonte por cidade (não conta Rio Claro em dobro)."""
    dados = pd.read_sql(SQL_FAIXAS, conexao, params=(municipio,))
    if dados.empty:
        return dados.drop(columns="origem")
    return escolher_uma_fonte(dados, uf_referencia).drop(columns="origem")


def comparar_faixas(faixas, cancer):
    """Distribuição por faixa etária na primeira e na segunda metade
    do período, para responder "a idade das internações mudou?"."""
    dados = faixas[faixas["tipo_cancer"] == cancer]
    if dados.empty:
        return pd.DataFrame(columns=["faixa", "periodo", "internacoes", "pct"]), None
    anos = sorted(dados["ano"].unique())
    meio = anos[len(anos) // 2]
    periodos = {f"{anos[0]}–{meio - 1}": dados[dados["ano"] < meio],
                f"{meio}–{anos[-1]}": dados[dados["ano"] >= meio]}
    linhas = []
    for periodo, parte in periodos.items():
        total = parte["internacoes"].sum()
        for faixa, _, _ in FAIXAS:
            n = parte[parte["faixa"] == faixa]["internacoes"].sum()
            linhas.append({"faixa": faixa, "periodo": periodo, "internacoes": int(n),
                           "pct": _razao(n, total) * 100})
    tabela = pd.DataFrame(linhas)
    return tabela, list(periodos)


def leitura_faixas(tabela, periodos):
    """A faixa que mais mudou de participação entre os dois períodos."""
    if tabela.empty or periodos is None:
        return []
    antes = tabela[tabela["periodo"] == periodos[0]].set_index("faixa")["pct"]
    depois = tabela[tabela["periodo"] == periodos[1]].set_index("faixa")["pct"]
    variacao = (depois - antes).dropna()
    faixa = variacao.abs().idxmax()
    total = tabela["internacoes"].sum()
    frases = []
    if abs(variacao[faixa]) >= 5:
        frases.append(f"A faixa de {faixa} passou de {formatar_numero(antes[faixa], 1)}% para "
                      f"{formatar_numero(depois[faixa], 1)}% das internações entre {periodos[0]} e {periodos[1]}.")
    else:
        frases.append("A distribuição por idade ficou parecida entre os dois períodos "
                      "(nenhuma faixa mudou 5 pontos ou mais).")
    if total < 60:
        frases.append("Poucas internações para dividir em faixas: leia como indício, não como conclusão.")
    return frases


# =====================================
# PLANEJAMENTO: evidências, nunca valor de orçamento
# =====================================

# Linhas de ação conhecidas (diretrizes do INCA). Possibilidades para a
# discussão da gestão, não recomendação de gasto.
LINHAS_DE_ACAO = {
    "MAMA": "rastreamento recomendado: mamografia de 50 a 69 anos",
    "COLO_UTERO": "rastreamento recomendado (exame preventivo / DNA-HPV) e vacina contra HPV",
    "COLORRETAL": "rastreamento possível: pesquisa de sangue oculto nas fezes",
    "PELE_NAO_MELANOMA": "prevenção por fotoproteção e exame de lesões na atenção básica",
    "PULMAO": "prevenção pelo controle do tabagismo",
}


def pressao_projetada(serie, cancer, horizonte=3):
    """Se a tendência continuar: internações, dias de internação e
    valor hospitalar registrado no último ano do horizonte, cada um
    com faixa e com o resultado do teste de acerto. Óbitos não são
    projetados: são poucos por ano e a reta seria enganosa."""
    mun = serie_doenca(serie, cancer)
    resultado = {}
    for coluna in ("internacoes", "dias_permanencia", "valor_total"):
        proj = projetar(mun, horizonte, coluna).iloc[-1]
        teste = testar_projecao(mun, coluna=coluna)
        resultado[coluna] = {
            "ano": int(proj["ano"]),
            "atual": float(mun[coluna].iloc[-1]),
            "previsto": float(proj[coluna]),
            "minimo": float(proj["minimo"]),
            "maximo": float(proj["maximo"]),
            "tendencia_acerta_mais": bool(teste and teste["erro_tendencia"] <= teste["erro_media"]),
        }
    return resultado


def evidencias_planejamento(serie):
    """Para cada câncer: sinais com o número que os sustenta, a
    pressão projetada e a linha de ação conhecida. Ordenado por
    quantidade de sinais. O Escudo não define quanto investir."""
    ano_fim = int(serie["ano"].max())
    linhas = []
    for cancer in resumo_doencas(serie)["tipo_cancer"]:
        f = ficha_cancer(serie, cancer)
        comp = comparar_com_estado(serie, cancer)
        sinais = []
        if comp["ritmo_municipio"] >= 3:
            sinais.append(f"internações crescem {formatar_numero(comp['ritmo_municipio'], 1)}% ao ano")
        if comp["ritmo_estado"] is not None and comp["ritmo_municipio"] - comp["ritmo_estado"] > 1.5:
            sinais.append(f"crescem mais rápido que no Estado ({formatar_numero(comp['ritmo_estado'], 1)}% ao ano)")
        if f["obitos"] >= 5 and f["letalidade"] > f["letalidade_estado"] * 1.2:
            sinais.append(f"letalidade hospitalar de {formatar_numero(f['letalidade'], 1)}%, acima do Estado "
                          f"({formatar_numero(f['letalidade_estado'], 1)}%)")
        if f["pct_valor"] >= 20:
            sinais.append(f"responde por {formatar_numero(f['pct_valor'], 1)}% do valor hospitalar registrado")
        fora = anos_fora_do_padrao(serie_doenca(serie, cancer))
        recentes = fora[(fora["direcao"] == "acima") & (fora["ano"] >= ano_fim - 2) & (fora["ano"] < ano_fim)]
        for ano in recentes["ano"]:
            sinais.append(f"{ano} ficou acima do esperado")
        linhas.append({
            "tipo_cancer": cancer,
            "doenca": nome_doenca(cancer),
            "sinais": sinais,
            "crescimento": comp["ritmo_municipio"],
            "letalidade_relativa": _razao(f["letalidade"], f["letalidade_estado"]) if f["obitos"] >= 5 else None,
            "internacoes": f["internacoes"],
            "pressao": pressao_projetada(serie, cancer),
            "linha_de_acao": LINHAS_DE_ACAO.get(cancer),
        })
    return sorted(linhas, key=lambda l: -len(l["sinais"]))
