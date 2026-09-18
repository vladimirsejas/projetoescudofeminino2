import sqlite3
import pandas as pd
from datetime import datetime

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# VERIFICAÇÃO DE PRÉ-REQUISITOS
#
# Evita erro confuso no meio do chat: se uma
# tabela que o motor precisa ainda não existe,
# avisa exatamente qual algoritmo rodar antes.
# =====================================

TABELAS_NECESSARIAS = [
    "priorizacao_executiva",
    "tendencia_estadual",
    "anomalias",
    "mortalidade",
    "custos_hospitalares",
    "permanencia_hospitalar",
    "faixa_etaria",
    "memoria_ia",
    "internacoes",
]

tabelas_existentes = set(
    row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
)

faltando = [t for t in TABELAS_NECESSARIAS if t not in tabelas_existentes]

if faltando:

    print("\nERRO: as seguintes tabelas ainda não existem no banco:\n")

    for tabela in faltando:
        print(f"  - {tabela}")

    print(
        "\nRode os algoritmos correspondentes (ver seção 4/5 do "
        "relatório de referência) antes de usar este chat."
    )

    conn.close()
    raise SystemExit(1)

# =====================================
# TABELA DE APRENDIZADO DE PERGUNTAS
# (Missão técnica nº 9)
# =====================================

conn.execute("""
CREATE TABLE IF NOT EXISTS perguntas_usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT,
    pergunta TEXT,
    categoria TEXT,
    reconhecida TEXT
)
""")

# se a tabela já existia na versão antiga (só data_hora/pergunta),
# adiciona as colunas novas sem apagar o histórico já registrado
for coluna in ("categoria", "reconhecida"):
    try:
        conn.execute(
            f"ALTER TABLE perguntas_usuarios ADD COLUMN {coluna} TEXT"
        )
    except sqlite3.OperationalError:
        pass  # coluna já existe

conn.commit()

# =====================================
# CARGA DO CONHECIMENTO
# (só leitura — nada é recalculado aqui)
# =====================================

priorizacao = pd.read_sql("SELECT * FROM priorizacao_executiva", conn)
tendencia = pd.read_sql("SELECT * FROM tendencia_estadual", conn)
anomalias_df = pd.read_sql("SELECT * FROM anomalias", conn)
mortalidade_df = pd.read_sql("SELECT * FROM mortalidade", conn)
custos_df = pd.read_sql("SELECT * FROM custos_hospitalares", conn)
permanencia_df = pd.read_sql("SELECT * FROM permanencia_hospitalar", conn)
faixa_df = pd.read_sql("SELECT * FROM faixa_etaria", conn)
memoria = pd.read_sql("SELECT * FROM memoria_ia", conn)

canceres = priorizacao["tipo_cancer"].tolist()


# =====================================
# REGISTRO DE USO (Missão nº 9)
# =====================================

