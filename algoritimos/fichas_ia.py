import sqlite3
import pandas as pd

from configuracao_geografica import (
    obter_municipio,
    ler_tabela_municipio,
    salvar_tabela_municipio
)

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

MUNICIPIO = obter_municipio()

df = ler_tabela_municipio("perfil_epidemiologico", conn, municipio=MUNICIPIO)
df = df.sort_values("pontuacao_final", ascending=False)

fichas = []

for _, row in df.iterrows():

    ficha = f"""
CÃ‚NCER: {row['tipo_cancer']}

PRIORIDADE:
{row['nivel_prioridade']}

PONTUAÃ‡ÃƒO:
{row['pontuacao_final']:.2f}

MORTALIDADE:
{row['taxa_mortalidade']:.2f}%

FAIXA ETÃRIA PREDOMINANTE:
{row['faixa_etaria']}

PERMANÃŠNCIA MÃ‰DIA:
{row['permanencia_media']:.2f} dias

CUSTO TOTAL:
R$ {row['valor_total']:,.2f}
"""

    fichas.append(
        {
            "tipo_cancer": row["tipo_cancer"],
            "ficha": ficha
        }
    )

resultado = pd.DataFrame(fichas)

print("\n=== FICHAS IA ===\n")

for _, row in resultado.iterrows():

    print("\n--------------------------\n")
    print(row["ficha"])

salvar_tabela_municipio(resultado, "fichas_ia", conn, municipio=MUNICIPIO)

print("\nTabela fichas_ia criada com sucesso.")

conn.close()
