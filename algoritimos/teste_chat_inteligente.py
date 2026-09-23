import pandas as pd

from chat_inteligente import entender, responder, fatos_mortalidade, fatos_custo
from inteligencia import completar_anos


def serie_teste():
    linhas = []
    for i, ano in enumerate(range(2013, 2026)):
        linhas.append(("MAMA", "MUNICIPIO", ano, 10 + i, 1 if i % 4 == 0 else 0, 1000 + i * 100, 30 + i))
        linhas.append(("OVARIO", "MUNICIPIO", ano, 5 + (i % 3), 1 if i % 5 == 0 else 0, 700 + i * 50, 20 + i))
        linhas.append(("MAMA", "SP", ano, 100 + i * 3, 5, 10000 + i * 200, 300 + i))
        linhas.append(("OVARIO", "SP", ano, 50 + i * 2, 3, 7000 + i * 100, 200 + i))
    return completar_anos(pd.DataFrame(linhas, columns=[
        "tipo_cancer", "grupo", "ano", "internacoes", "obitos",
        "valor_total", "dias_permanencia"
    ]))


SERIE = serie_teste()
DISPONIVEIS = {"MAMA", "OVARIO"}


def checar(nome, condicao):
    print(("OK   " if condicao else "FALHOU ") + nome)
    if not condicao:
        raise AssertionError(nome)


# 1. Sinônimos de câncer
casos_cancer = [
    ("internações de mama", "MAMA"),
    ("câncer de seio", "MAMA"),
    ("mama em 2024", "MAMA"),
    ("câncer de ovário", "OVARIO"),
    ("ovarios", "OVARIO"),
]
for pergunta, esperado in casos_cancer:
    r = entender(pergunta, DISPONIVEIS, "MAMA")
    checar(f"câncer: {pergunta}", r["cancer"] == esperado)


# 2. Assuntos
casos_assunto = [
    ("qual a mortalidade?", "MORTALIDADE"),
    ("quanto custou?", "CUSTO"),
    ("quantos dias ficam internadas?", "PERMANENCIA"),
    ("como evoluiu?", "EVOLUCAO"),
    ("compare com São Paulo", "ESTADO"),
    ("o que merece atenção?", "ATENCAO"),
    ("o que esperar até 2028?", "PROJECAO"),
    ("houve algum ano fora do padrão?", "FORA_PADRAO"),
    ("como esses dados são calculados?", "METODO"),
    ("qual a faixa etária?", "IDADE"),
    ("isso é incidência?", "INCIDENCIA"),
    ("qual o panorama?", "PANORAMA"),
]
for pergunta, esperado in casos_assunto:
    r = entender(pergunta, DISPONIVEIS, "MAMA")
    checar(f"assunto: {pergunta}", esperado in r["assuntos"])


# 3. Perguntas combinadas
r = entender("qual a mortalidade e o custo do câncer de mama?", DISPONIVEIS, "MAMA")
checar("combinação mortalidade + custo", "MORTALIDADE" in r["assuntos"] and "CUSTO" in r["assuntos"])
checar("combinação identifica mama", r["cancer"] == "MAMA")


# 4. Memória de conversa
historico = [{
    "pergunta": "Como evoluiu o câncer de mama?",
    "assunto": "EVOLUCAO",
    "contexto": {"cancer": "MAMA", "ano": 2024},
}]
r = entender("e em 2024?", DISPONIVEIS, "OVARIO", historico)
checar("continuação preserva câncer anterior", r["cancer"] == "MAMA")
checar("continuação preserva ano", r["ano"] == 2024)

r = entender("e os gastos?", DISPONIVEIS, "MAMA", historico)
checar("continuação troca assunto para custo", "CUSTO" in r["assuntos"])
checar("continuação preserva câncer", r["cancer"] == "MAMA")


# 5. Resposta sem Gemini nunca fica muda
r = responder("quanto custou o câncer de mama?", SERIE, "Rio Claro",
               cancer_em_foco="MAMA", explicar=None)
checar("fallback sem Gemini produz texto", bool(r["texto"]))
checar("fallback calcula custo", any("R$" in f for f in r["fatos"]))
checar("fallback identifica custo", r["assunto"] == "CUSTO")


# 6. Explicador controlado recebe fatos, não banco
recebido = {}


def explicador(pergunta, contexto, perfil, memoria=None):
    recebido["pergunta"] = pergunta
    recebido["contexto"] = contexto
    recebido["perfil"] = perfil
    recebido["memoria"] = memoria
    return "Resposta redigida a partir dos fatos."


r = responder("mortalidade da mama", SERIE, "Rio Claro",
               cancer_em_foco="MAMA", perfil="TECNICO",
               explicar=explicador, historico=historico)
checar("explicador recebe pergunta", recebido["pergunta"] == "mortalidade da mama")
checar("explicador recebe fatos", "letalidade" in recebido["contexto"].lower())
checar("explicador recebe memória", bool(recebido["memoria"]))
checar("resposta marcada como IA", r["usou_ia"] is True)


# 7. Capacidades que não devem ser inventadas
r = responder("qual a incidência de câncer?", SERIE, "Rio Claro",
               cancer_em_foco="MAMA", explicar=None)
checar("incidência é explicitamente indisponível", "não calcula incidência" in r["texto"].lower())

r = responder("qual a faixa etária?", SERIE, "Rio Claro",
               cancer_em_foco="MAMA", explicar=None)
checar("idade não é inventada", "não está exposta" in r["texto"].lower())


# 8. Integridade dos números
r = responder("quantas internações de mama?", SERIE, "Rio Claro",
               cancer_em_foco="MAMA", explicar=None)
total_mama = SERIE[(SERIE.grupo == "MUNICIPIO") & (SERIE.tipo_cancer == "MAMA")].internacoes.sum()
checar("total de mama aparece nos fatos", any(str(int(total_mama)) in f.replace(".", "") for f in r["fatos"]))


# 9. Mortalidade informa óbitos durante internação, sem chamar de mortalidade populacional
fatos, _ = fatos_mortalidade(SERIE, "Rio Claro", "MAMA")
checar("mortalidade contém ressalva hospitalar", any("não a mortalidade populacional" in f for f in fatos))


# 10. Custo usa linguagem metodologicamente correta
fatos, _ = fatos_custo(SERIE, "Rio Claro", "MAMA")
checar("custo fala em valores registrados", "registrados nas AIHs" in fatos[0])
checar("custo não chama isso de orçamento total", "não representa todo o orçamento" in fatos[-1])


print("\nTodas as checagens do chatbot passaram.")
