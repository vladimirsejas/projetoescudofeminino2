import json
import re
import sqlite3
from urllib.request import urlopen

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"
URL_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios"


def normalizar_origem(nome, codigo_ibge):
    texto = re.sub(r"[^A-Z0-9]+", "_", nome.upper()).strip("_")
    if not texto:
        texto = f"MUNICIPIO_{codigo_ibge}"
    return texto


def carregar_municipios_ibge():
    with urlopen(URL_IBGE, timeout=30) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))

    municipios = []
    for item in dados:
        codigo = int(item["id"])
        nome = item["nome"]
        municipios.append(
            {
                "codigo_ibge": codigo,
                "origem": normalizar_origem(nome, codigo),
                "nome": nome,
                "uf": "SP",
            }
        )

    return municipios


def atualizar():
    municipios = carregar_municipios_ibge()

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

    for municipio in municipios:
        cursor.execute("""
            INSERT INTO municipios (codigo_ibge, origem, nome, uf)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(codigo_ibge) DO UPDATE SET
                origem = excluded.origem,
                nome = excluded.nome,
                uf = excluded.uf
        """, (
            municipio["codigo_ibge"],
            municipio["origem"],
            municipio["nome"],
            municipio["uf"],
        ))

    conexao.commit()

    total = cursor.execute(
        "SELECT COUNT(*) FROM municipios WHERE uf = 'SP'"
    ).fetchone()[0]

    sao_paulo = cursor.execute("""
        SELECT codigo_ibge, origem, nome, uf
        FROM municipios
        WHERE codigo_ibge = 3550308
    """).fetchone()

    rio_claro = cursor.execute("""
        SELECT codigo_ibge, origem, nome, uf
        FROM municipios
        WHERE codigo_ibge = 3543907
    """).fetchone()

    print(f"Municípios de SP cadastrados: {total}")
    print(f"São Paulo: {sao_paulo}")
    print(f"Rio Claro: {rio_claro}")

    conexao.close()


if __name__ == "__main__":
    atualizar()
