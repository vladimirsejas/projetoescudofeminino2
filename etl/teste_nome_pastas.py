import os

BASE_DADOS = r"C:\projetoescudofeminino2\dados"

for pasta in os.listdir(BASE_DADOS):
    print("PASTA:", pasta)

    partes = pasta.split("_")

    print("PARTES:", partes)

    tipo_cancer = "_".join(partes[1:-2])

    print("TIPO:", tipo_cancer)

    print("-" * 40)
