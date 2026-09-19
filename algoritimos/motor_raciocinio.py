import sqlite3
import pandas as pd

from configuracao_geografica import obter_municipio, obter_nome_municipio

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"


def conectar():
    return sqlite3.connect(BANCO)


def _ler_tabela(nome):
    """
    Lê `nome` filtrando pelo município selecionado. `internacoes` é
    a única tabela crua (usa `origem`); todas as demais são tabelas
    derivadas multi-município (usam `municipio`).
    """
    conn = conectar()
    try:
        coluna_filtro = "origem" if nome == "internacoes" else "municipio"
        return pd.read_sql(
            f"SELECT * FROM {nome} WHERE {coluna_filtro} = ?",
            conn,
            params=(obter_municipio(),)
        )
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def buscar_cancer(nome_cancer):
    conn = conectar()
    df = pd.read_sql("""
        SELECT * FROM base_conhecimento
        WHERE UPPER(tipo_cancer) = UPPER(?) AND municipio = ?
    """, conn, params=[nome_cancer, obter_municipio()])
    conn.close()
    if df.empty:
        return None
    return df.iloc[0]


def buscar_memoria(nome_cancer):
    conn = conectar()
    try:
        df = pd.read_sql("""
            SELECT * FROM memoria_ia
            WHERE UPPER(tipo_cancer) = UPPER(?) AND municipio = ?
        """, conn, params=[nome_cancer, obter_municipio()])
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

    nome_municipio = obter_nome_municipio()

    contexto = f"""
SISTEMA: ESCUDO FEMININO
ESCOPO: PANORAMA GERAL DE {nome_municipio.upper()}

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
- Tendência estadual: comparação entre {nome_municipio} e São Paulo.
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



def contexto_inteligente(pergunta, intencao, cancer=None):
    """
    Seleciona o contexto já calculado de acordo com a intenção.
    Não recalcula indicadores; apenas escolhe os dados necessários
    para responder à pergunta.
    """
    base = contexto_geral_raciocinado()

    if intencao == "CANCER_ESPECIFICO" and cancer:
        return contexto_para_ia(cancer)

    tabelas = {
        "PRIORIDADE_MAXIMA": (
            "priorizacao_executiva",
            ["tipo_cancer", "nivel_prioridade", "pontuacao_final"],
            "PRIORIDADES"
        ),
        "APOIO_DECISAO": (
            "priorizacao_executiva",
            ["tipo_cancer", "nivel_prioridade", "pontuacao_final"],
            "APOIO À DECISÃO"
        ),
        "MUDANCA_TEMPORAL": (
            "tendencia_estadual",
            ["tipo_cancer", "variacao_municipio", "variacao_sp", "desvio", "evento"],
            "MUDANÇA TEMPORAL / TENDÊNCIA"
        ),
        "TOP_PRIORIDADES": (
            "priorizacao_executiva",
            ["tipo_cancer", "nivel_prioridade", "pontuacao_final"],
            "PRIORIDADES"
        ),
        "MORTALIDADE": (
            "mortalidade",
            ["tipo_cancer", "taxa_mortalidade"],
            "MORTALIDADE"
        ),
        "CUSTO": (
            "custos_hospitalares",
            ["tipo_cancer", "valor_total", "ranking_custo"],
            "CUSTOS HOSPITALARES"
        ),
        "PERMANENCIA": (
            "permanencia_hospitalar",
            ["tipo_cancer", "permanencia_media"],
            "PERMANÊNCIA HOSPITALAR"
        ),
        "FAIXA_ETARIA": (
            "faixa_etaria",
            ["tipo_cancer", "faixa_etaria", "internacoes"],
            "FAIXA ETÁRIA"
        ),
        "TENDENCIA_ESTADUAL": (
            "tendencia_estadual",
            ["tipo_cancer", "variacao_municipio", "variacao_sp", "desvio", "evento"],
            "TENDÊNCIA ESTADUAL"
        ),
        "ANOMALIAS": (
            "anomalias",
            ["tipo_cancer", "media_historica", "valor_2025",
             "desvio_percentual", "situacao"],
            "ANOMALIAS"
        ),
        "INCIDENCIA": (
            "internacoes",
            ["tipo_cancer"],
            "INCIDÊNCIA HOSPITALAR"
        ),
    }

    if intencao not in tabelas:
        return base

    nome_tabela, colunas, titulo = tabelas[intencao]
    df = _ler_tabela(nome_tabela)

    if df.empty:
        return base

    if intencao in ("TENDENCIA_ESTADUAL", "MUDANCA_TEMPORAL"):
        titulo = (
            f"{titulo} — MUNICÍPIO ANALISADO: "
            f"{obter_nome_municipio()}"
        )

    colunas_validas = [c for c in colunas if c in df.columns]
    if not colunas_validas:
        return base

    if intencao == "TENDENCIA_ESTADUAL" and "desvio" in df.columns:
        df = df.sort_values("desvio", ascending=False)
    elif intencao == "MORTALIDADE" and "taxa_mortalidade" in df.columns:
        df = df.sort_values("taxa_mortalidade", ascending=False)
    elif intencao == "CUSTO" and "valor_total" in df.columns:
        df = df.sort_values("valor_total", ascending=False)
    elif intencao == "PERMANENCIA" and "permanencia_media" in df.columns:
        df = df.sort_values("permanencia_media", ascending=False)
    elif intencao in ("PRIORIDADE_MAXIMA", "TOP_PRIORIDADES", "APOIO_DECISAO"):
        df = df.sort_values("pontuacao_final", ascending=False)
    elif intencao == "ANOMALIAS" and "situacao" in df.columns:
        df = df[df["situacao"] != "NORMAL"]
    elif intencao == "INCIDENCIA":
        df = (
            df.groupby("tipo_cancer")
            .size()
            .reset_index(name="total_internacoes")
            .sort_values("total_internacoes", ascending=False)
        )
        colunas_validas = ["tipo_cancer", "total_internacoes"]

    detalhe = df[colunas_validas].to_string(index=False)

    return (
        f"{base}\\n\\n"
        f"DADOS ESPECÍFICOS PARA A PERGUNTA:\\n"
        f"{titulo}\\n"
        f"{detalhe}\\n\\n"
        f"REGRA: estes dados já foram calculados pelo Escudo Feminino. "
        f"Use-os para responder à pergunta sem recalcular os indicadores."
    )


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
