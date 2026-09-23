import json
import os

import pandas as pd

from inteligencia import completar_anos
from lia import CAMINHOS, EXPRESSOES, INICIO, Contexto, caminho, responder, responder_texto, sobre

# =====================================
# TESTE DA LIA (algoritimos/lia.py)
#
# A. Percorre a árvore INTEIRA com a base pública real (Rio Claro x
#    SP): clica em todos os botões de todas as respostas, até não
#    sobrar caminho novo. Nenhum pode quebrar, ficar sem fala, sem
#    botão de recomeço ou com destino inválido.
# B. Regras da Lia: nada de orçamento, projeção com os três níveis e
#    os limites, expressão cautelosa quando o dado pede cuidado.
# C. Texto livre passa pelo motor do chat e volta no formato da Lia.
# =====================================

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CSV_REAL = os.path.join(DIRETORIO_ATUAL, "..", "analises", "base_preditiva_2013_2025.csv")
ABAS = {"Panorama", "Evolução", "Investigar", "Planejamento", "Método"}
MEDIDAS = {"Internações", "Valor hospitalar registrado", "Óbitos na internação", "Dias de internação"}

falhas = []


def checar(nome, condicao):
    print(("OK   " if condicao else "FALHOU ") + nome)
    if not condicao:
        falhas.append(nome)


real = pd.read_csv(CSV_REAL, sep=";")
codigos = {"Mama": "MAMA", "Colo do útero": "COLO_UTERO", "Colorretal": "COLORRETAL", "Ovário": "OVARIO",
           "Pele não melanoma": "PELE_NAO_MELANOMA", "Pulmão": "PULMAO", "Tireoide": "TIREOIDE"}
real["tipo_cancer"] = real["cancer"].map(codigos)
real["grupo"] = real["territorio"].map({"Rio Claro": "MUNICIPIO", "São Paulo": "SP"})
real["dias_permanencia"] = real["dias_internacao_total"]
serie = completar_anos(real[["tipo_cancer", "grupo", "ano", "internacoes", "obitos",
                             "valor_total", "dias_permanencia"]])
faixas = pd.DataFrame([(c, ano, f, 5 + (ano % 3)) for c in codigos.values() for ano in range(2013, 2026)
                       for f in ("até 39 anos", "40 a 49", "50 a 69", "70 ou mais")],
                      columns=["tipo_cancer", "ano", "faixa", "internacoes"])
ctx = Contexto(serie=serie, cidade="Rio Claro", faixas=faixas)

# ---- A. árvore inteira ----
vistos, fila, respostas, erros = set(), [INICIO], {}, []
while fila:
    acao = fila.pop()
    chave = json.dumps(acao, sort_keys=True)
    if chave in vistos:
        continue
    vistos.add(chave)
    try:
        r = responder(ctx, acao)
    except Exception as erro:  # registra e segue, para ver todos os problemas de uma vez
        erros.append(f"{chave}: {type(erro).__name__}: {erro}")
        continue
    respostas[chave] = r
    fila.extend(a for _, a in r.botoes)

checar(f"A. percorreu {len(respostas)} respostas sem erro", not erros and len(respostas) >= 60)
for e in erros[:5]:
    print("   ", e)
checar("A. toda resposta tem fala", all(r.fala.strip() for r in respostas.values()))
checar("A. toda expressão é uma das 5", all(r.expressao in EXPRESSOES for r in respostas.values()))
checar("A. toda resposta (menos a saudação) oferece 'Começar de novo'",
       all(any(a == INICIO for _, a in r.botoes) for k, r in respostas.items() if k != json.dumps(INICIO)))
checar("A. todo destino aponta para uma aba que existe",
       all(r.destino is None or r.destino.get("aba") in ABAS for r in respostas.values()))
checar("A. toda medida pedida existe no painel",
       all(r.destino is None or r.destino.get("medida") in (None, *MEDIDAS) for r in respostas.values()))
checar("A. os 8 caminhos da saudação existem", len(responder(ctx, INICIO).botoes) == len(CAMINHOS))

# ---- B. regras ----
r = responder(ctx, caminho("atencao"))
checar("B. atenção: evidências, sem valor de orçamento, decisão da gestão",
       "decisão de quanto investir é da gestão" in r.fala and "R$" not in r.fala and r.expressao == "atenta")
r = responder(ctx, sobre("MAMA", "projecao"))
checar("B. projeção tem os três níveis",
       all(t in r.fala for t in ("O que aconteceu", "O que está acontecendo", "O que pode acontecer")))
checar("B. projeção diz que não é previsão de casos novos", "não previsão de casos novos" in r.fala)
checar("B. projeção com 2025 em investigação fica cautelosa", r.expressao == "cautelosa")
r = responder(ctx, sobre("TIREOIDE", "evolucao"))
checar("B. câncer com poucas internações: expressão cautelosa e aviso", r.expressao == "cautelosa"
       and "poucas internações" in r.fala)
r = responder(ctx, caminho("valores"))
checar("B. valores: termo certo e aviso de que não é orçamento",
       "valores hospitalares registrados no SIH/SUS" in r.fala and "não é o orçamento" in r.fala)
r = responder(ctx, caminho("metodo"))
checar("B. método: expressão pensativa e o que os dados não permitem", r.expressao == "pensativa"
       and "não" in r.fala and "causas" in r.fala)
