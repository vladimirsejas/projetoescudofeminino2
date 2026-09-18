import sqlite3
import pandas as pd

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"


def conectar():
    return sqlite3.connect(BANCO)


def _ler_tabela(nome):
    conn = conectar()
    try:
        return pd.read_sql(f"SELECT * FROM {nome}", conn)
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def buscar_cancer(nome_cancer):
    conn = conectar()
    df = pd.read_sql("""
        SELECT * FROM base_conhecimento
        WHERE UPPER(tipo_cancer) = UPPER(?)
    """, conn, params=[nome_cancer])
    conn.close()
    if df.empty:
        return None
    return df.iloc[0]


def buscar_memoria(nome_cancer):
    conn = conectar()
    try:
        df = pd.read_sql("""
            SELECT * FROM memoria_ia
            WHERE UPPER(tipo_cancer) = UPPER(?)
        """, conn, params=[nome_cancer])
    except Exception:
        df = pd.DataFrame()
    conn.close()
    if df.empty:
        return None
    return df.iloc[0]


def raciocinar_cancer(nome_cancer):
    conhecimento = buscar_cancer(nome_cancer)
    if conhecimento is None:
        return None

    memoria = buscar_memoria(nome_cancer)
    resultado = {
        "tipo_cancer": conhecimento["tipo_cancer"],
        "nivel_prioridade": conhecimento["nivel_prioridade"],
        "pontuacao_final": conhecimento["pontuacao_final"],
        "o_que_aconteceu": (
            f"{conhecimento['tipo_cancer']} está classificado como prioridade "
            f"{conhecimento['nivel_prioridade']}, com pontuação final de "
            f"{conhecimento['pontuacao_final']:.2f}."
        ),
        "por_que_aconteceu": conhecimento["motivo"],
        "isso_e_importante": (
            f"O nível de prioridade é {conhecimento['nivel_prioridade'].lower()} "
            "em comparação com os demais cânceres monitorados."
        ),
        "impacto": conhecimento["impacto"],
        "o_que_deve_ser_feito": conhecimento["recomendacao"],
    }

    if memoria is not None:
        resultado["memoria"] = memoria["memoria"]
    return resultado


def contexto_para_ia(nome_cancer):
    resultado = raciocinar_cancer(nome_cancer)
    if resultado is None:
        return None

    contexto = f"""
SISTEMA: ESCUDO FEMININO

CÂNCER: {resultado['tipo_cancer']}

NÍVEL DE PRIORIDADE:
{resultado['nivel_prioridade']}

PONTUAÇÃO:
{resultado['pontuacao_final']:.2f}

O QUE ACONTECEU:
{resultado['o_que_aconteceu']}

POR QUE ACONTECEU:
{resultado['por_que_aconteceu']}

ISSO É IMPORTANTE:
{resultado['isso_e_importante']}

QUAL O IMPACTO:
{resultado['impacto']}

O QUE DEVE SER FEITO:
{resultado['o_que_deve_ser_feito']}
"""

    if resultado.get("memoria"):
        contexto += f"""

MEMÓRIA ESTRUTURADA DO ESCUDO:
{resultado['memoria']}
"""
    return contexto.strip()


def contexto_geral():
    """Cria um contexto compacto para o modelo de linguagem."""
    partes = []

    priorizacao = _ler_tabela("priorizacao_executiva")
    if not priorizacao.empty:
        colunas = [c for c in ["tipo_cancer", "nivel_prioridade", "pontuacao_final"] if c in priorizacao.columns]
        if colunas:
            top = priorizacao.sort_values("pontuacao_final", ascending=False).head(5)
            partes.append("TOP PRIORIDADES:\n" + top[colunas].to_string(index=False))

    tendencia = _ler_tabela("tendencia_estadual")
    if not tendencia.empty:
        colunas = [c for c in ["tipo_cancer", "RIO_CLARO", "SP", "desvio", "evento"] if c in tendencia.columns]
        if colunas:
            partes.append("TENDÊNCIA ESTADUAL:\n" + tendencia[colunas].to_string(index=False))

    anomalias = _ler_tabela("anomalias")
    if not anomalias.empty:
        if "situacao" in anomalias.columns:
            ativas = anomalias[anomalias["situacao"] != "NORMAL"]
        else:
            ativas = anomalias
        partes.append("ANOMALIAS:\n" + (ativas.to_string(index=False) if not ativas.empty else "Nenhuma anomalia ativa."))

    mortalidade = _ler_tabela("mortalidade")
    if not mortalidade.empty:
        if "taxa_mortalidade" in mortalidade.columns:
            mortalidade = mortalidade.sort_values("taxa_mortalidade", ascending=False)
        partes.append("MORTALIDADE:\n" + mortalidade.head(5).to_string(index=False))

    return "\n\n".join(partes)
