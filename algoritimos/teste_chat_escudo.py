import io
import os
import sqlite3
import sys
import tempfile
from contextlib import redirect_stdout

# =====================================
# TESTE DO MOTOR DE PERGUNTAS (chat_escudo.py)
#
# "Janela de Fechamento das Perguntas": audita a cadeia completa
# categoria reconhecida -> consulta/contexto correto -> dado correto
# -> resposta correta -> linguagem adequada, no caminho determinístico
# puro (ESCUDO_IA_ATIVA=NAO, sem depender de chave de API).
#
# Roda chat_escudo.py de verdade (via exec, como os outros testes do
# projeto) contra um banco sqlite temporário com 3 cânceres
# (MAMA, PULMAO, OVARIO) montados de propósito para que o câncer "de
# maior destaque" em cada indicador NUNCA seja o mesmo -- assim, um
# teste que pede o indicador de um câncer específico só passa se o
# filtro por câncer realmente funcionar, não por coincidência de já
# ser o maior valor geral.
#
# Cobre dois achados da revisão cruzada (Claude + ChatGPT):
#   1. classificar_intencao() checava nome de câncer antes de
#      indicadores específicos -- "mortalidade do câncer de mama"
#      virava CANCER_ESPECIFICO em vez de MORTALIDADE.
#   2. MUDANCA_TEMPORAL e APOIO_DECISAO eram reconhecidos pelo
#      classificador mas não tinham nenhuma resposta em responder() --
#      caíam no "Ainda não compreendi", mesmo registrando no banco
#      como reconhecida = SIM.
# E cobre a nova capacidade da camada preditiva (PREVISAO).
# =====================================

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ORIGINAL = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

sys.path.insert(0, DIRETORIO_ATUAL)


