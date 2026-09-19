import os

MUNICIPIO_PADRAO = "RIO_CLARO"
UF_REFERENCIA = "SP"


def obter_municipio():
    return os.getenv("ESCUDO_MUNICIPIO", MUNICIPIO_PADRAO).upper().strip()


def nome_coluna_municipio(df):
    municipio = obter_municipio()
    if municipio in df.columns:
        return municipio
    if MUNICIPIO_PADRAO in df.columns:
        return MUNICIPIO_PADRAO
    return None
