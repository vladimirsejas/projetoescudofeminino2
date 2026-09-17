import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

canceres = [
    "MAMA",
    "COLORRETAL",
    "PELE_NAO_MELANOMA",
    "COLO_UTERO",
    "PULMAO",
    "OVARIO",
    "TIREOIDE"
]

eventos = []

for cancer in canceres:

    sql_rc = f"""
    SELECT ano, COUNT(*) AS internacoes
    FROM internacoes
    WHERE tipo_cancer = '{cancer}'
    AND origem = 'RIO_CLARO'
    GROUP BY ano
    ORDER BY ano
    """

    sql_sp = f"""
    SELECT ano, COUNT(*) AS internacoes
    FROM internacoes
    WHERE tipo_cancer = '{cancer}'
    AND origem = 'SP'
    GROUP BY ano
    ORDER BY ano
    """

    rc = pd.read_sql(sql_rc, conexao)
    sp = pd.read_sql(sql_sp, conexao)

    if len(rc) == 0 or len(sp) == 0:
        continue

    try:

        rc_2024 = int(
            rc.loc[rc["ano"] == 2024, "internacoes"].values[0]
        )

        rc_2025 = int(
            rc.loc[rc["ano"] == 2025, "internacoes"].values[0]
        )

        sp_2024 = int(
            sp.loc[sp["ano"] == 2024, "internacoes"].values[0]
        )

        sp_2025 = int(
            sp.loc[sp["ano"] == 2025, "internacoes"].values[0]
        )

        var_rc = ((rc_2025 - rc_2024) / rc_2024) * 100
        var_sp = ((sp_2025 - sp_2024) / sp_2024) * 100

        diferenca = var_rc - var_sp

        if diferenca > 10:
            evento = "ACIMA DA TENDENCIA ESTADUAL"
        elif diferenca < -10:
            evento = "ABAIXO DA TENDENCIA ESTADUAL"
        else:
            evento = "COMPORTAMENTO SEMELHANTE AO ESTADO"

        eventos.append(
            [
                cancer,
                round(var_rc, 2),
                round(var_sp, 2),
                round(diferenca, 2),
                evento
            ]
        )

    except:
        pass

conexao.close()

resultado = pd.DataFrame(
    eventos,
    columns=[
        "cancer",
        "variacao_rio_claro",
        "variacao_sp",
        "diferenca",
        "evento"
    ]
)

print()
print("=" * 70)
print("GERADOR DE EVENTOS")
print("=" * 70)
print()
print(resultado)