def _montar_banco(caminho):

    conexao = sqlite3.connect(caminho)

    conexao.executescript("""
        CREATE TABLE internacoes (
            tipo_cancer TEXT, origem TEXT, municipio TEXT,
            codigo_ibge INTEGER, ano INTEGER, idade INTEGER,
            dias_permanencia INTEGER, obito INTEGER, valor_total REAL
        );

        CREATE TABLE mortalidade (
            tipo_cancer TEXT, taxa_mortalidade REAL, municipio TEXT
        );

        CREATE TABLE custos_hospitalares (
            tipo_cancer TEXT, valor_total REAL, municipio TEXT
        );

        CREATE TABLE permanencia_hospitalar (
            tipo_cancer TEXT, permanencia_media REAL, municipio TEXT
        );

        CREATE TABLE faixa_etaria (
            tipo_cancer TEXT, faixa_etaria TEXT, internacoes INTEGER,
            municipio TEXT
        );

        CREATE TABLE tendencia_estadual (
            tipo_cancer TEXT, variacao_municipio REAL, variacao_sp REAL,
            desvio REAL, evento TEXT, confiabilidade TEXT, municipio TEXT
        );

        CREATE TABLE anomalias (
            tipo_cancer TEXT, situacao TEXT, municipio TEXT
        );

        CREATE TABLE priorizacao_executiva (
            tipo_cancer TEXT, nivel_prioridade TEXT,
            pontuacao_final REAL, municipio TEXT
        );

        CREATE TABLE base_conhecimento (
            tipo_cancer TEXT, nivel_prioridade TEXT, pontuacao_final REAL,
            motivo TEXT, impacto TEXT, recomendacao TEXT, evento TEXT,
            situacao TEXT, confiabilidade TEXT,
            confiabilidade_anomalia TEXT, municipio TEXT
        );

        CREATE TABLE memoria_ia (
            tipo_cancer TEXT, memoria TEXT, municipio TEXT
        );

        CREATE TABLE vulnerabilidade (
            tipo_cancer TEXT, faixa_mais_vulneravel TEXT,
            taxa_mortalidade_faixa REAL, obitos_faixa INTEGER,
            internacoes_faixa INTEGER, confiabilidade TEXT, municipio TEXT
        );

        CREATE TABLE previsao_temporal (
            tipo_cancer TEXT, anos_historico INTEGER, ano_previsto INTEGER,
            internacoes_previstas REAL, erro_validacao_pct REAL,
            erro_baseline_pct REAL, supera_baseline INTEGER,
            dobras_validacao INTEGER, confiabilidade TEXT, municipio TEXT
        );
    """)

    M = "RIO_CLARO"

    # mortalidade: PULMAO é o maior geral -- MAMA precisa vir com o
    # próprio número (10.0%), não o 25.0% de PULMAO, quando perguntado
    # especificamente por ela
    conexao.executemany(
        "INSERT INTO mortalidade VALUES (?,?,?)",
        [("MAMA", 10.0, M), ("PULMAO", 25.0, M), ("OVARIO", 15.0, M)]
    )

    # custo: MAMA é o maior geral -- OVARIO precisa vir com o próprio
    # número (30000), não o 50000 de MAMA
    conexao.executemany(
        "INSERT INTO custos_hospitalares VALUES (?,?,?)",
        [("MAMA", 50000.0, M), ("PULMAO", 20000.0, M), ("OVARIO", 30000.0, M)]
    )

    # permanência: PULMAO é o maior geral -- MAMA precisa vir com o
    # próprio número (5.0 dias), não o 8.0 de PULMAO
    conexao.executemany(
        "INSERT INTO permanencia_hospitalar VALUES (?,?,?)",
        [("MAMA", 5.0, M), ("PULMAO", 8.0, M), ("OVARIO", 6.0, M)]
    )

    conexao.executemany(
        "INSERT INTO faixa_etaria VALUES (?,?,?,?)",
        [
            ("MAMA", "60-79", 20, M), ("PULMAO", "60-79", 15, M),
            ("OVARIO", "40-59", 10, M)
        ]
    )

    # tendência: PULMAO tem o maior desvio absoluto -- MAMA precisa
    # vir com o próprio desvio (5.0%), não o 20.0% de PULMAO
    conexao.executemany(
        "INSERT INTO tendencia_estadual VALUES (?,?,?,?,?,?,?)",
        [
            ("MAMA", 5.0, 3.0, 5.0, "ACIMA_DA_TENDENCIA_ESTADUAL", "OK", M),
            ("PULMAO", 20.0, 2.0, 20.0, "ACIMA_DA_TENDENCIA_ESTADUAL", "OK", M),
            ("OVARIO", -15.0, 1.0, -15.0, "ABAIXO_DA_TENDENCIA_ESTADUAL", "OK", M),
        ]
    )

    conexao.executemany(
        "INSERT INTO anomalias VALUES (?,?,?)",
        [("MAMA", "NORMAL", M), ("PULMAO", "ANOMALIA_POSITIVA", M),
         ("OVARIO", "NORMAL", M)]
    )

    # priorização: MAMA é a maior -- usada por SITUACAO_GERAL,
    # PRIORIDADE_MAXIMA, TOP_PRIORIDADES, APOIO_DECISAO
    conexao.executemany(
        "INSERT INTO priorizacao_executiva VALUES (?,?,?,?)",
        [("MAMA", "CRITICA", 9.5, M), ("PULMAO", "ALTA", 7.0, M),
         ("OVARIO", "MEDIA", 4.0, M)]
    )

    conexao.executemany(
        "INSERT INTO base_conhecimento VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("MAMA", "CRITICA", 9.5, "motivo mama", "impacto mama",
             "recomendacao mama", "ACIMA_DA_TENDENCIA_ESTADUAL",
             "NORMAL", "OK", "OK", M),
            ("PULMAO", "ALTA", 7.0, "motivo pulmao", "impacto pulmao",
             "recomendacao pulmao", "ACIMA_DA_TENDENCIA_ESTADUAL",
             "ANOMALIA_POSITIVA", "OK", "OK", M),
            ("OVARIO", "MEDIA", 4.0, "motivo ovario", "impacto ovario",
             "recomendacao ovario", "ABAIXO_DA_TENDENCIA_ESTADUAL",
             "NORMAL", "OK", "OK", M),
        ]
    )

    conexao.executemany(
        "INSERT INTO memoria_ia VALUES (?,?,?)",
        [
            ("MAMA", "MEMORIA_TEXTO_MAMA", M),
            ("PULMAO", "MEMORIA_TEXTO_PULMAO", M),
            ("OVARIO", "MEMORIA_TEXTO_OVARIO", M),
        ]
    )

    conexao.execute(
        "INSERT INTO vulnerabilidade VALUES (?,?,?,?,?,?,?)",
        ("MAMA", "60-79", 20.0, 2, 10, "OK", M)
    )

    # previsão: MAMA e PULMAO superam o baseline (ganho real),
    # OVARIO não supera -- é o caso "SEM_GANHO_PREDITIVO" citado na
    # revisão cruzada. MAMA tem a maior previsão (100), usada no
    # teste de "qual câncer tem maior previsão".
    conexao.executemany(
        "INSERT INTO previsao_temporal VALUES "
        "(?,?,?,?,?,?,?,?,?,?)",
        [
            ("MAMA", 13, 2026, 100.0, 15.0, 25.0, 1, 4, "OK", M),
            ("PULMAO", 13, 2026, 40.0, 20.0, 30.0, 1, 4, "OK", M),
            (
                "OVARIO", 13, 2026, 20.0, 50.0, 25.0, 0, 4,
                "SEM_GANHO_PREDITIVO (regressão errou 50.0% em média, "
                "baseline simples errou 25.0% -- usando o baseline "
                "como previsão)", M
            ),
        ]
    )

    # internações 2025: MAMA tem mais linhas que PULMAO e OVARIO --
    # usada por INCIDENCIA (maior volume geral) e por SIMULACAO
    # (filtra por câncer + ano = 2025)
    linhas_internacoes = (
        [("MAMA", "RIO_CLARO", M, 3543907, 2025, 55, 5, 1, 1000.0)] * 3
        + [("MAMA", "RIO_CLARO", M, 3543907, 2025, 60, 5, 0, 1000.0)] * 2
        + [("PULMAO", "RIO_CLARO", M, 3543907, 2025, 65, 6, 1, 2000.0)] * 3
        + [("OVARIO", "RIO_CLARO", M, 3543907, 2025, 50, 4, 0, 1500.0)] * 2
    )
    conexao.executemany(
        "INSERT INTO internacoes VALUES (?,?,?,?,?,?,?,?,?)",
        linhas_internacoes
    )

    conexao.commit()
    conexao.close()


