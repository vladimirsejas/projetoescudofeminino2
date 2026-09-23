import os
import sqlite3
import tempfile

import pandas as pd

from inteligencia import (
    anos_fora_do_padrao,
    ano_atipico_no_estado,
    carregar_serie,
    completar_anos,
    escolher_uma_fonte,
    formatar_numero,
    leitura_evolucao,
    nome_doenca,
    projetar,
    resumo_doencas,
    ritmo_estadual_na_escala,
    serie_doenca,
    testar_projecao,
)

# =====================================
# TESTE DA INTELIGÊNCIA CENTRAL
#
# Séries sintéticas com números fáceis de conferir de cabeça, um
# banco sqlite temporário (para a regra de "uma fonte por cidade")
# e a base pública real analises/base_preditiva_2013_2025.csv.
# Não precisa do banco do Windows.
# =====================================

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CSV_REAL = os.path.join(DIRETORIO_ATUAL, "..", "analises", "base_preditiva_2013_2025.csv")

falhas = []


def checar(nome, condicao):
    print(("OK   " if condicao else "FALHOU ") + nome)
    if not condicao:
        falhas.append(nome)


def serie(valores_municipio, valores_estado=None, cancer="MAMA", ano_inicial=2013):
    linhas = []
    for i, v in enumerate(valores_municipio):
        linhas.append((cancer, "MUNICIPIO", ano_inicial + i, v, 0, 100.0 * v, 3 * v))
    for i, v in enumerate(valores_estado or []):
        linhas.append((cancer, "SP", ano_inicial + i, v, 0, 100.0 * v, 3 * v))
    return completar_anos(pd.DataFrame(linhas, columns=[
        "tipo_cancer", "grupo", "ano", "internacoes", "obitos", "valor_total", "dias_permanencia"]))


# ---- A. nomes ----
checar("A. 'COLO_UTERO' -> 'Colo do útero'", nome_doenca("COLO_UTERO") == "Colo do útero")
checar("A. 'PELE_NAO_MELANOMA' -> 'Pele não melanoma'", nome_doenca("PELE_NAO_MELANOMA") == "Pele não melanoma")
checar("A. nome já bonito continua igual", nome_doenca("Pulmão") == "Pulmão")
checar("A. código desconhecido não some", nome_doenca("NOVO_CANCER") == "Novo cancer")
checar("A. 1234567 -> '1.234.567'", formatar_numero(1234567) == "1.234.567")

# ---- B. ano sem internação vira zero ----
s = completar_anos(pd.DataFrame([
    ("MAMA", "MUNICIPIO", 2013, 5, 0, 1.0, 1), ("MAMA", "MUNICIPIO", 2016, 5, 0, 1.0, 1)],
    columns=["tipo_cancer", "grupo", "ano", "internacoes", "obitos", "valor_total", "dias_permanencia"]))
checar("B. 2014 e 2015 entram com zero", s[s["ano"].isin([2014, 2015])]["internacoes"].tolist() == [0, 0])

# ---- C. anos fora do padrão ----
estavel = [50, 52, 49, 51, 50, 53, 48, 50, 52, 49, 51, 50, 52]
checar("C. série estável: nenhum ano marcado",
       anos_fora_do_padrao(serie_doenca(serie(estavel), "MAMA")).empty)

pico = estavel.copy(); pico[8] = 90  # 2021
fora = anos_fora_do_padrao(serie_doenca(serie(pico), "MAMA"))
checar("C. pico marcado no ano certo e como 'acima'",
       fora["ano"].tolist() == [2021] and fora["direcao"].iloc[0] == "acima")

crescente = [10 + 5 * i for i in range(13)]
checar("C. crescimento regular não é 'fora do padrão'",
       anos_fora_do_padrao(serie_doenca(serie(crescente), "MAMA")).empty)

pequena = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1]  # 1 -> 3: "+200%", mas são 2 internações
checar("C. cidade pequena: 1 -> 3 NÃO é marcado (diferença mínima)",
       anos_fora_do_padrao(serie_doenca(serie(pequena), "MAMA")).empty)

agudos = [3, 4, 2, 4, 7, 2, 3, 3, 1, 4, 3, 12, 5]  # caso real do print (ovário, 2024)
fora = anos_fora_do_padrao(serie_doenca(serie(agudos), "MAMA"))
checar("C. pico de cidade pequena marcado e com aviso de números pequenos",
       fora["ano"].tolist() == [2024] and bool(fora["numeros_pequenos"].iloc[0]))

# ---- D. Estado na escala da cidade ----
s = serie([10] * 13, [1000 + 100 * i for i in range(13)])
estado = ritmo_estadual_na_escala(s, "MAMA")
checar("D. linha do Estado tem o mesmo total que a cidade",
       abs(estado["internacoes"].sum() - 130) < 1e-6)
checar("D. linha do Estado mantém o formato (sobe)",
       estado["internacoes"].iloc[-1] > estado["internacoes"].iloc[0])

