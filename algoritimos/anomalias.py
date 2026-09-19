import sqlite3
import pandas as pd
from configuracao_geografica import obter_municipio

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"
conn = sqlite3.connect(BANCO)
MUNICIPIO = obter_municipio()

df = pd.read_sql("""
SELECT tipo_cancer, ano, COUNT(*) AS internacoes
FROM internacoes
WHERE municipio = ?
GROUP BY tipo_cancer, ano
ORDER BY tipo_cancer, ano
""", conn, params=(MUNICIPIO,))

LIMIAR_AMOSTRA_PEQUENA = 10
resultado = []

for cancer in df["tipo_cancer"].unique():
    dados = df[df["tipo_cancer"] == cancer].copy()
    if len(dados) < 5:
        continue
    historico = dados[dados["ano"] < 2025]
    atual = dados[dados["ano"] == 2025]
    if historico.empty or atual.empty:
        continue

    media_historica = historico["internacoes"].mean()
    valor_2025 = atual.iloc[0]["internacoes"]

    if media_historica == 0:
        if valor_2025 == 0:
            desvio, situacao = 0.0, "NORMAL"
        else:
            desvio, situacao = float("inf"), "ANOMALIA_POSITIVA"
        confiabilidade = (
            "BAIXA (não havia nenhuma internação histórica registrada antes "
            "de 2025 — desvio percentual não pode ser calculado de forma confiável)"
        )
    else:
        desvio = ((valor_2025 - media_historica) / media_historica) * 100
        if desvio >= 50:
            situacao = "ANOMALIA_POSITIVA"
        elif desvio <= -50:
            situacao = "ANOMALIA_NEGATIVA"
        else:
            situacao = "NORMAL"
        confiabilidade = (
            f"BAIXA (média histórica de apenas {media_historica:.1f} "
            "internações/ano — percentual pode enganar)"
            if media_historica < LIMIAR_AMOSTRA_PEQUENA else "OK"
        )

    resultado.append({
        "tipo_cancer": cancer,
        "media_historica": round(media_historica, 2),
        "valor_2025": int(valor_2025),
        "desvio_percentual": None if desvio == float("inf") else round(desvio, 2),
        "situacao": situacao,
        "confiabilidade": confiabilidade
    })

anomalias = pd.DataFrame(resultado)
if not anomalias.empty:
    anomalias = anomalias.sort_values("desvio_percentual", ascending=False, na_position="first")

print(f"\n=== ANOMALIAS DETECTADAS ({MUNICIPIO}) ===\n")
print(anomalias.to_string(index=False))
anomalias.to_sql("anomalias", conn, if_exists="replace", index=False)
print("\nTabela anomalias atualizada com sucesso.")
conn.close()