checar("B. câncer inexistente na cidade volta ao começo",
       responder(ctx, sobre("XYZ", "evolucao")).expressao == "acolhedora")

# ---- C. texto livre ----
sem_ia = lambda *a: (_ for _ in ()).throw(RuntimeError("sem chave"))
r, bruto = responder_texto(ctx, "Qual a mortalidade do câncer de mama?", explicar=sem_ia)
checar("C. texto livre usa o motor do chat e volta com botões e destino",
       bruto["assunto"] == "MORTALIDADE" and r.destino["aba"] == "Panorama" and len(r.botoes) >= 3)
r, _ = responder_texto(ctx, "Qual câncer mais mata?", explicar=sem_ia)
checar("C. texto livre sem câncer oferece caminhos gerais", any("atenção" in rot for rot, _ in r.botoes))

# ---- D. caixa de texto: tempo limite da IA e exemplos ----
import time
import lia as modulo_lia

def ia_lenta(pergunta, contexto, perfil):
    time.sleep(3)
    return "resposta tardia"

# a própria função com limite, trocando o Gemini por uma IA lenta
import ia_linguagem
original = ia_linguagem.responder_com_ia
ia_linguagem.responder_com_ia = ia_lenta
try:
    inicio = time.time()
    r, bruto = responder_texto(ctx, "Qual a mortalidade do câncer de mama?",
                               explicar=modulo_lia.explicar_com_limite(segundos=0.5))
    demorou = time.time() - inicio
finally:
    ia_linguagem.responder_com_ia = original
checar("D. IA lenta: responde em menos de 2 s, direto com os números",
       demorou < 2 and not bruto["usou_ia"] and "Mama" in r.fala)

from conversa import entender
# Toda pergunta sugerida, para todo câncer, cai no assunto certo e no
# câncer certo -- mesmo com OUTRO câncer em foco no painel -- e volta
# com resposta de verdade (nenhum botão que leva ao silêncio).
disponiveis = set(codigos.values())
erros_sugestao = []
for foco in codigos.values():
    outro_foco = "OVARIO" if foco != "OVARIO" else "MAMA"
    sug = modulo_lia.sugestoes_de_pergunta(ctx, foco)
    for (rotulo, pergunta), (_, _, assunto) in zip(sug["do_cancer"], modulo_lia.PERGUNTAS_DO_CANCER):
        e = entender(pergunta, disponiveis, outro_foco)
        r, _ = responder_texto(ctx, pergunta, cancer_em_foco=outro_foco, explicar=sem_ia)
        if e["assunto"] != assunto or e["cancer"] != foco or not r.fala.strip() or r.destino.get("cancer") != foco:
            erros_sugestao.append(f"{pergunta} -> {e['assunto']}/{e['cancer']}")
for (rotulo, pergunta), (_, _, assunto) in zip(sug["gerais"], modulo_lia.PERGUNTAS_GERAIS):
    e = entender(pergunta, disponiveis, None)
    r, _ = responder_texto(ctx, pergunta, explicar=sem_ia)
    if e["assunto"] != assunto or e["cancer"] is not None or not r.fala.strip():
        erros_sugestao.append(f"{pergunta} -> {e['assunto']}/{e['cancer']}")
checar("D. todas as perguntas sugeridas caem no assunto e no câncer certos " + str(erros_sugestao),
       not erros_sugestao)
checar("D. sugestões sem câncer em foco usam o maior",
       modulo_lia.sugestoes_de_pergunta(ctx, None)["cancer"] == "MAMA")
checar("D. rótulos das sugestões são curtos (cabem no botão da lateral)",
       all(len(r) <= 20 for r, _, _ in modulo_lia.PERGUNTAS_DO_CANCER + modulo_lia.PERGUNTAS_GERAIS))

# o que os dados não respondem: a Lia diz o limite antes
r, _ = responder_texto(ctx, "Por que o câncer de mama aumentou?", explicar=sem_ia)
checar("D. 'por que' avisa que os dados não mostram causa", r.fala.startswith("**Um limite antes:**")
       and "não **por que**" in r.fala and "mama" in r.fala.lower())
r, _ = responder_texto(ctx, "Qual tratamento devemos oferecer?", explicar=sem_ia)
checar("D. tratamento: avisa que não é orientação médica", "não é orientação médica" in r.fala)
r, _ = responder_texto(ctx, "Quantas mulheres terão câncer de mama em 2030?", explicar=sem_ia)
checar("D. casos futuros: avisa que internação não é caso novo", "internação não é caso novo" in r.fala)
r, _ = responder_texto(ctx, "Como evoluiu o câncer de mama?", explicar=sem_ia)
checar("D. pergunta dentro do alcance não recebe aviso de limite", "Um limite antes" not in r.fala)

r, _ = responder_texto(ctx, "O que esperar para 2028?", explicar=sem_ia)
checar("D. pergunta sobre o futuro liga a projeção no gráfico",
       r.destino["aba"] == "Evolução" and r.destino["camadas"]["ver_projecao"])
r, _ = responder_texto(ctx, "Qual a mortalidade do câncer de mama?", explicar=sem_ia)
checar("D. pergunta sobre óbitos troca a medida das barras", r.destino.get("medida") == "Óbitos na internação")

print()
if falhas:
    print(f"{len(falhas)} checagem(ns) falharam.")
    raise SystemExit(1)
print("Todas as checagens passaram.")
