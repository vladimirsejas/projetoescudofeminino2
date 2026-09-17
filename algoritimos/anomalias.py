import sqlite3
import pandas as pd

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# DADOS ANUAIS
# =====================================

df = pd.read_sql("""
SELECT
    tipo_cancer,
    ano,
    COUNT(*) AS internacoes
FROM internacoes
GROUP BY tipo_cancer, ano
ORDER BY tipo_cancer, ano
""", conn)

# =====================================
# DETECÇÃO DE ANOMALIAS
# =====================================

resultado = []

for cancer in df["tipo_cancer"].unique():

    dados = df[
        df["tipo_cancer"] == cancer
    ].copy()

    if len(dados) < 5:
        continue

    historico = dados[
        dados["ano"] < 2025
    ]

    atual = dados[
        dados["ano"] == 2025
    ]

    if historico.empty or atual.empty:
        continue

    media_historica = historico["internacoes"].mean()

    valor_2025 = atual.iloc[0]["internacoes"]

    desvio = (
        (valor_2025 - media_historica)
        / media_historica
    ) * 100

    if desvio >= 50:
        situacao = "ANOMALIA_POSITIVA"

    elif desvio <= -50:
        situacao = "ANOMALIA_NEGATIVA"

    else:
        situacao = "NORMAL"

    resultado.append(
        {
            "tipo_cancer": cancer,
            "media_historica": round(media_historica, 2),
            "valor_2025": int(valor_2025),
            "desvio_percentual": round(desvio, 2),
            "situacao": situacao
        }
    )

# =====================================
# DATAFRAME FINAL
# =====================================

anomalias = pd.DataFrame(resultado)

anomalias = anomalias.sort_values(
    "desvio_percentual",
    ascending=False
)

# =====================================
# RESULTADO
# =====================================

print("\n=== ANOMALIAS DETECTADAS ===\n")

print(anomalias)

# =====================================
# GRAVAR SQLITE
# =====================================

anomalias.to_sql(
    "anomalias",
    conn,
    if_exists="replace",
    index=False
)

print("\nTabela anomalias criada com sucesso.")

conn.close()