import sqlite3
import pandas as pd

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# CARGA DAS TABELAS
# =====================================

fichas = pd.read_sql("""
SELECT *
FROM fichas_ia
""", conn)

perfil = pd.read_sql("""
SELECT *
FROM perfil_epidemiologico
""", conn)

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

    respondeu = False

    # =====================================
    # PERFIL DE CÂNCER
    # =====================================

    for _, row in fichas.iterrows():

        if row["tipo_cancer"] in pergunta_upper:

            print("\n")
            print(row["ficha"])

            respondeu = True
            break

    # =====================================
    # MAIOR PRIORIDADE
    # =====================================

    if not respondeu and (
        "ATENCAO" in pergunta_upper
        or "ATENÇÃO" in pergunta_upper
        or "PRIORIDADE" in pergunta_upper
        or "RISCO" in pergunta_upper
    ):

        df = perfil.sort_values(
            "pontuacao_final",
            ascending=False
        )

        r = df.iloc[0]

        print("\nResposta:\n")

        print(
            f"O câncer que merece maior atenção "
            f"atualmente é {r['tipo_cancer']}."
        )

        print(
            f"Classificação: "
            f"{r['nivel_prioridade']}."
        )

        print(
            f"Pontuação final: "
            f"{r['pontuacao_final']:.2f}."
        )

        respondeu = True

    # =====================================
    # MORTALIDADE
    # =====================================

    if not respondeu and (
        "MORTALIDADE" in pergunta_upper
        or "OBITO" in pergunta_upper
        or "ÓBITO" in pergunta_upper
        or "MATA" in pergunta_upper
    ):

        df = perfil.sort_values(
            "taxa_mortalidade",
            ascending=False
        )

        r = df.iloc[0]

        print("\nResposta:\n")

        print(
            f"{r['tipo_cancer']} possui a maior "
            f"taxa de mortalidade "
            f"({r['taxa_mortalidade']:.2f}%)."
        )

        respondeu = True

    # =====================================
    # CUSTOS
    # =====================================

    if not respondeu and (
        "CUSTO" in pergunta_upper
        or "CUSTOS" in pergunta_upper
        or "GASTO" in pergunta_upper
        or "FINANCEIRO" in pergunta_upper
    ):

        df = perfil.sort_values(
            "valor_total",
            ascending=False
        )

        r = df.iloc[0]

        print("\nResposta:\n")

        print(
            f"{r['tipo_cancer']} apresenta "
            f"o maior custo hospitalar."
        )

        print(
            f"Valor total: "
            f"R$ {r['valor_total']:,.2f}"
        )

        respondeu = True

    # =====================================
    # PERMANÊNCIA
    # =====================================

    if not respondeu and (
        "PERMANENCIA" in pergunta_upper
        or "PERMANÊNCIA" in pergunta_upper
        or "LEITO" in pergunta_upper
        or "INTERNADO" in pergunta_upper
    ):

        df = perfil.sort_values(
            "permanencia_media",
            ascending=False
        )

        r = df.iloc[0]

        print("\nResposta:\n")

        print(
            f"{r['tipo_cancer']} apresenta "
            f"a maior permanência hospitalar."
        )

        print(
            f"Média: "
            f"{r['permanencia_media']:.2f} dias."
        )

        respondeu = True

    # =====================================
    # FAIXA ETÁRIA
    # =====================================

    if not respondeu and (
        "IDADE" in pergunta_upper
        or "FAIXA" in pergunta_upper
        or "ETARIA" in pergunta_upper
        or "ETÁRIA" in pergunta_upper
    ):

        print("\nResposta:\n")

        for _, row in perfil.iterrows():

            print(
                f"{row['tipo_cancer']} -> "
                f"{row['faixa_etaria']}"
            )

        respondeu = True

    # =====================================
    # DESCONHECIDO
    # =====================================

    if not respondeu:

        print(
            "\nAinda não compreendi essa pergunta."
        )

conn.close()

print("\nChat encerrado.")