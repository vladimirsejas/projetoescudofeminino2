import pandas as pd

dados = [
    ["MAMA", 75.47, 55.82, 19.65, "ACIMA DA TENDENCIA ESTADUAL"],
    ["COLORRETAL", 5.00, 56.36, -51.36, "ABAIXO DA TENDENCIA ESTADUAL"],
    ["PELE_NAO_MELANOMA", 150.00, 70.47, 79.53, "ACIMA DA TENDENCIA ESTADUAL"],
    ["COLO_UTERO", 366.67, 45.75, 320.92, "ACIMA DA TENDENCIA ESTADUAL"],
    ["PULMAO", -40.00, 56.83, -96.83, "ABAIXO DA TENDENCIA ESTADUAL"],
    ["OVARIO", 14.29, 55.40, -41.11, "ABAIXO DA TENDENCIA ESTADUAL"],
    ["TIREOIDE", 66.67, 36.32, 30.35, "ACIMA DA TENDENCIA ESTADUAL"]
]

df = pd.DataFrame(
    dados,
    columns=[
        "cancer",
        "variacao_rio_claro",
        "variacao_sp",
        "diferenca",
        "evento"
    ]
)

print()
print("=" * 70)
print("RELATORIO EXECUTIVO DE EVENTOS")
print("=" * 70)

for _, linha in df.iterrows():

    print()

    print(f"Cancer: {linha['cancer']}")
    print(f"Rio Claro: {linha['variacao_rio_claro']}%")
    print(f"SP: {linha['variacao_sp']}%")
    print(f"Diferenca: {linha['diferenca']} pontos")
    print(f"Evento: {linha['evento']}")

print()
print("=" * 70)