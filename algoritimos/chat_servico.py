import os
import re
import sqlite3
import unicodedata
from datetime import datetime

from motor_raciocinio import contexto_inteligente
from ia_linguagem import responder_com_ia

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).upper()


def listar_canceres():
    conn = sqlite3.connect(BANCO)
    try:
        df = __import__("pandas").read_sql(
            "SELECT DISTINCT tipo_cancer FROM internacoes WHERE tipo_cancer IS NOT NULL ORDER BY tipo_cancer",
            conn,
        )
        return df["tipo_cancer"].tolist()
    finally:
        conn.close()


def detectar_cancer(pergunta_norm, canceres):
    for cancer in canceres:
        nome = normalizar(cancer.replace("_", " "))
        if cancer in pergunta_norm or nome in pergunta_norm:
            return cancer
    return None


def classificar_intencao(pergunta_norm, canceres):
    if any(p in pergunta_norm for p in (
        "SIMULAR", "SIMULACAO", "E SE REDUZIRMOS", "SE REDUZIR", "SE DIMINUIR"
    )):
        return "SIMULACAO"

    if any(p in pergunta_norm for p in (
        "VULNERAVEL", "VULNERAVEIS", "VULNERABILIDADE",
        "GRUPO DE RISCO", "QUEM ESTA EM RISCO", "MAIS EM RISCO"
    )):
        return "VULNERABILIDADE"

    if detectar_cancer(pergunta_norm, canceres):
        return "CANCER_ESPECIFICO"

    if any(p in pergunta_norm for p in (
        "EVOLUCAO", "EVOLUIU", "EVOLUCAO TEMPORAL", "SERIE HISTORICA",
        "AO LONGO DOS ANOS", "NOS ULTIMOS ANOS"
    )):
        return "EVOLUCAO"

    if any(p in pergunta_norm for p in (
        "COMPARAR", "COMPARACAO", "COMPARANDO", "EM COMPARACAO",
        "OUTRO MUNICIPIO", "OUTRA CIDADE"
    )):
        return "COMPARACAO"

    if any(p in pergunta_norm for p in (
        "O QUE MUDOU", "MUDOU DESDE", "MUDANCAS DESDE",
        "COMPARAR COM O ANO PASSADO", "COMPARADOS AO ANO PASSADO",
        "COMPARADO AO ANO PASSADO", "COMPARACAO COM O ANO PASSADO",
        "EM RELACAO AO ANO PASSADO", "ANO ANTERIOR"
    )):
        return "MUDANCA_TEMPORAL"

    if any(p in pergunta_norm for p in (
        "COMO ESTA", "SITUACAO GERAL", "VISAO GERAL", "PANORAMA",
        "MELHORANDO", "PIORANDO"
    )):
        return "SITUACAO_GERAL"

    if any(p in pergunta_norm for p in (
        "ATENCAO", "PRIORIDADE", "PRIORITARIO", "RISCO", "GRAVE",
        "GRAVIDADE", "PREOCUPA", "PREOCUPANTE", "URGENTE", "URGENCIA",
        "SERIO", "INVESTIR", "RECURSOS", "ONDE AGIR", "O QUE FAZER",
        "ESCOLHER", "EXIGEM ACAO", "EXIGE ACAO"
    )):
        return "PRIORIDADE_MAXIMA"

    if any(p in pergunta_norm for p in ("TOP", "3 MAIORES", "TRES MAIORES", "RANKING")):
        return "TOP_PRIORIDADES"

    if any(p in pergunta_norm for p in (
        "MORTALIDADE", "OBITO", "MATA", "MORTE", "MORTAL", "LETAL", "LETALIDADE"
    )):
        return "MORTALIDADE"

    if any(p in pergunta_norm for p in (
        "CUSTO", "CUSTOS", "GASTO", "GASTOS", "FINANCEIRO",
        "ORCAMENTO", "DINHEIRO", "CARO"
    )):
        return "CUSTO"

    if any(p in pergunta_norm for p in (
        "PERMANENCIA", "LEITO", "LEITOS", "INTERNADO", "DIAS INTERNADO", "OCUPACAO"
    )):
        return "PERMANENCIA"

    if any(p in pergunta_norm for p in (
        "IDADE", "FAIXA", "ETARIA", "JOVEM", "IDOSA", "IDOSAS"
    )):
        return "FAIXA_ETARIA"

    if any(p in pergunta_norm for p in (
        "TENDENCIA", "ESTADUAL", "CRESCENDO", "CAINDO",
        "ACOMPANHA", "COMPARADO AO ESTADO", "COMPARADO A SP"
    )):
        return "TENDENCIA_ESTADUAL"

    if any(p in pergunta_norm for p in (
        "ANOMALIA", "ANOMALIAS", "PADRAO", "ALERTA", "ALERTAS",
        "FORA DO NORMAL", "ATIPICO", "ANORMA"
    )):
        return "ANOMALIAS"

    if any(p in pergunta_norm for p in (
        "INCIDENCIA", "INTERNACOES", "MAIS CASOS", "MAIS COMUM",
        "AFETAM MAIS", "AFETA MAIS"
    )):
        return "INCIDENCIA"

    if detectar_cancer(pergunta_norm, canceres):
        return "CANCER_ESPECIFICO"

    return "DESCONHECIDA"


