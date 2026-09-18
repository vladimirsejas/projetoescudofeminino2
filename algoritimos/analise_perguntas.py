import sqlite3
import pandas as pd

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

df = pd.read_sql("SELECT * FROM perguntas_usuarios", conn)

conn.close()

# =====================================
# RESULTADO
# =====================================

print("\n=== ANÁLISE DAS PERGUNTAS JÁ FEITAS AO CHAT ===\n")

if df.empty:
    print(
        "Ainda não há perguntas registradas. Use o chat_escudo.py "
        "algumas vezes e rode este script de novo."
    )

else:

    print(f"Total de perguntas registradas: {len(df)}\n")

    print("--- Perguntas por categoria ---\n")
    print(
        df["categoria"]
        .value_counts()
        .to_string()
    )

    print("\n--- Taxa de reconhecimento ---\n")

    reconhecidas = (df["reconhecida"] == "SIM").sum()
    nao_reconhecidas_qtd = (df["reconhecida"] == "NAO").sum()
    total = len(df)

    print(f"Reconhecidas: {reconhecidas} ({reconhecidas / total * 100:.1f}%)")
    print(
        f"Não reconhecidas: {nao_reconhecidas_qtd} "
        f"({nao_reconhecidas_qtd / total * 100:.1f}%)"
    )

    nao_reconhecidas = df[df["reconhecida"] == "NAO"]

    if not nao_reconhecidas.empty:

        print(
            "\n--- Perguntas NÃO reconhecidas ---\n"
            "(candidatas a virar novos sinônimos no motor de "
            "intenções — quanto mais se repetirem, maior a "
            "prioridade de cobrir)\n"
        )

        for pergunta, quantidade in (
            nao_reconhecidas["pergunta"]
            .value_counts()
            .items()
        ):
            print(f"[{quantidade}x] {pergunta}")

    else:
        print(
            "\nNenhuma pergunta ficou sem reconhecimento até agora."
        )
