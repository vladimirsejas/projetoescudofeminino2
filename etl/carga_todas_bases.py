import os
import re
import sqlite3
import pandas as pd

BASE_DADOS = r"C:\projetoescudofeminino2\dados"
BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

# Só os arquivos ESTADUAIS entram no banco. Cada um traz as
# internações de todas as moradoras de SP, já com o município de
# residência (MUNIC_RES) -- inclusive as de Rio Claro. As pastas
# municipais antigas (ex.: cancer_mama_rio_claro) repetiam essas
# mesmas internações: carregar as duas contava Rio Claro em dobro
# (confirmado no banco real em 09/2026: 1.668 + as mesmas 1.668).
# Por isso elas não têm mais caminho na carga; se ainda estiverem em
# dados\, são ignoradas com aviso. Fonte única também deixa todas
# as cidades comparáveis entre si.
MAPA = {
    "cancer_mama_sp": ("MAMA", "SP"),
    "cancer_colorretal_sp": ("COLORRETAL", "SP"),
    "cancer_colo_utero_sp": ("COLO_UTERO", "SP"),
    "cancer_ovario_sp": ("OVARIO", "SP"),
    "cancer_pulmao_sp": ("PULMAO", "SP"),
    "cancer_tireoide_sp": ("TIREOIDE", "SP"),
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
    Lista as subpastas de `base_dados` que a carga reconhece (as
    chaves de MAPA). Falha alto se nenhuma bater -- por exemplo, se
    os CSVs foram deixados soltos direto em dados\\ em vez de dentro
    de dados\\cancer_mama_sp\\ etc. Sem essa checagem, esse
    engano não gera erro nenhum: o laço da carga simplesmente ignora
    todo mundo que não bate com MAPA e termina com TOTAL: 0, fácil de
    passar despercebido.
    """

    pastas = [
        entrada
        for entrada in sorted(os.listdir(base_dados))
        if entrada in MAPA
    ]

    if not pastas:
        raise RuntimeError(
            f"Nenhuma subpasta reconhecida foi encontrada em '{base_dados}'. "
            "A carga espera uma subpasta estadual por câncer (ex.: "
            "dados\\cancer_mama_sp\\, com um único CSV dentro dela) "
            "-- não arquivos soltos direto em dados\\. Pastas esperadas: "
            + ", ".join(sorted(MAPA))
        )

    return pastas


def pastas_ignoradas(base_dados):
    """
    Subpastas de dados\\ com cara de base (cancer_...) que a carga
    NÃO lê -- hoje, as municipais antigas (cancer_mama_rio_claro
    etc.). Só para avisar: elas podem ficar no computador como
    arquivo, mas não entram no banco.
    """

    return [
        entrada
        for entrada in sorted(os.listdir(base_dados))
        if entrada.startswith("cancer_") and entrada not in MAPA
        and os.path.isdir(os.path.join(base_dados, entrada))
    ]


def canceres_faltando(pastas):
    """Cânceres de MAPA sem pasta estadual em dados\\."""

    presentes = {MAPA[pasta][0] for pasta in pastas}
    return sorted({tipo for tipo, _ in MAPA.values()} - presentes)


def municipios_duplicados(conexao):
    """
    (Município, câncer) com internações vindas de mais de uma fonte
    (origem). Com só os arquivos estaduais a lista deve vir vazia;
    se não vier, esses totais estão contados em dobro. É por
    câncer: mama do estadual + ovário da pasta da cidade é normal.
    """

    return conexao.execute("""
        SELECT municipio, tipo_cancer, GROUP_CONCAT(DISTINCT origem)
        FROM internacoes
        GROUP BY municipio, tipo_cancer
        HAVING COUNT(DISTINCT origem) > 1
    """).fetchall()


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

    desconhecidos = municipios.isna()

    if desconhecidos.any():
        quantidade = int(desconhecidos.sum())
        exemplos = (
            codigos[desconhecidos]
            .dropna()
            .astype(str)
            .head(10)
            .tolist()
        )
        raise RuntimeError(
            f"{quantidade} registros de {origem} possuem código municipal "
            "sem correspondência no catálogo IBGE. Exemplos: {exemplos}"
        )

    return municipios, codigos


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

    pastas = encontrar_pastas_validas(BASE_DADOS)

    for pasta in pastas_ignoradas(BASE_DADOS):
        print(
            f"IGNORADA: {pasta} -- a carga usa só os arquivos estaduais "
            "(as internações dessa cidade já vêm neles, com o município "
            "de residência). Pode guardar a pasta fora de dados\\."
        )

    for tipo in canceres_faltando(pastas):
        print(f"ATENÇÃO: falta a pasta estadual de {tipo} "
              "(esse câncer fica fora do banco).")

    for pasta in pastas:

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

        municipios, codigos = resolver_municipios(
            df, origem, catalogo
        )

        dados = pd.DataFrame({
            "tipo_cancer": [tipo_cancer] * len(df),
            "origem": [origem] * len(df),
            "municipio": municipios,
            "codigo_ibge": codigos,
            "ano": df["ANO_CMPT"],
            # mês de competência: o Escudo precisa dele para saber quais
            # meses a fonte não oferece (inteligencia.ajustar_meses)
            "mes": pd.to_numeric(df["MES_CMPT"], errors="coerce") if "MES_CMPT" in df else None,
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

    duplicados = (
        municipios_duplicados(conexao) if total_registros else []
    )

    conexao.close()

    if duplicados:
        print("\nATENÇÃO: municípios com internações de mais de uma fonte "
              "(totais em dobro):", duplicados)

    if total_registros == 0:
        raise RuntimeError(
            "A carga encontrou pastas reconhecidas, mas nenhuma continha "
            "um CSV -- confira se os arquivos foram mesmo colocados "
            "dentro das subpastas de dados\\ (uma por câncer), e não "
            "deixados soltos na raiz."
        )

    print("\n" + "=" * 60)
    print("CARGA TERRITORIAL FINALIZADA")
    print("TOTAL:", total_registros)
    print("=" * 60)


if __name__ == "__main__":
    carregar()
