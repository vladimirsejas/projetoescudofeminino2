import sqlite3
import pandas as pd

banco = r"C:\projetoescudofeminino\banco\escudo_feminino.db"

conexao = sqlite3.connect(banco)

sql_rc = """
SELECT
    ano,
    COUNT(*) AS internacoes
FROM internacoes
WHERE tipo_cancer = 'MAMA'
AND origem = 'RIO_CLARO'
GROUP BY ano
ORDER BY ano
"""

sql_sp = """
SELECT
    ano,
    COUNT(*) AS internacoes
FROM internacoes
WHERE tipo_cancer = 'MAMA'
AND origem = 'SP'
GROUP BY ano
ORDER BY ano
"""

rc = pd.read_sql(sql_rc, conexao)
sp = pd.read_sql(sql_sp, conexao)

conexao.close()

rc_2024 = int(rc.loc[rc["ano"] == 2024, "internacoes"].values[0])
rc_2025 = int(rc.loc[rc["ano"] == 2025, "internacoes"].values[0])

sp_2024 = int(sp.loc[sp["ano"] == 2024, "internacoes"].values[0])
sp_2025 = int(sp.loc[sp["ano"] == 2025, "internacoes"].values[0])

var_rc = ((rc_2025 - rc_2024) / rc_2024) * 100
var_sp = ((sp_2025 - sp_2024) / sp_2024) * 100

print()
print("MAMA - RIO CLARO X SP")
print()

print(f"Rio Claro 2024: {rc_2024}")
print(f"Rio Claro 2025: {rc_2025}")
print(f"Variacao Rio Claro: {var_rc:.2f}%")

print()

print(f"SP 2024: {sp_2024}")
print(f"SP 2025: {sp_2025}")
print(f"Variacao SP: {var_sp:.2f}%")

print()

if var_rc > var_sp:
    print("Rio Claro cresceu acima da tendencia estadual.")
elif var_rc < var_sp:
    print("Rio Claro cresceu abaixo da tendencia estadual.")
else:
    print("Rio Claro acompanhou a tendencia estadual.")