# ---- E. leitura ----
frases = leitura_evolucao(serie(crescente, [1000] * 13), "MAMA")
checar("E. cita o crescimento", any("cresceram" in f for f in frases))
checar("E. compara com o Estado (mais rápido)", any("mais rápido" in f for f in frases))
frases = leitura_evolucao(serie(agudos), "MAMA")
checar("E. avisa números pequenos", any("Números pequenos" in f for f in frases))

# ---- F. projeção ----
proj = projetar(serie_doenca(serie(crescente), "MAMA"))
checar("F. reta perfeita projeta exato (2026 = 75)", abs(proj["internacoes"].iloc[0] - 75) < 1e-6)
proj = projetar(serie_doenca(serie([5, 4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0]), "MAMA"))
checar("F. projeção e faixa nunca negativas", (proj[["internacoes", "minimo"]] >= 0).all().all())
teste = testar_projecao(serie_doenca(serie(crescente), "MAMA"))
checar("F. teste de acerto: reta perfeita erra zero", teste["erro_tendencia"] < 1e-6)

# ---- G. uma fonte por cidade (evita contar Rio Claro em dobro) ----
linhas = pd.DataFrame({"tipo_cancer": ["MAMA", "MAMA"], "origem": ["RIO_CLARO", "SP"], "internacoes": [10, 10]})
checar("G. cidade nas duas fontes: usa só a estadual",
       escolher_uma_fonte(linhas)["origem"].tolist() == ["SP"])
checar("G. cidade só no arquivo próprio: usa ele",
       escolher_uma_fonte(linhas[linhas["origem"] == "RIO_CLARO"])["origem"].tolist() == ["RIO_CLARO"])
misto = pd.DataFrame({"tipo_cancer": ["MAMA", "MAMA", "OVARIO"],
                      "origem": ["RIO_CLARO", "SP", "RIO_CLARO"], "internacoes": [10, 10, 4]})
escolhido = escolher_uma_fonte(misto)
checar("G. escolha é por câncer: ovário só da pasta da cidade não some",
       sorted(zip(escolhido["tipo_cancer"], escolhido["origem"])) == [("MAMA", "SP"), ("OVARIO", "RIO_CLARO")])

caminho = os.path.join(tempfile.mkdtemp(), "teste.db")
conn = sqlite3.connect(caminho)
conn.execute("CREATE TABLE internacoes (tipo_cancer TEXT, origem TEXT, municipio TEXT, ano INTEGER, "
             "obito INTEGER, valor_total REAL, dias_permanencia INTEGER)")
registros = []
for ano in range(2013, 2019):
    registros += [("MAMA", "RIO_CLARO", "RIO_CLARO", ano, 0, 100.0, 2)] * 4  # arquivo de Rio Claro
    registros += [("MAMA", "SP", "RIO_CLARO", ano, 0, 100.0, 2)] * 4         # as mesmas, no estadual
    registros += [("MAMA", "SP", "LIMEIRA", ano, 0, 100.0, 2)] * 6
conn.executemany("INSERT INTO internacoes VALUES (?,?,?,?,?,?,?)", registros)
s = carregar_serie(conn, "RIO_CLARO")
conn.close()
checar("G. banco: Rio Claro conta 4 por ano, não 8",
       serie_doenca(s, "MAMA")["internacoes"].tolist() == [4] * 6)
checar("G. banco: Estado soma todas as cidades do arquivo estadual (10 por ano)",
       serie_doenca(s, "MAMA", "SP")["internacoes"].tolist() == [10] * 6)

# ---- H. base pública real ----
if os.path.exists(CSV_REAL):
    real = pd.read_csv(CSV_REAL, sep=";")
    codigos = {"Mama": "MAMA", "Colo do útero": "COLO_UTERO", "Colorretal": "COLORRETAL",
               "Ovário": "OVARIO", "Pele não melanoma": "PELE_NAO_MELANOMA",
               "Pulmão": "PULMAO", "Tireoide": "TIREOIDE"}
    real["tipo_cancer"] = real["cancer"].map(codigos)
    real["grupo"] = real["territorio"].map({"Rio Claro": "MUNICIPIO", "São Paulo": "SP"})
    real["dias_permanencia"] = real["dias_internacao_total"]
    s = completar_anos(real[["tipo_cancer", "grupo", "ano", "internacoes", "obitos",
                             "valor_total", "dias_permanencia"]])
    resumo = resumo_doencas(s)
    checar("H. base real: Mama é o maior volume em Rio Claro (670)",
           resumo.iloc[0]["doenca"] == "Mama" and resumo.iloc[0]["internacoes"] == 670)
    fora, total = ano_atipico_no_estado(s, 2025)
    checar("H. base real: 2025 fora do padrão no Estado na maioria dos cânceres",
           total == 7 and fora >= 4)
else:
    print("(pulado) H. base real não encontrada em " + CSV_REAL)

print()
if falhas:
    print(f"{len(falhas)} checagem(ns) falharam.")
    raise SystemExit(1)
print("Todas as checagens passaram.")
