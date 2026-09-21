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


def selecionar_csv_unico(caminho_pasta, pasta):
    """
    Exige um único CSV por pasta -- a carga lê só um arquivo (não
    concatena vários). Se sobrar mais de um (ex.: o CSV antigo
    2021-2025 ao lado do novo 2013-2025 recém-baixado), a ordem
    alfabética decidiria sozinha qual entra no banco, sem avisar, e
    o erro passaria despercebido. Falhar aqui é melhor do que
    carregar o arquivo errado ou contar o mesmo ano duas vezes.
    """

    arquivos_csv = sorted(
        arquivo
        for arquivo in os.listdir(caminho_pasta)
        if arquivo.lower().endswith(".csv")
    )

    if not arquivos_csv:
        return None

    if len(arquivos_csv) > 1:
        raise RuntimeError(
            f"A pasta '{pasta}' tem mais de um CSV: {arquivos_csv}. "
            "A carga lê um único arquivo por pasta -- deixe só o mais "
            "atual (ex.: o que cobre 2013-2025) dentro dela e mova os "
            "arquivos antigos para fora de dados\\, senão a carga pode "
            "pegar o arquivo errado sem avisar ou duplicar anos que "
            "existam nos dois arquivos."
        )

    return os.path.join(caminho_pasta, arquivos_csv[0])


def encontrar_pastas_validas(base_dados):
    """
    Exige que as 14 subpastas esperadas estejam presentes. Sem isso,
    a carga poderia terminar com uma base incompleta sem deixar claro
    que um câncer/território ficou de fora.
    """

    pastas_existentes = {
        entrada
        for entrada in os.listdir(base_dados)
        if entrada in MAPA
    }

    esperadas = set(MAPA)
    ausentes = sorted(esperadas - pastas_existentes)

    if ausentes:
        raise RuntimeError(
            f"Faltam {len(ausentes)} subpasta(s) esperada(s) em "
            f"'{base_dados}': {ausentes}. "
            "A carga exige as 14 pastas (7 cânceres x 2 recortes)."
        )

    return sorted(pastas_existentes)

def detectar_separador(caminho_csv, encoding="latin1"):
    """
    Descobre se o CSV usa ';' (padrão do extrato bruto do DATASUS) ou
    ',' (visto em arquivos consolidados por outra ferramenta, ex.:
    pysus) -- olhando só a linha de cabeçalho, sem carregar o arquivo
    inteiro. Sem isso, um CSV separado por vírgula lido com sep=';'
    vira uma única coluna gigante e a carga falha com KeyError em
    ANO_CMPT sem dizer por quê.
    """

    with open(caminho_csv, encoding=encoding) as arquivo:
        cabecalho = arquivo.readline()

    def colunas(separador):
        return {coluna.strip().strip('"') for coluna in cabecalho.split(separador)}

    if "ANO_CMPT" in colunas(";"):
        return ";"

    if "ANO_CMPT" in colunas(","):
        return ","

    raise RuntimeError(
        f"Não encontrei a coluna ANO_CMPT no cabeçalho de '{caminho_csv}' "
        "nem separando por ';' nem por ','. Cabeçalho encontrado: "
        f"{cabecalho.strip()!r}"
    )


def carregar_catalogo(conexao):
    linhas = conexao.execute(
        "SELECT codigo_ibge, origem, nome, uf "
        "FROM municipios WHERE uf = 'SP'"
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
            df,
            pd.Series(["RIO_CLARO"] * len(df), index=df.index),
            pd.Series([3543907] * len(df), index=df.index),
        )

    coluna = encontrar_coluna_codigo(df)

    if origem == "SP" and coluna is None:
        raise RuntimeError(
            "Os arquivos estaduais de SP não possuem uma coluna de código "
            "municipal reconhecida. A carga foi interrompida para não "
            "misturar todo o Estado em um único município. "
            f"Colunas encontradas: {list(df.columns)}"
        )

    codigos = df[coluna].map(limpar_codigo)

    municipios = codigos.map(
        lambda codigo: catalogo.get(str(codigo))
        if codigo is not None else None
    )

    if origem == "SP":
        codigos_texto = codigos.astype("Int64").astype("string")
        fora_de_sp = ~codigos_texto.str.startswith("35", na=False)

        if fora_de_sp.any():
            quantidade = int(fora_de_sp.sum())
            exemplos = (
                codigos[fora_de_sp]
                .dropna()
                .astype(int)
                .astype(str)
                .head(10)
                .tolist()
            )
            print(
                f"ATENÇÃO: {quantidade} registros de {origem} foram "
                "descartados porque a residência não pertence ao "
                f"Estado de São Paulo. Exemplos: {exemplos}"
            )

            df = df.loc[~fora_de_sp].copy()
            codigos = codigos.loc[~fora_de_sp]
            municipios = municipios.loc[~fora_de_sp]

    desconhecidos = municipios.isna()

    if desconhecidos.any():
        quantidade = int(desconhecidos.sum())
        exemplos = (
            codigos[desconhecidos]
            .dropna()
            .astype(int)
            .astype(str)
            .head(10)
            .tolist()
        )
        raise RuntimeError(
            f"{quantidade} registros de {origem} possuem código municipal "
            "SP sem correspondência no catálogo IBGE depois da filtragem. "
            f"Exemplos: {exemplos}"
        )

    return df, municipios, codigos


VERSAO_CARGA = "carga_todas_bases.py -- com detecção automática de separador (; ou ,)"


def carregar():
    print(VERSAO_CARGA)

    conexao = sqlite3.connect(BANCO)

    try:
        catalogo = carregar_catalogo(conexao)
    except sqlite3.OperationalError as erro:
        conexao.close()
        raise RuntimeError(
            "A tabela municipios não existe. Execute primeiro "
            "etl\\criar_tabela_municipios.py."
        ) from erro

    total_registros = 0
    primeira_carga = True

    for pasta in encontrar_pastas_validas(BASE_DADOS):

        caminho_pasta = os.path.join(BASE_DADOS, pasta)

        arquivo_csv = selecionar_csv_unico(caminho_pasta, pasta)

        if arquivo_csv is None:
            continue

        tipo_cancer, origem = MAPA[pasta]

        print("\n" + "=" * 60)
        print("PASTA:", pasta)
        print("TIPO:", tipo_cancer)
        print("ORIGEM:", origem)

        separador = detectar_separador(arquivo_csv)

        df = pd.read_csv(
            arquivo_csv,
            sep=separador,
            encoding="latin1",
            low_memory=False
        )

        df, municipios, codigos = resolver_municipios(
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

    if total_registros == 0:
        raise RuntimeError(
            "A carga encontrou pastas reconhecidas, mas nenhuma continha "
            "um CSV -- confira se os arquivos foram mesmo colocados "
            "dentro das subpastas de dados\\ (uma por câncer x "
            "território), e não deixados soltos na raiz."
        )

    print("\n" + "=" * 60)
    print("CARGA TERRITORIAL FINALIZADA")
    print("TOTAL:", total_registros)
    print("=" * 60)


if __name__ == "__main__":
    carregar()