def registrar_pergunta(pergunta, categoria, reconhecida):

    conn.execute(
        """
        INSERT INTO perguntas_usuarios
        (data_hora, pergunta, categoria, reconhecida)
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            pergunta,
            categoria,
            reconhecida
        )
    )

    conn.commit()


# =====================================
# MOTOR DE INTENÇÕES
#
# União de todas as palavras-chave que estavam
# espalhadas em chat_escudo.py, motor_respostas.py,
# orquestrador_ia.py e perguntas_negocio.py.
# =====================================

def classificar_intencao(pergunta_upper):

    for cancer in canceres:
        if cancer in pergunta_upper:
            return "CANCER_ESPECIFICO"

    if any(p in pergunta_upper for p in (
        "ATENCAO", "ATENÇÃO", "PRIORIDADE", "RISCO"
    )):
        return "PRIORIDADE_MAXIMA"

    if any(p in pergunta_upper for p in (
        "TOP", "3 MAIORES", "TRÊS MAIORES", "TRES MAIORES"
    )):
        return "TOP_PRIORIDADES"

    if any(p in pergunta_upper for p in (
        "MORTALIDADE", "OBITO", "ÓBITO", "MATA", "MORTE"
    )):
        return "MORTALIDADE"

    if any(p in pergunta_upper for p in (
        "CUSTO", "CUSTOS", "GASTO", "FINANCEIRO"
    )):
        return "CUSTO"

    if any(p in pergunta_upper for p in (
        "PERMANENCIA", "PERMANÊNCIA", "LEITO", "INTERNADO"
    )):
        return "PERMANENCIA"

    if any(p in pergunta_upper for p in (
        "IDADE", "FAIXA", "ETARIA", "ETÁRIA"
    )):
        return "FAIXA_ETARIA"

    if any(p in pergunta_upper for p in (
        "TENDENCIA", "TENDÊNCIA", "ESTADUAL"
    )):
        return "TENDENCIA_ESTADUAL"

    if any(p in pergunta_upper for p in (
        "ANOMALIA", "PADRAO", "PADRÃO"
    )):
        return "ANOMALIAS"

    if any(p in pergunta_upper for p in (
        "INCIDENCIA", "INCIDÊNCIA", "INTERNACOES", "INTERNAÇÕES"
    )):
        return "INCIDENCIA"

    if "RELATORIO" in pergunta_upper or "RELATÓRIO" in pergunta_upper:
        return "RELATORIO_EXECUTIVO"

    return "DESCONHECIDA"


# =====================================
# RESPOSTAS
# =====================================

def responder(intencao, pergunta_upper):

    if intencao == "CANCER_ESPECIFICO":

        cancer = next(c for c in canceres if c in pergunta_upper)
        linha = memoria[memoria["tipo_cancer"] == cancer]

        if linha.empty:
            print(f"\nAinda não há memória registrada para {cancer}.")
            return

        print("\n")
        print(linha.iloc[0]["memoria"])
        return

    if intencao == "PRIORIDADE_MAXIMA":

        r = priorizacao.sort_values(
            "pontuacao_final", ascending=False
        ).iloc[0]

        print("\nResposta:\n")
        print(
            f"O câncer que merece maior atenção atualmente "
            f"é {r['tipo_cancer']}."
        )
        print(f"Classificação: {r['nivel_prioridade']}.")
        print(f"Pontuação final: {r['pontuacao_final']:.2f}.")

        linha = memoria[memoria["tipo_cancer"] == r["tipo_cancer"]]

        if not linha.empty:
            print("\n")
            print(linha.iloc[0]["memoria"])

        return

    if intencao == "TOP_PRIORIDADES":

        top3 = priorizacao.sort_values(
            "pontuacao_final", ascending=False
        ).head(3)

        print("\nTOP 3 PRIORIDADES:\n")

        for i, (_, row) in enumerate(top3.iterrows(), start=1):
            print(
                f"{i}º {row['tipo_cancer']} — "
                f"{row['nivel_prioridade']} "
                f"({row['pontuacao_final']:.2f})"
            )

        print(
            "\nPergunte pelo nome de um câncer específico para "
            "ver o motivo, o impacto e a recomendação."
        )
        return

    if intencao == "MORTALIDADE":

        r = mortalidade_df.sort_values(
            "taxa_mortalidade", ascending=False
        ).iloc[0]

        print("\nResposta:\n")
        print(
            f"{r['tipo_cancer']} possui a maior taxa de "
            f"mortalidade ({r['taxa_mortalidade']:.2f}%)."
        )
        return

    if intencao == "CUSTO":

        r = custos_df.sort_values(
            "valor_total", ascending=False
        ).iloc[0]

        print("\nResposta:\n")
        print(f"{r['tipo_cancer']} apresenta o maior custo hospitalar.")
        print(f"Valor total: R$ {r['valor_total']:,.2f}")
        return

    if intencao == "PERMANENCIA":

        r = permanencia_df.sort_values(
            "permanencia_media", ascending=False
        ).iloc[0]

        print("\nResposta:\n")
        print(
            f"{r['tipo_cancer']} apresenta a maior "
            f"permanência hospitalar."
        )
        print(f"Média: {r['permanencia_media']:.2f} dias.")
        return

    if intencao == "FAIXA_ETARIA":

        dominante = (
            faixa_df
            .sort_values("internacoes", ascending=False)
            .drop_duplicates("tipo_cancer")
        )

        print("\nResposta:\n")

        for _, row in dominante.iterrows():
            print(f"{row['tipo_cancer']} -> {row['faixa_etaria']}")

        return

    if intencao == "TENDENCIA_ESTADUAL":

        r = tendencia.sort_values(
            "desvio", ascending=False
        ).iloc[0]

        print("\nResposta:\n")

        if r["desvio"] >= 0:
            print(
                f"{r['tipo_cancer']} está {r['desvio']:.2f}% "
                f"acima da tendência estadual."
            )
        else:
            print(
                f"{r['tipo_cancer']} está {abs(r['desvio']):.2f}% "
                f"abaixo da tendência estadual."
            )

        return

    if intencao == "ANOMALIAS":

        df = anomalias_df[anomalias_df["situacao"] != "NORMAL"]

        print("\nResposta:\n")

        if df.empty:
            print("Nenhuma anomalia identificada.")
        else:
            for _, row in df.iterrows():
                print(f"{row['tipo_cancer']} - {row['situacao']}")

        return

    if intencao == "INCIDENCIA":

        df = pd.read_sql("""
        SELECT tipo_cancer, COUNT(*) AS total
        FROM internacoes
        GROUP BY tipo_cancer
        ORDER BY total DESC
        LIMIT 1
        """, conn)

        r = df.iloc[0]

        print("\nResposta:\n")
        print(
            f"O câncer com maior incidência hospitalar "
            f"é {r['tipo_cancer']}."
        )
        return

    if intencao == "RELATORIO_EXECUTIVO":

        try:
            with open(
                "relatorio_executivo.txt", "r", encoding="utf-8"
            ) as arquivo:
                print("\n")
                print(arquivo.read())

        except FileNotFoundError:
            print(
                "\nArquivo relatorio_executivo.txt não encontrado "
                "na pasta atual."
            )

        return

    print("\nAinda não compreendi essa pergunta.")
    print(
        "Tente perguntar sobre: prioridade, mortalidade, custo, "
        "permanência, faixa etária, tendência estadual, anomalias, "
        "incidência, relatório executivo, ou o nome de um câncer "
        "específico (ex.: MAMA, COLO_UTERO)."
    )


# =====================================
# CHAT
# =====================================

print("\n=== CHAT ESCUDO FEMININO ===\n")

while True:

    pergunta = input(
        "\nPergunta (digite 'sair' para encerrar): "
    )

    if pergunta.lower() == "sair":
        break

    pergunta_upper = pergunta.upper()

    intencao = classificar_intencao(pergunta_upper)

    responder(intencao, pergunta_upper)

    registrar_pergunta(
        pergunta,
        intencao,
        "SIM" if intencao != "DESCONHECIDA" else "NAO"
    )

conn.close()

print("\nChat encerrado.")
