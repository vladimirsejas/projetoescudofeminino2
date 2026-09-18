import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# BASE DE CONHECIMENTO
# =====================================

base = pd.read_sql(
    """
    SELECT *
    FROM base_conhecimento
    """,
    conn
)

# =====================================
# PRIORIZAÇÃO
# =====================================

priorizacao = pd.read_sql(
    """
    SELECT *
    FROM priorizacao_executiva
    """,
    conn
)

# =====================================
# VULNERABILIDADE
# =====================================

try:

    vulnerabilidade = pd.read_sql(
        """
        SELECT *
        FROM vulnerabilidade
        """,
        conn
    )

except Exception:

    vulnerabilidade = pd.DataFrame()

conn.close()

# =====================================
# BUSCA CÂNCER
# =====================================

def buscar_cancer(nome_cancer):

    cancer = nome_cancer.upper()

    linha = base[
        base["tipo_cancer"].str.upper()
        ==
        cancer
    ]

    if linha.empty:
        return None

    return linha.iloc[0]

# =====================================
# RACIOCÍNIO
# =====================================

def raciocinar_cancer(nome_cancer):

    registro = buscar_cancer(nome_cancer)

    if registro is None:

        return {
            "o_que_aconteceu":
                "Câncer não encontrado.",
            "por_que_aconteceu":
                "",
            "isso_e_importante":
                "",
            "impacto":
                "",
            "o_que_deve_ser_feito":
                ""
        }

    resposta = {}

    # CAMADA 1

    resposta["o_que_aconteceu"] = (

        f"{registro['tipo_cancer']} foi "
        f"classificado como "
        f"{registro['nivel_prioridade']}."

    )

    # CAMADA 2

    resposta["por_que_aconteceu"] = (
        registro["motivo"]
    )

    # CAMADA 3

    resposta["isso_e_importante"] = (

        f"Este câncer está atualmente "
        f"classificado com prioridade "
        f"{registro['nivel_prioridade']} "
        f"para o município de Rio Claro."

    )

    # CAMADA 4

    resposta["impacto"] = (
        registro["impacto"]
    )

    # CAMADA 5

    resposta["o_que_deve_ser_feito"] = (
        registro["recomendacao"]
    )

    return resposta