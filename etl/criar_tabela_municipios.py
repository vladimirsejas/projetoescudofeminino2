import sqlite3

# =====================================
# CATÁLOGO DE MUNICÍPIOS
#
# Identifica territorialmente cada valor já usado na coluna
# internacoes.origem pelo código oficial do IBGE. `origem` continua
# sendo o identificador interno (o mesmo usado em todo WHERE origem
# = ? do projeto) -- esta tabela só adiciona metadados em cima dele:
# código IBGE, nome para apresentação e UF.
#
# SP não entra aqui: é a referência estadual (todo o Estado de São
# Paulo), não um município.
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conexao = sqlite3.connect(BANCO)

cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS municipios (
    codigo_ibge INTEGER PRIMARY KEY,
    origem TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    uf TEXT NOT NULL
)
""")

# Código IBGE oficial de Rio Claro, SP: 3543907
# (confirmado em geoftp.ibge.gov.br/.../mapas_municipais/SP/3543907.pdf)
cursor.execute("""
INSERT OR IGNORE INTO municipios (codigo_ibge, origem, nome, uf)
VALUES (3543907, 'RIO_CLARO', 'Rio Claro', 'SP')
""")

conexao.commit()

print("\n=== MUNICÍPIOS CADASTRADOS ===\n")

for linha in cursor.execute(
    "SELECT codigo_ibge, origem, nome, uf FROM municipios ORDER BY nome"
):
    print(linha)

print("\nTabela municipios criada/atualizada com sucesso.")

conexao.close()
