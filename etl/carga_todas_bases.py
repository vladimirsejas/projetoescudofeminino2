import os
import re
import sqlite3
import pandas as pd

BASE_DADOS = r"C:\projetoescudofeminino2\dados"
BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

MAPA = {
    "cancer_mama_rio_claro": ("MAMA", "RIO_CLARO"),
    "cancer_mama_sp": ("MAMA", "SP"),
    "cancer_colorretal_rio_claro": ("COLORRETAL", "RIO_CLARO"),
    "cancer_colorretal_sp": ("COLORRETAL", "SP"),
    "cancer_colo_utero_rio_claro": ("COLO_UTERO", "RIO_CLARO"),
    "cancer_colo_utero_sp": ("COLO_UTERO", "SP"),
    "cancer_ovario_rio_claro": ("OVARIO", "RIO_CLARO"),
    "cancer_ovario_sp": ("OVARIO", "SP"),
    "cancer_pulmao_rio_claro": ("PULMAO", "RIO_CLARO"),
    "cancer_pulmao_sp": ("PULMAO", "SP"),
    "cancer_tireoide_rio_claro": ("TIREOIDE", "RIO_CLARO"),
    "cancer_tireoide_sp": ("TIREOIDE", "SP"),
    "cancer_pele_nao_melanoma_rio_claro": ("PELE_NAO_MELANOMA", "RIO_CLARO"),
    "cancer_pele_nao_melanoma_sp": ("PELE_NAO_MELANOMA", "SP"),
}

CANDIDATOS_CODIGO_MUNICIPIO = [
    "MUNIC_RES",
    "MUNIC_RESID",
    "CODMUNRES",
    "COD_MUN_RES",
    "CODMUN_RES",
    "MUNICIPIO_RES",
    "MUNICIPIO_RESIDENCIA",
    "MUNICIPIO",
]


def limpar_codigo(valor):
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.endswith(".0"):
        texto = texto[:-2]

    digitos = re.sub(r"\D", "", texto)

    if len(digitos) in (6, 7):
        return int(digitos)

    return None


def encontrar_coluna_codigo(df):
    colunas = {str(c).strip().upper(): c for c in df.columns}

    for candidato in CANDIDATOS_CODIGO_MUNICIPIO:
        if candidato in colunas:
            return colunas[candidato]

    return None


def carregar_catalogo(conexao):
    linhas = conexao.execute(
        "SELECT codigo_ibge, origem, nome, uf FROM municipios WHERE uf = 'SP'"
    ).fetchall()

    por_codigo = {}
    for codigo, origem, nome, uf in linhas:
        texto = str(codigo)
        por_codigo[texto] = origem
        por_codigo[texto[:6]] = origem

    return por_codigo


def resolver_municipios(df, origem, catalogo):
    # A pasta de Rio Claro já representa o recorte municipal original.
    # Não reclassificamos esses registros pelo código do CSV.
    if origem == "RIO_CLARO":
        return (
            pd.Series(["RIO_CLARO"] * len(df), index=df.index),
            pd.Series([3543907] * len(df), index=df.index),
        )

    coluna = encontrar_coluna_codigo(df)

    if origem == "SP" and coluna is None:
        raise RuntimeError(
            "Os arquivos estaduais de SP não possuem uma coluna de código "
            "municipal reconhecida. O ETL foi interrompido para não "
            "misturar todo o Estado em um único município. "
            f"Colunas encontradas: {list(df.columns)}"
        )

    codigos = df[coluna].map(limpar_codigo)

    municipios = codigos.map(
        lambda codigo: catalogo.get(str(codigo)) if codigo is not None else None
    )

    desconhecidos = municipios.isna()

    if desconhecidos.any():
        quantidade = int(desconhecidos.sum())
        exemplos = codigos[desconhecidos].dropna().astype(str).head(10).tolist()
        raise RuntimeError(
            f"{quantidade} registros de {origem} possuem código municipal "
            "sem correspondência no catálogo IBGE. Exemplos: "
            f"{exemplos}"
        )

    return municipios, codigos



def carregar():
    conexao = sqlite3.connect(BANCO)

    # O catálogo deve existir antes da carga.
    try:
        catalogo = carregar_catalogo(conexao)
    except sqlite3.OperationalError as erro:
        conexao.close()
        raise RuntimeError(
            "A tabela municipios não existe. Execute primeiro "
            "etl\criar_tabela_municipios.py."
        ) from erro

    total_registros = 0
    primeira_carga = True

    for pasta in sorted(os.listdir(BASE_DADOS)):

        if pasta not in MAPA:
            continue

        caminho_pasta = os.path.join(BASE_DADOS, pasta)

        arquivos_csv = sorted(
            arquivo
            for arquivo in os.listdir(caminho_pasta)
            if arquivo.lower().endswith(".csv")
        )

        if not arquivos_csv:
            continue

        arquivo_csv = os.path.join(caminho_pasta, arquivos_csv[0])
        tipo_cancer, origem = MAPA[pasta]

        print("\n" + "=" * 60)
        print("PASTA:", pasta)
        print("TIPO:", tipo_cancer)
        print("ORIGEM:", origem)

        df = pd.read_csv(
            arquivo_csv,
            sep=";",
            encoding="latin1",
            low_memory=False
        )

        municipios, codigos = resolver_municipios(
            df, origem, catalogo
        )

        dados = pd.DataFrame({
            "tipo_cancer": [tipo_cancer] * len(df),
            "origem": [origem] * len(df),
            "municipio": municipios,
            "codigo_ibge": codigos,
            "ano": df["ANO_CMPT"],
            "idade": df["IDADE"],
            "dias_permanencia": df["DIAS_PERM"],
            "obito": df["MORTE"],
            "valor_total": df["VAL_TOT"]
        })

        print("Municípios identificados:", dados["municipio"].nunique())
        print(dados["municipio"].value_counts().head(10))
        print(dados.head())

        dados.to_sql(
            "internacoes",
            conexao,
            if_exists="replace" if primeira_carga else "append",
            index=False
        )

        primeira_carga = False
        total_registros += len(dados)

        print("OK ->", len(dados), "registros")

    conexao.close()

    print("\n" + "=" * 60)
    print("CARGA TERRITORIAL FINALIZADA")
    print("TOTAL:", total_registros)
    print("=" * 60)


if __name__ == "__main__":
    carregar()
