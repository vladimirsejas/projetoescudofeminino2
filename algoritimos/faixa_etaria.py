import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

df = pd.read_sql("""
SELECT
    tipo_cancer,
    idade
FROM internacoes
""", conn)

# =====================================
# FAIXAS ETÁRIAS
# =====================================

def faixa(idade):

    if idade < 20:
        return "0-19"

    elif idade < 40:
        return "20-39"

    elif idade < 60:
        return "40-59"

    elif idade < 80:
        return "60-79"

    else:
        return "80+"

df["faixa_etaria"] = df["idade"].apply(faixa)

resultado = (
    df.groupby(
        [
            "tipo_cancer",
            "faixa_etaria"
        ]
    )
    .size()
    .reset_index(name="internacoes")
)

resultado = resultado.sort_values(
    [
        "tipo_cancer",
        "internacoes"
    ],
    ascending=[True, False]
)

print("\n=== FAIXA ETÁRIA ===\n")

print(resultado)

resultado.to_sql(
    "faixa_etaria",
    conn,
    if_exists="replace",
    index=False
)

print(
    "\nTabela faixa_etaria criada com sucesso."
)

conn.close()