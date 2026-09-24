import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apoio  # noqa: E402
from lia import INICIO  # noqa: E402

# =====================================
# TESTE DO APOIO À MULHER (algoritimos/apoio.py)
#
# Catálogo: todo item tem fonte, link oficial (https), caminho e
# lâmina válidos, ids únicos. Lia: percorre a árvore inteira a partir
# do início (todos os botões, até não sobrar botão novo) e confere
# que cada resposta tem fala, expressão válida, destino numa lâmina
# e termina com "Começar de novo"; item a confirmar deixa a Lia
# cautelosa; nenhuma fala promete vaga nem dá conduta médica.
# Uso: py algoritimos\teste_apoio.py
# =====================================

falhas = []


def checar(nome, condicao):
    print(("OK   " if condicao else "FALHOU ") + nome)
    if not condicao:
        falhas.append(nome)


# ---------- catálogo ----------
ids = [i["id"] for i in apoio.ITENS]
checar("ids únicos", len(ids) == len(set(ids)))
checar("todo item tem fonte e link https", all(i["fonte"] and i["link"].startswith("https://") for i in apoio.ITENS))
checar("todo item está num caminho válido", all(i["caminho"] in apoio.NOME_CAMINHO for i in apoio.ITENS))
checar("toda lâmina de item existe", all(i["lamina"] in ("caminho", "rio_claro", "barretos") for i in apoio.ITENS))
checar("todo caminho tem pelo menos um item", all(apoio.itens(caminho=c) for c in apoio.NOME_CAMINHO))
checar("Rio Claro tem lâmina com itens", len(apoio.itens(lamina="rio_claro")) >= 4)
checar("Barretos tem lâmina com itens", len(apoio.itens(lamina="barretos")) >= 3)
outras = {"Campinas", "Ribeirão Preto", "São José do Rio Preto"}
checar("outras cidades entram só nos caminhos (sem lâmina própria)",
       all(i["lamina"] == "caminho" for i in apoio.ITENS if i["onde"] in outras)
       and any(i["onde"] in outras for i in apoio.ITENS)
       and any(i["onde"].startswith("Piracicaba") for i in apoio.ITENS))
checar("texto sem seta ASCII (->)", not any("->" in str(v) for i in apoio.ITENS for v in i.values()))

# ---------- a Lia: árvore inteira ----------
inicio = apoio.responder(INICIO)
checar("saudação diz onde a pessoa está", apoio.CIDADE in inicio.fala and inicio.expressao == "acolhedora")
checar("saudação oferece os 8 caminhos", all(any(a == apoio.caminho(c) for _, a in inicio.botoes)
                                              for c in apoio.NOME_CAMINHO))

vistos, fila, respostas = set(), deque([INICIO]), 0
problemas = []
while fila:
    acao = fila.popleft()
    chave = tuple(sorted(acao.items()))
    if chave in vistos:
        continue
    vistos.add(chave)
    r = apoio.responder(acao)
    respostas += 1
    if not r.fala or r.expressao not in ("acolhedora", "explicando", "atenta", "cautelosa", "pensativa"):
        problemas.append(f"fala/expressão: {acao}")
    if not r.destino or r.destino.get("aba") not in apoio.LAMINAS.values():
        problemas.append(f"destino: {acao}")
    if acao is not INICIO and (not r.botoes or r.botoes[-1] != ("Começar de novo", INICIO)):
        problemas.append(f"sem começar de novo: {acao}")
    for proibida in ("vai conseguir", "garantid", "tome ", "você tem câncer"):
        if proibida in r.fala.lower():
            problemas.append(f"fala proibida '{proibida}': {acao}")
    if acao.get("tipo") == "apoio_item":
        i = apoio.POR_ID[acao["id"]]
        if (i["confirmar"] is not None) != (r.expressao == "cautelosa"):
            problemas.append(f"expressão x confirmar: {acao}")
        if i["link"] not in r.fala or apoio.CONFERIDO not in r.fala:
            problemas.append(f"item sem link/data: {acao}")
    for _, a in r.botoes:
        fila.append(a)
checar(f"árvore inteira sem problemas ({respostas} respostas)", not problemas)
for p in problemas[:10]:
    print("   ", p)
itens_alcancados = {dict(k)["id"] for k in vistos if dict(k).get("tipo") == "apoio_item"}
checar("todo item é alcançável pelos botões", itens_alcancados == set(ids))
checar("botão desconhecido volta à saudação", apoio.responder({"tipo": "apoio_item", "id": "nao_existe"}).fala
       == inicio.fala)

print()
print("Todas as checagens do apoio passaram." if not falhas else f"{len(falhas)} falha(s).")
sys.exit(1 if falhas else 0)