def registrar_pergunta(pergunta, categoria, reconhecida):
    conn = sqlite3.connect(BANCO)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS perguntas_usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT,
                pergunta TEXT,
                categoria TEXT,
                reconhecida TEXT
            )
        """)
        for coluna in ("categoria", "reconhecida"):
            try:
                conn.execute(f"ALTER TABLE perguntas_usuarios ADD COLUMN {coluna} TEXT")
            except sqlite3.OperationalError:
                pass
        conn.execute(
            "INSERT INTO perguntas_usuarios (data_hora, pergunta, categoria, reconhecida) VALUES (?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pergunta, categoria, reconhecida),
        )
        conn.commit()
    finally:
        conn.close()


def responder_pergunta(pergunta, municipio, cancer_selecionado=None, ano_selecionado=None):
    canceres = listar_canceres()
    pergunta_norm = normalizar(pergunta)
    intencao = classificar_intencao(pergunta_norm, canceres)

    antigo = os.environ.get("ESCUDO_MUNICIPIO")
    os.environ["ESCUDO_MUNICIPIO"] = municipio

    try:
        cancer = detectar_cancer(pergunta_norm, canceres)

        if intencao == "DESCONHECIDA":
            resposta = (
                "Posso explorar os dados de várias formas. Você pode perguntar "
                "sobre internações, evolução, mortalidade, custos, permanência, "
                "faixa etária, tendência em relação a São Paulo, anomalias, "
                "priorização, vulnerabilidade, simulações ou pedir um relatório. "
                "Também pode combinar doença + indicador, por exemplo: "
                "'qual a mortalidade do câncer de mama?', "
                "'como evoluiu o câncer de mama?' ou "
                "'quanto foi gasto com câncer de mama?'"
            )
        else:
            if intencao == "CANCER_ESPECIFICO" and cancer is None:
                cancer = cancer_selecionado

            contexto = contexto_inteligente(pergunta, intencao, cancer, ano_selecionado)
            if not contexto:
                resposta = "Não encontrei dados suficientes no Escudo para responder a essa pergunta."
            else:
                try:
                    resposta = responder_com_ia(pergunta, contexto, "SIMPLES")
                except Exception:
                    resposta = (
                        "Encontrei a categoria da pergunta, mas a camada de linguagem "
                        "não está disponível neste momento. Os dados continuam disponíveis "
                        "nas áreas de exploração do painel."
                    )

        registrar_pergunta(pergunta, intencao, "SIM" if intencao != "DESCONHECIDA" else "NAO")
        return resposta, intencao
    finally:
        if antigo is None:
            os.environ.pop("ESCUDO_MUNICIPIO", None)
        else:
            os.environ["ESCUDO_MUNICIPIO"] = antigo
