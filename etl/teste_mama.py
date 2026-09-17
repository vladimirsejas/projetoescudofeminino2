import pandas as pd

arquivo = r"C:\projetoescudofeminino\dados\cancer_mama_rio_claro\cancer_mama_mulheres_rio_claro_2021_2025.csv"

df = pd.read_csv(
    arquivo,
    sep=";",
    encoding="latin1"
)

print("INTERNAÇÕES POR ANO")
print("-" * 30)

internacoes = df.groupby("ANO_CMPT").size()

print(internacoes)