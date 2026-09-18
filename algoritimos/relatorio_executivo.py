import sqlite3
import pandas as pd
from datetime import datetime
from io import StringIO

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# LEITURA DAS FONTES
# (as mesmas quatro definidas na Memória Técnica
# como fontes prioritárias do relatório)
# =====================================

base = pd.read_sql(
    "SELECT * FROM base_conhecimento ORDER BY pontuacao_final DESC",
    conn
)

priorizacao = pd.read_sql(
    "SELECT * FROM priorizacao_executiva ORDER BY pontuacao_final DESC",
    conn
)

anomalias_df = pd.read_sql(
    "SELECT * FROM anomalias", conn
)

tendencia_df = pd.read_sql(
    "SELECT * FROM tendencia_estadual", conn
)

conn.close()

# =====================================
# MONTAGEM DO RELATÓRIO
# (escrito em um buffer para poder ser
# impresso na tela e salvo em arquivo
# com o mesmo conteúdo, sem repetir lógica)
# =====================================

saida = StringIO()


def escrever(texto=""):
    saida.write(texto + "\n")


escrever("=" * 70)
escrever("RELATÓRIO EXECUTIVO — ESCUDO FEMININO")
escrever(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
escrever("Fontes: base_conhecimento, priorizacao_executiva, "
         "anomalias, tendencia_estadual")
escrever("=" * 70)

# =====================================
# 1. RESUMO DA SITUAÇÃO
# =====================================

total = len(priorizacao)

criticos_altos = priorizacao[
    priorizacao["nivel_prioridade"].isin(["CRITICA", "ALTA"])
]

anomalias_ativas = anomalias_df[
    anomalias_df["situacao"] != "NORMAL"
]

acima_tendencia = tendencia_df[tendencia_df["desvio"] > 0]

escrever("\n1. RESUMO DA SITUAÇÃO\n")

verbo_estao = "está" if len(criticos_altos) == 1 else "estão"
verbo_apresentam = "apresenta" if len(anomalias_ativas) == 1 else "apresentam"
verbo_crescem = "cresce" if len(acima_tendencia) == 1 else "crescem"

escrever(
    f"Rio Claro monitora atualmente {total} tipos de câncer feminino "
    f"a partir de internações hospitalares do SUS. Desse total, "
    f"{len(criticos_altos)} {verbo_estao} classificados em nível "
    f"CRÍTICO ou ALTA de prioridade, {len(anomalias_ativas)} "
    f"{verbo_apresentam} anomalia em relação ao padrão histórico, "
    f"e {len(acima_tendencia)} {verbo_crescem} mais rápido em "
    f"Rio Claro do que no Estado de São Paulo no mesmo período."
)

# =====================================
# 2. PRINCIPAIS RISCOS (anomalias ativas)
# =====================================

escrever("\n2. PRINCIPAIS RISCOS\n")

if anomalias_ativas.empty:
    escrever("Nenhuma anomalia identificada no período analisado.")
else:
    for _, row in anomalias_ativas.iterrows():
        escrever(
            f"- {row['tipo_cancer']}: {row['situacao']} "
            f"(desvio de {row['desvio_percentual']:.1f}% em relação "
            f"à média histórica de {row['media_historica']:.1f} "
            f"internações/ano; valor observado em 2025: "
            f"{int(row['valor_2025'])})."
        )

# =====================================
# 3. PRIORIDADES
# =====================================

escrever("\n3. PRIORIDADES\n")

for _, row in priorizacao.iterrows():
    escrever(
        f"- {row['tipo_cancer']}: {row['nivel_prioridade']} "
        f"(pontuação final {row['pontuacao_final']:.2f})"
    )

# =====================================
# 4. TENDÊNCIAS (Rio Claro x Estado de SP)
# =====================================

escrever("\n4. TENDÊNCIAS (Rio Claro em relação ao Estado de SP)\n")

for _, row in tendencia_df.sort_values(
    "desvio", ascending=False
).iterrows():

    if row["desvio"] > 0:
        direcao = f"{row['desvio']:.1f}% acima"
    elif row["desvio"] < 0:
        direcao = f"{abs(row['desvio']):.1f}% abaixo"
    else:
        direcao = "no mesmo ritmo"

    escrever(
        f"- {row['tipo_cancer']}: {direcao} da tendência estadual "
        f"({row['evento']})."
    )

# =====================================
# 5. RECOMENDAÇÕES
# (só para os câncers em nível CRÍTICA ou ALTA —
# são os que realmente pedem ação no curto prazo)
# =====================================

escrever("\n5. RECOMENDAÇÕES\n")

prioritarios = base[
    base["nivel_prioridade"].isin(["CRITICA", "ALTA"])
].sort_values("pontuacao_final", ascending=False)

if prioritarios.empty:
    escrever(
        "Nenhum câncer está classificado em nível CRÍTICO ou ALTA "
        "no momento. Recomenda-se manter o monitoramento de rotina "
        "de todos os tipos acompanhados."
    )
else:
    for _, row in prioritarios.iterrows():
        escrever(f"[{row['tipo_cancer']}]")
        escrever(row["recomendacao"])
        escrever("")

escrever("=" * 70)
escrever(
    "Este relatório é gerado automaticamente a partir do conhecimento "
    "estruturado do Escudo Feminino. É uma ferramenta de apoio à "
    "decisão; a responsabilidade pela decisão administrativa "
    "permanece com o gestor e as instituições competentes."
)
escrever("=" * 70)

texto_final = saida.getvalue()

# =====================================
# IMPRESSÃO NA TELA
# =====================================

print(texto_final)

# =====================================
# GRAVAÇÃO EM ARQUIVO
# (mesmo arquivo que o chat_escudo.py já lê
# quando a pergunta pede um relatório executivo)
# =====================================

with open("relatorio_executivo.txt", "w", encoding="utf-8") as arquivo:
    arquivo.write(texto_final)

print("\nArquivo relatorio_executivo.txt atualizado com sucesso.")
