import pandas as pd
import sqlite3

arquivo = r"C:\projetoescudofeminino\dados\cancer_mama_rio_claro\cancer_mama_mulheres_rio_claro_2021_2025.csv"

banco = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

df = pd.read_csv(
    arquivo,
    sep=";",
    encoding="latin1"
)

dados = pd.DataFrame()

dados["tipo_cancer"] = "Mama"
dados["origem"] = "RIO_CLARO"
dados["ano"] = df["ANO_CMPT"]
dados["idade"] = df["IDADE"]
dados["dias_permanencia"] = df["DIAS_PERM"]
dados["obito"] = df["MORTE"]
dados["valor_total"] = df["VAL_TOT"]

conexao = sqlite3.connect(banco)

dados.to_sql(
    "internacoes",
    conexao,
    if_exists="append",
    index=False
)

conexao.close()

print("Carga concluída com sucesso!")
print("Registros carregados:", len(dados))