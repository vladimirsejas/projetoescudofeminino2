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

def contexto_geral_raciocinado():
    """
    Organiza o panorama geral em camadas de raciocínio.
    Usa somente indicadores já calculados pelo Escudo.
    Não recalcula score, tendência ou anomalia.
    """
    priorizacao = _ler_tabela("priorizacao_executiva")
    tendencia = _ler_tabela("tendencia_estadual")
    anomalias = _ler_tabela("anomalias")
    mortalidade = _ler_tabela("mortalidade")

    if priorizacao.empty:
        return None

    top = priorizacao.sort_values(
        "pontuacao_final", ascending=False
    ).head(3)

    criticos_altos = priorizacao[
        priorizacao["nivel_prioridade"].isin(["CRITICA", "ALTA"])
    ]

    if "situacao" in anomalias.columns:
        anomalias_ativas = anomalias[
            anomalias["situacao"] != "NORMAL"
        ]
    else:
        anomalias_ativas = anomalias

    if "desvio" in tendencia.columns:
        acima_tendencia = tendencia[tendencia["desvio"] > 0]
    else:
        acima_tendencia = pd.DataFrame()

    linhas_top = []
    for _, row in top.iterrows():
        linhas_top.append(
            f"{row['tipo_cancer']} — {row['nivel_prioridade']} "
            f"(pontuação {row['pontuacao_final']:.2f})"
        )

    if not acima_tendencia.empty:
        tendencia_texto = (
            f"{len(acima_tendencia)} câncer(es) apresentam desvio "
            "positivo em relação à referência estadual."
        )
    else:
        tendencia_texto = (
            "Não há, no recorte disponível, cânceres com desvio "
            "positivo em relação à referência estadual."
        )

    if not mortalidade.empty and "taxa_mortalidade" in mortalidade.columns:
        mortalidade_top = mortalidade.sort_values(
            "taxa_mortalidade", ascending=False
        ).iloc[0]
        mortalidade_texto = (
            f"{mortalidade_top['tipo_cancer']} apresenta a maior "
            f"taxa de mortalidade entre os registros disponíveis "
            f"({mortalidade_top['taxa_mortalidade']:.2f}%)."
        )
    else:
        mortalidade_texto = "Indicador de mortalidade não disponível."

    contexto = f"""
SISTEMA: ESCUDO FEMININO
ESCOPO: PANORAMA GERAL DE RIO CLARO

O QUE FOI OBSERVADO:
- {len(criticos_altos)} de {len(priorizacao)} cânceres estão classificados
  como CRÍTICA ou ALTA prioridade.
- As três maiores prioridades atualmente são:
  {'; '.join(linhas_top)}.
- {len(anomalias_ativas)} câncer(es) apresentam situação diferente de NORMAL.
- {tendencia_texto}
- {mortalidade_texto}

EVIDÊNCIAS DISPONÍVEIS:
- Priorização executiva: classificação e pontuação final.
- Tendência estadual: comparação entre Rio Claro e São Paulo.
- Anomalias: identificação de desvios em relação ao histórico.
- Mortalidade: taxa de mortalidade por câncer.

POR QUE ISSO É IMPORTANTE:
A priorização permite identificar quais cânceres concentram maior
atenção segundo os indicadores já calculados pelo Escudo. Tendências
e anomalias ajudam a identificar mudanças de comportamento que merecem
investigação.

IMPACTO:
Os indicadores podem apoiar a definição de prioridades de monitoramento,
a discussão sobre uso de recursos e a identificação de situações que
merecem investigação adicional. Eles não demonstram, isoladamente, a
causa de um comportamento observado.

O QUE PODE SER FEITO:
Usar as prioridades, tendências e anomalias como ponto de partida para
investigação e planejamento das ações de saúde da mulher. A decisão
final cabe ao responsável pela gestão, considerando também informações
que não estão neste conjunto de dados.

LIMITAÇÕES:
Este panorama é descritivo. Associação, tendência ou anomalia não
constitui prova de causalidade. A resposta deve permanecer limitada
aos dados fornecidos pelo Escudo.
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
