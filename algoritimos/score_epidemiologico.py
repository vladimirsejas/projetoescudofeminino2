import sqlite3
import pandas as pd
from configuracao_geografica import obter_municipio

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"
conn = sqlite3.connect(BANCO)
MUNICIPIO = obter_municipio()

df = pd.read_sql("""
SELECT tipo_cancer, COUNT(*) AS internacoes, SUM(obito) AS obitos
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer
""", conn, params=(MUNICIPIO,))

crescimento = pd.read_sql("""
SELECT tipo_cancer,
       SUM(CASE WHEN ano = 2024 THEN 1 ELSE 0 END) AS ano_2024,
       SUM(CASE WHEN ano = 2025 THEN 1 ELSE 0 END) AS ano_2025
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer
""", conn, params=(MUNICIPIO,))

crescimento["crescimento"] = (
    (crescimento["ano_2025"] - crescimento["ano_2024"])
    / crescimento["ano_2024"].replace(0, 1)
) * 100

df = df.merge(crescimento[["tipo_cancer", "crescimento"]], on="tipo_cancer")
df["internacoes_norm"] = (df["internacoes"] / df["internacoes"].max()) * 100
df["obitos_norm"] = (df["obitos"] / df["obitos"].max()) * 100
df["crescimento_norm"] = (df["crescimento"] / df["crescimento"].max()) * 100

df["score"] = (
    df["internacoes_norm"] * 0.40
    + df["obitos_norm"] * 0.30
    + df["crescimento_norm"] * 0.30
)

def classificar(score):
    if score >= 80:
        return "CRITICA"
    if score >= 60:
        return "ALTA"
    if score >= 40:
        return "MEDIA"
    return "BAIXA"

df["prioridade"] = df["score"].apply(classificar)
df = df.sort_values("score", ascending=False)

print(f"\n=== SCORE EPIDEMIOLÓGICO ({MUNICIPIO}) ===\n")
print(df[["tipo_cancer","internacoes","obitos","crescimento","score","prioridade"]])

df[["tipo_cancer","internacoes","obitos","crescimento","score","prioridade"]].to_sql(
    "indicadores_epidemiologicos", conn, if_exists="replace", index=False
)
print("\nTabela indicadores_epidemiologicos criada com sucesso.")
conn.close()