def _rodar_chat(caminho_banco, respostas):
    """
    Executa chat_escudo.py de verdade (exec), alimentando `respostas`
    como se fossem digitadas no input() -- a primeira é o perfil
    (1 = técnico), as seguintes são as perguntas, a última deve ser
    "sair". Cada resposta consumida marca o início do trecho de saída
    que ela gerou, imprimindo "@@Q@@<valor>" antes de devolvê-la --
    isso permite depois separar a transcrição em blocos por pergunta.
    """

    fila = iter(respostas)

    def input_stub(prompt=""):
        valor = next(fila)
        print(f"@@Q@@{valor}")
        return valor

    caminho_script = os.path.join(DIRETORIO_ATUAL, "chat_escudo.py")
    codigo_fonte = open(caminho_script, encoding="utf-8-sig").read()
    codigo_fonte = codigo_fonte.replace(
        CAMINHO_ORIGINAL, caminho_banco.replace("\\", "\\\\")
    )

    os.environ["ESCUDO_MUNICIPIO"] = "RIO_CLARO"
    os.environ["ESCUDO_IA_ATIVA"] = "NAO"

    if "configuracao_geografica" in sys.modules:
        sys.modules["configuracao_geografica"].BANCO = caminho_banco

    saida = io.StringIO()

    builtins_input_original = __builtins__["input"] if isinstance(
        __builtins__, dict
    ) else __builtins__.input

    import builtins
    builtins.input = input_stub

    try:
        with redirect_stdout(saida):
            exec(
                compile(codigo_fonte, "chat_escudo.py", "exec"),
                {"__name__": "__teste_chat_escudo__"}
            )
    finally:
        builtins.input = builtins_input_original

    return saida.getvalue()


def _blocos_por_pergunta(transcricao):
    """
    Separa a transcrição em blocos por marcador "@@Q@@". O bloco 0 é
    o cabeçalho (antes da primeira pergunta de perfil); os seguintes
    correspondem, em ordem, a cada valor de `respostas` consumido.
    """
    return transcricao.split("@@Q@@")[1:]


