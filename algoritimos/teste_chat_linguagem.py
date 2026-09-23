"""Bateria virtual de linguagem do Escudo.

Não chama Gemini nem banco real. Testa variações de linguagem que um
usuário real pode escrever, inclusive abreviações, acentos ausentes,
perguntas curtas e continuação.
"""

from chat_inteligente import entender


DISPONIVEIS = {"MAMA", "OVARIO", "COLO_UTERO", "COLORRETAL", "PULMAO", "TIREOIDE", "PELE_NAO_MELANOMA"}

CASOS = [
    ("me fala da mama", "MAMA"),
    ("mama", "MAMA"),
    ("e mama?", "MAMA"),
    ("e o seio?", "MAMA"),
    ("cancer de ovario", "OVARIO"),
    ("ovário em 2024", "OVARIO"),
    ("tumor do utero", "COLO_UTERO"),
    ("cancer cervical", "COLO_UTERO"),
    ("colon", "COLORRETAL"),
    ("intestino", "COLORRETAL"),
    ("pulmão", "PULMAO"),
    ("pulmoes", "PULMAO"),
    ("tireoide", "TIREOIDE"),
    ("pele", "PELE_NAO_MELANOMA"),
    ("quanto morreu?", "MORTALIDADE"),
    ("quantos obitos?", "MORTALIDADE"),
    ("qual a letalidade?", "MORTALIDADE"),
    ("quem mais mata?", "MORTALIDADE"),
    ("qual tem mais mortes?", "MORTALIDADE"),
    ("quanto custa?", "CUSTO"),
    ("qual o gasto?", "CUSTO"),
    ("quanto foi pago?", "CUSTO"),
    ("quanto foi registrado?", "CUSTO"),
    ("valor das aih", "CUSTO"),
    ("quantos dias fica internada?", "PERMANENCIA"),
    ("tempo de internação", "PERMANENCIA"),
    ("ocupação de leito", "PERMANENCIA"),
    ("como evoluiu?", "EVOLUCAO"),
    ("cresceu?", "EVOLUCAO"),
    ("subiu?", "EVOLUCAO"),
    ("como mudou ao longo dos anos?", "EVOLUCAO"),
    ("qual a tendencia?", "EVOLUCAO"),
    ("evolucao de 2013 a 2025", "EVOLUCAO"),
    ("compare com sp", "ESTADO"),
    ("como estamos em relação a sao paulo?", "ESTADO"),
    ("estamos acima do estado?", "ESTADO"),
    ("e o estado?", "ESTADO"),
    ("teve algum pico?", "FORA_PADRAO"),
    ("teve alguma anomalia?", "FORA_PADRAO"),
    ("algum ano estranho?", "FORA_PADRAO"),
    ("ficou acima do esperado?", "FORA_PADRAO"),
    ("o que esperar para 2028?", "PROJECAO"),
    ("vai crescer?", "PROJECAO"),
    ("projecao", "PROJECAO"),
    ("e daqui a tres anos?", "PROJECAO"),
    ("o que merece atencao?", "ATENCAO"),
    ("onde devemos olhar?", "ATENCAO"),
    ("onde agir?", "ATENCAO"),
    ("isso merece recurso?", "ATENCAO"),
    ("como calculou?", "METODO"),
    ("de onde vem esses dados?", "METODO"),
    ("posso confiar?", "METODO"),
    ("o que significa sih?", "METODO"),
    ("qual a faixa etaria?", "IDADE"),
    ("qual idade mais aparece?", "IDADE"),
    ("tem incidencia?", "INCIDENCIA"),
    ("quantos casos novos?", "INCIDENCIA"),
]


def normalizar_assunto(pergunta):
    return entender(pergunta, DISPONIVEIS, "MAMA")["assunto"]


falhas = []
for pergunta, esperado in CASOS:
    obtido = normalizar_assunto(pergunta)
    if obtido != esperado:
        falhas.append((pergunta, esperado, obtido))
        print(f"FALHOU: {pergunta!r}: esperado {esperado}, obtido {obtido}")
    else:
        print(f"OK: {pergunta!r} -> {obtido}")

if falhas:
    raise SystemExit(f"{len(falhas)} casos falharam.")

print(f"\n{len(CASOS)} perguntas virtuais passaram.")
