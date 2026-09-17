import pandas as pd

eventos = [
    ["MAMA", 75.47, 55.82, 19.65, "ACIMA DA TENDENCIA ESTADUAL"],
    ["COLORRETAL", 5.00, 56.36, -51.36, "ABAIXO DA TENDENCIA ESTADUAL"],
    ["PELE_NAO_MELANOMA", 150.00, 70.47, 79.53, "ACIMA DA TENDENCIA ESTADUAL"],
    ["COLO_UTERO", 366.67, 45.75, 320.92, "ACIMA DA TENDENCIA ESTADUAL"],
    ["PULMAO", -40.00, 56.83, -96.83, "ABAIXO DA TENDENCIA ESTADUAL"],
    ["OVARIO", 14.29, 55.40, -41.11, "ABAIXO DA TENDENCIA ESTADUAL"],
    ["TIREOIDE", 66.67, 36.32, 30.35, "ACIMA DA TENDENCIA ESTADUAL"]
]

df = pd.DataFrame(
    eventos,
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
print("ESCUDO FEMININO COPILOT")
print("=" * 70)

print()
print("CANCERES COM ALERTA")

print()

alertas = df[
    df["evento"] == "ACIMA DA TENDENCIA ESTADUAL"
]

for _, linha in alertas.iterrows():

    print(
        f"{linha['cancer']} apresentou crescimento acima da tendencia estadual."
    )

print()

maior = df.sort_values(
    by="diferenca",
    ascending=False
).iloc[0]

print(
    f"MAIOR ALERTA: {maior['cancer']}"
)

print(
    f"DIFERENCA: {maior['diferenca']:.2f} pontos percentuais"
)

print()
print("=" * 70)