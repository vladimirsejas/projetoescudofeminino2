import os
import pandas as pd
import sqlite3

BASE_DADOS = r"C:\projetoescudofeminino\dados"
BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

MAPA = {
    "cancer_mama_rio_claro": ("MAMA", "RIO_CLARO"),
    "cancer_mama_sp": ("MAMA", "SP"),

    "cancer_colorretal_rio_claro": ("COLORRETAL", "RIO_CLARO"),
    "cancer_colorretal_sp": ("COLORRETAL", "SP"),

    "cancer_colo_utero_rio_claro": ("COLO_UTERO", "RIO_CLARO"),
    "cancer_colo_utero_sp": ("COLO_UTERO", "SP"),

    "cancer_ovario_rio_claro": ("OVARIO", "RIO_CLARO"),
    "cancer_ovario_sp": ("OVARIO", "SP"),

    "cancer_pulmao_rio_claro": ("PULMAO", "RIO_CLARO"),
    "cancer_pulmao_sp": ("PULMAO", "SP"),

    "cancer_tireoide_rio_claro": ("TIREOIDE", "RIO_CLARO"),
    "cancer_tireoide_sp": ("TIREOIDE", "SP"),

    "cancer_pele_nao_melanoma_rio_claro": ("PELE_NAO_MELANOMA", "RIO_CLARO"),
    "cancer_pele_nao_melanoma_sp": ("PELE_NAO_MELANOMA", "SP")
}

conexao = sqlite3.connect(BANCO)

total_registros = 0

for pasta in os.listdir(BASE_DADOS):

    if pasta not in MAPA:
        continue

    caminho_pasta = os.path.join(BASE_DADOS, pasta)

    arquivos_csv = [
        arquivo
        for arquivo in os.listdir(caminho_pasta)
        if arquivo.endswith(".csv")
    ]

    if len(arquivos_csv) == 0:
        continue

    arquivo_csv = os.path.join(
        caminho_pasta,
        arquivos_csv[0]
    )

    tipo_cancer, origem = MAPA[pasta]

    print("\n" + "=" * 60)
    print("PASTA:", pasta)
    print("TIPO:", tipo_cancer)
    print("ORIGEM:", origem)

    df = pd.read_csv(
        arquivo_csv,
        sep=";",
        encoding="latin1",
        low_memory=False
    )

    dados = pd.DataFrame({
        "tipo_cancer": [tipo_cancer] * len(df),
        "origem": [origem] * len(df),
        "ano": df["ANO_CMPT"],
        "idade": df["IDADE"],
        "dias_permanencia": df["DIAS_PERM"],
        "obito": df["MORTE"],
        "valor_total": df["VAL_TOT"]
    })

    print(dados.head())

    dados.to_sql(
        "internacoes",
        conexao,
        if_exists="append",
        index=False
    )

    total_registros += len(dados)

    print("OK ->", len(dados), "registros")

conexao.close()

print("\n" + "=" * 60)
print("CARGA FINALIZADA")
print("TOTAL:", total_registros)
print("=" * 60)