def testar():

    falhas = []

    def checar(descricao, condicao):
        status = "OK" if condicao else "FALHOU"
        print(f"[{status}] {descricao}")
        if not condicao:
            falhas.append(descricao)

    fd, banco = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    perguntas = [
        "mortalidade do cancer de mama",
        "qual o custo do cancer de ovario",
        "permanencia do cancer de mama",
        "tendencia do cancer de mama",
        "anomalia no cancer de mama",
        "quais anomalias existem",
        "o que mudou desde o ano passado",
        "onde devemos investir",
        "previsao do cancer de mama",
        "por que o sistema nao usou a tendencia para ovario",
        "qual cancer apresenta maior previsao para 2026",
        "quais previsoes apresentaram ganho em relacao ao metodo simples",
        "MAMA",
        "situacao geral",
        "top 3 prioridades",
        "incidencia",
        "relatorio executivo",
        "grupos vulneraveis",
        "simular reducao de 20% na mama",
        "pergunta sem nenhum sentido xyzxyz",
    ]

    try:
        _montar_banco(banco)
        transcricao = _rodar_chat(banco, ["1"] + perguntas + ["sair"])
    finally:
        os.remove(banco)

    blocos = _blocos_por_pergunta(transcricao)

    # bloco 0 = perfil ("1"); blocos 1..N = perguntas, na mesma ordem
    respostas = {
        pergunta: blocos[i + 1] for i, pergunta in enumerate(perguntas)
    }

    # --- achado 1: câncer específico + indicador não vira mais
    # CANCER_ESPECIFICO, e o indicador usa o câncer certo, não o
    # maior geral ---

    checar(
        "mortalidade do câncer de mama -> responde 10.00% (MAMA), "
        "não 25.00% (PULMAO, que é o maior geral)",
        "10.00%" in respostas["mortalidade do cancer de mama"]
        and "25.00%" not in respostas["mortalidade do cancer de mama"]
    )

    checar(
        "custo do câncer de ovário -> responde 30.000 (OVARIO), não "
        "50.000 (MAMA, que é o maior geral)",
        "30,000.00" in respostas["qual o custo do cancer de ovario"]
        and "50,000.00" not in respostas["qual o custo do cancer de ovario"]
    )

    checar(
        "permanência do câncer de mama -> responde 5.00 dias (MAMA), "
        "não 8.00 (PULMAO, que é o maior geral)",
        "5.00 dias" in respostas["permanencia do cancer de mama"]
        and "8.00 dias" not in respostas["permanencia do cancer de mama"]
    )

    checar(
        "tendência do câncer de mama -> responde 5.00% (MAMA), não "
        "20.00% (PULMAO, que é o maior desvio geral)",
        "5.00%" in respostas["tendencia do cancer de mama"]
        and "20.00%" not in respostas["tendencia do cancer de mama"]
    )

    checar(
        "anomalia do câncer de mama -> diz explicitamente que MAMA "
        "não tem anomalia (não lista a de PULMAO por engano)",
        "MAMA não apresenta anomalia" in respostas["anomalia no cancer de mama"]
    )

    checar(
        "'quais anomalias existem' (genérico) -> lista só PULMAO, "
        "que é o único fora de NORMAL",
        "PULMAO" in respostas["quais anomalias existem"]
        and "OVARIO -" not in respostas["quais anomalias existem"]
        and "MAMA -" not in respostas["quais anomalias existem"]
    )

    # --- achado 2: MUDANCA_TEMPORAL e APOIO_DECISAO agora respondem
    # de verdade, em vez de cair no "não compreendi" ---

    resp_mudanca = respostas["o que mudou desde o ano passado"]
    checar(
        "'o que mudou desde o ano passado' -> responde de verdade, "
        "não cai mais no 'Ainda não compreendi' (MUDANCA_TEMPORAL "
        "não tinha handler nenhum antes desta correção)",
        "Ainda não compreendi" not in resp_mudanca
        and "PULMAO" in resp_mudanca
    )
    checar(
        "'o que mudou' -> ordena por magnitude da mudança "
        "(PULMAO 20% antes de OVARIO 15%, antes de MAMA 5%)",
        resp_mudanca.find("PULMAO") < resp_mudanca.find("OVARIO")
        < resp_mudanca.find("MAMA")
    )

    resp_apoio = respostas["onde devemos investir"]
    checar(
        "'onde devemos investir' -> responde de verdade (APOIO_DECISAO "
        "não tinha handler nenhum antes desta correção), aponta MAMA "
        "(maior pontuação) e traz a memória associada",
        "Ainda não compreendi" not in resp_apoio
        and "MAMA" in resp_apoio
        and "MEMORIA_TEXTO_MAMA" in resp_apoio
    )

    # --- nova capacidade: PREVISAO ---

    resp_prev_mama = respostas["previsao do cancer de mama"]
    checar(
        "previsão do câncer de mama -> mostra o número (100) e "
        "diferencia internação SUS de caso novo de câncer",
        "100" in resp_prev_mama
        and "internações registradas no SUS" in resp_prev_mama
        and "não previsão de novos casos" in resp_prev_mama
    )

    resp_prev_ovario = respostas[
        "por que o sistema nao usou a tendencia para ovario"
    ]
    checar(
        "'por que o sistema não usou a tendência para ovário' -> cai "
        "em PREVISAO (não em TENDENCIA_ESTADUAL, apesar de conter a "
        "palavra 'tendencia'), e explica o SEM_GANHO_PREDITIVO",
        "SEM_GANHO_PREDITIVO" not in resp_prev_ovario
        # a palavra-chave completa não aparece no texto de resposta,
        # mas a explicação em linguagem natural do fallback aparece:
        or "não demonstrou ganho real sobre o baseline" in resp_prev_ovario
    )
    checar(
        "resposta sobre ovário cita o valor usado como previsão "
        "(baseline, 20 internações) -- não a extrapolação da reta",
        "20 internações" in resp_prev_ovario
    )

    resp_prev_maior = respostas["qual cancer apresenta maior previsao para 2026"]
    checar(
        "'qual câncer tem maior previsão' -> aponta MAMA (100), a "
        "maior entre as três",
        "MAMA" in resp_prev_maior and "100" in resp_prev_maior
    )

    resp_prev_ganho = respostas[
        "quais previsoes apresentaram ganho em relacao ao metodo simples"
    ]
    checar(
        "'quais previsões tiveram ganho' -> lista MAMA e PULMAO "
        "(supera_baseline), não lista OVARIO (não superou)",
        "MAMA" in resp_prev_ganho and "PULMAO" in resp_prev_ganho
        and "OVARIO" not in resp_prev_ganho
    )

    # --- regressão: intenções que já existiam continuam funcionando
    # depois da reordenação de classificar_intencao() ---

    checar(
        "'MAMA' sozinho continua caindo em CANCER_ESPECIFICO "
        "(memória técnica do câncer)",
        "MEMORIA_TEXTO_MAMA" in respostas["MAMA"]
    )
    checar(
        "'situação geral' continua funcionando (panorama)",
        "Panorama geral" in respostas["situacao geral"]
    )
    checar(
        "'top 3 prioridades' continua funcionando",
        "TOP 3 PRIORIDADES" in respostas["top 3 prioridades"]
    )
    checar(
        "'incidência' continua apontando o câncer de maior volume "
        "(MAMA, 5 internações em 2025)",
        "MAMA" in respostas["incidencia"]
    )
    checar(
        "'relatório executivo' continua reconhecido (arquivo pode "
        "não existir no diretório de teste, mas a intenção responde)",
        "Ainda não compreendi" not in respostas["relatorio executivo"]
    )
    checar(
        "'grupos vulneráveis' continua funcionando",
        "60-79" in respostas["grupos vulneraveis"]
        and "vulnerável identificado" in respostas["grupos vulneraveis"]
    )
    checar(
        "'simular redução de 20% na mama' continua funcionando",
        "Simulação: MAMA" in respostas["simular reducao de 20% na mama"]
    )
    checar(
        "pergunta sem sentido nenhum ainda cai no fallback "
        "'Ainda não compreendi'",
        "Ainda não compreendi"
        in respostas["pergunta sem nenhum sentido xyzxyz"]
    )

    if falhas:
        raise SystemExit(f"{len(falhas)} checagem(ns) falharam: {falhas}")

    print("\nTodas as checagens do motor de perguntas passaram.")


if __name__ == "__main__":
    testar()
