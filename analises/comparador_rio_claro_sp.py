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

print("\nCOMPARADOR RIO CLARO X SP\n")

for cancer in canceres:

    sql_rc = f"""
    SELECT
        ano,
        COUNT(*) AS internacoes
    FROM internacoes
    WHERE tipo_cancer = '{cancer}'
    AND origem = 'RIO_CLARO'
    GROUP BY ano
    ORDER BY ano
    """

    sql_sp = f"""
    SELECT
        ano,
        COUNT(*) AS internacoes
    FROM internacoes
    WHERE tipo_cancer = '{cancer}'
    AND origem = 'SP'
    GROUP BY ano
    ORDER BY ano
    """

    rc = pd.read_sql(sql_rc, conexao)
    sp = pd.read_sql(sql_sp, conexao)

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

        var_rc = (
            (rc_2025 - rc_2024)
            / rc_2024
        ) * 100

        var_sp = (
            (sp_2025 - sp_2024)
            / sp_2024
        ) * 100

        diferenca = var_rc - var_sp

        print("-" * 60)
        print(cancer)
        print(f"Rio Claro: {var_rc:.2f}%")
        print(f"SP: {var_sp:.2f}%")
        print(f"Diferenca: {diferenca:.2f}%")

        if diferenca > 10:
            print("ALERTA: Rio Claro acima da tendencia estadual")

        elif diferenca < -10:
            print("ALERTA: Rio Claro abaixo da tendencia estadual")

        else:
            print("Comportamento semelhante ao Estado")

    except:
        print(f"{cancer}: dados insuficientes")

conexao.close()