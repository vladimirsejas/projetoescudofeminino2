import os
import re
import sqlite3
import tempfile

# =====================================
# TESTE DA ARQUITETURA TERRITORIAL (código IBGE)
#
# Roda a cadeia determinística de verdade (mortalidade -> custos ->
# permanência -> faixa etária -> score -> tendência estadual ->
# anomalias -> priorizador -> base_conhecimento), mas contra um
# banco sqlite TEMPORÁRIO e sintético -- nunca contra o banco real
# nem inserindo cidades fictícias nele (regra do item 15 da tarefa:
# não baixar dados de outra cidade nesta etapa).
#
# LIMEIRA aqui é só um município de teste, usado exclusivamente
# dentro deste banco temporário, para provar que a arquitetura
# funciona para "qualquer município no banco" sem depender de dados
# reais de Limeira.
# =====================================

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

SCRIPTS_DA_CADEIA = [
    "mortalidade.py",
    "custos_hospitalares.py",
    "permanencia_hospitalar.py",
    "faixa_etaria.py",
    "score_epidemiologico.py",
    "tendencia_estadual.py",
    "anomalias.py",
    "priorizador.py",
    "base_conhecimento.py",
]


ANOS_HISTORICO = [2021, 2022, 2023, 2024, 2025]


def _linhas(cancer, origem, ano, total, obitos, dias=5, valor=1000.0):
    """
    `total` internações no ano, das quais `obitos` resultam em óbito.
    Controle explícito para os números do teste serem verificáveis
    à mão, em vez de depender de "todo o ano teve obito=X".
    """
    linhas = [(cancer, origem, ano, 55, dias, 1, valor)] * obitos
    linhas += [(cancer, origem, ano, 55, dias, 0, valor)] * (total - obitos)
    return linhas


def _montar_banco_sintetico(caminho, incluir_limeira):

    conexao = sqlite3.connect(caminho)

    conexao.execute("""
        CREATE TABLE internacoes (
            tipo_cancer TEXT, origem TEXT, ano INTEGER, idade INTEGER,
            dias_permanencia INTEGER, obito INTEGER, valor_total REAL
        )
    """)

    conexao.execute("""
        CREATE TABLE municipios (
            codigo_ibge INTEGER PRIMARY KEY,
            origem TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            uf TEXT NOT NULL
        )
    """)
    conexao.execute(
        "INSERT INTO municipios VALUES (3543907, 'RIO_CLARO', 'Rio Claro', 'SP')"
    )

    linhas = []

    # anomalias.py só analisa um câncer se ele tiver pelo menos 5 anos
    # de histórico -- por isso os 5 anos em ANOS_HISTORICO, não é
    # exigência da camada territorial, é uma regra já existente do
    # próprio script.
    for ano in ANOS_HISTORICO:

        # RIO_CLARO/MAMA: taxa de mortalidade real e alta (30%),
        # de propósito, para poder detectar se algum cálculo diluiu
        # esse número com o volume de SP (que é baixo, 0.1%).
        if ano == 2025:
            linhas += _linhas("MAMA", "RIO_CLARO", ano, total=10, obitos=3)
        else:
            linhas += _linhas("MAMA", "RIO_CLARO", ano, total=8, obitos=0)

        linhas += _linhas("PULMAO", "RIO_CLARO", ano, total=4, obitos=1)
        linhas += _linhas("COLORRETAL", "RIO_CLARO", ano, total=5, obitos=0)

        # SP: taxa de mortalidade de MAMA propositalmente baixa, para
        # o teste conseguir distinguir "taxa real de Rio Claro" de
        # "taxa contaminada pelo volume do Estado".
        if ano == 2025:
            linhas += _linhas("MAMA", "SP", ano, total=500, obitos=1)
        else:
            linhas += _linhas("MAMA", "SP", ano, total=500, obitos=0)

        linhas += _linhas("PULMAO", "SP", ano, total=200, obitos=40)
        linhas += _linhas("COLORRETAL", "SP", ano, total=250, obitos=20)

        if incluir_limeira:
            # LIMEIRA aqui é só para testar a arquitetura (item 12) --
            # sem óbitos nenhum, de propósito: se algum cálculo
            # vazar dados de Rio Claro para Limeira, a taxa deixa de
            # ser zero e o teste F) pega isso.
            linhas += _linhas("MAMA", "LIMEIRA", ano, total=6, obitos=0)
            linhas += _linhas("PULMAO", "LIMEIRA", ano, total=2, obitos=0)
            linhas += _linhas("COLORRETAL", "LIMEIRA", ano, total=3, obitos=0)

    conexao.executemany(
        "INSERT INTO internacoes VALUES (?,?,?,?,?,?,?)", linhas
    )
    conexao.commit()
    conexao.close()


def _rodar_script(nome_arquivo, caminho_banco, municipio_env):

    caminho_script = os.path.join(DIRETORIO_ATUAL, nome_arquivo)
    codigo_fonte = open(caminho_script, encoding="utf-8-sig").read()

    caminho_escapado = caminho_banco.replace("\\", "\\\\")
    codigo_fonte = codigo_fonte.replace(
        r'C:\projetoescudofeminino2\banco\escudo_feminino.db',
        caminho_escapado
    )

    os.environ["ESCUDO_MUNICIPIO"] = municipio_env

    namespace = {"__name__": f"__teste_{nome_arquivo}__"}
    exec(compile(codigo_fonte, nome_arquivo, "exec"), namespace)

    return namespace


def _rodar_cadeia(caminho_banco, municipio_env):

    ultimo_namespace = None

    for nome_arquivo in SCRIPTS_DA_CADEIA:
        ultimo_namespace = _rodar_script(
            nome_arquivo, caminho_banco, municipio_env
        )

    return ultimo_namespace


def testar():

    falhas = []
    total_checagens = [0]

    def checar(descricao, condicao):
        total_checagens[0] += 1
        status = "OK" if condicao else "FALHOU"
        print(f"[{status}] {descricao}")
        if not condicao:
            falhas.append(descricao)

    # -------------------------------------------------
    # A) Rio Claro continua funcionando exatamente como antes
    # G) nenhum cálculo mistura registros municipais com SP
    # -------------------------------------------------

    fd, banco_rc = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _montar_banco_sintetico(banco_rc, incluir_limeira=False)

    ns_rc = _rodar_cadeia(banco_rc, "RIO_CLARO")

    conexao = sqlite3.connect(banco_rc)
    mortalidade_tabela = dict(
        conexao.execute(
            "SELECT tipo_cancer, taxa_mortalidade FROM mortalidade"
        ).fetchall()
    )
    conexao.close()

    # Calculado a partir dos mesmos números usados em _montar_banco_sintetico:
    # RIO_CLARO/MAMA: 4 anos com 8 internações/0 óbitos + 2025 com 10
    # internações/3 óbitos = 42 internações, 3 óbitos.
    internacoes_rc = 8 * 4 + 10
    obitos_rc = 3
    taxa_esperada_isolada = obitos_rc / internacoes_rc * 100

    # Se o cálculo (ainda) misturasse com SP/MAMA (5 anos x 500
    # internações + 1 óbito em 2025), a taxa ficaria bem menor --
    # é exatamente o bug que já corrigimos antes nesta sessão.
    internacoes_sp = 500 * 5
    obitos_sp = 1
    taxa_se_misturado = (
        (obitos_rc + obitos_sp) / (internacoes_rc + internacoes_sp) * 100
    )

    taxa_mama = mortalidade_tabela.get("MAMA", -1)

    checar(
        f"A) Rio Claro: taxa de mortalidade de MAMA bate com o cálculo "
        f"isolado esperado ({taxa_esperada_isolada:.2f}%, obtido "
        f"{taxa_mama:.2f}%)",
        abs(taxa_mama - taxa_esperada_isolada) < 0.01
    )

    checar(
        f"G) taxa de MAMA claramente NÃO é a versão contaminada com SP "
        f"(contaminada seria {taxa_se_misturado:.2f}%, obtido "
        f"{taxa_mama:.2f}% -- confirma que origem=SP não vazou no "
        f"cálculo)",
        abs(taxa_mama - taxa_se_misturado) > 1.0
    )

    # -------------------------------------------------
    # B) SP continua sendo a referência estadual
    # -------------------------------------------------

    conexao = sqlite3.connect(banco_rc)
    colunas_tendencia = [
        linha[1] for linha in
        conexao.execute("PRAGMA table_info(tendencia_estadual)")
    ]
    conexao.close()

    checar(
        "B) tendencia_estadual mantém a coluna SP como referência "
        f"estadual (colunas: {colunas_tendencia})",
        "SP" in colunas_tendencia and "RIO_CLARO" in colunas_tendencia
    )

    os.remove(banco_rc)

    # -------------------------------------------------
    # C) Município inexistente não quebra o sistema
    # E) Código IBGE identifica corretamente o município
    # D) Lista de municípios vem do banco
    # -------------------------------------------------

    fd, banco_cfg = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _montar_banco_sintetico(banco_cfg, incluir_limeira=False)

    import configuracao_geografica as cg
    cg.BANCO = banco_cfg

    os.environ["ESCUDO_MUNICIPIO"] = "9999999"  # código IBGE inexistente
    try:
        municipio_resolvido = cg.obter_municipio()
        checar(
            "C) código IBGE inexistente não quebra o sistema "
            f"(caiu no padrão: {municipio_resolvido})",
            municipio_resolvido == "RIO_CLARO"
        )
    except Exception as erro:
        checar(f"C) município inexistente não quebra o sistema ({erro})", False)

    os.environ["ESCUDO_MUNICIPIO"] = "3543907"
    checar(
        "E) código IBGE 3543907 resolve corretamente para RIO_CLARO",
        cg.obter_municipio() == "RIO_CLARO"
    )

    os.environ.pop("ESCUDO_MUNICIPIO", None)
    disponiveis = cg.listar_municipios_disponiveis()
    checar(
        f"D) lista de municípios disponíveis vem do banco: {disponiveis}",
        len(disponiveis) == 1 and disponiveis[0]["origem"] == "RIO_CLARO"
    )

    os.remove(banco_cfg)

    # -------------------------------------------------
    # F) Indicadores respeitam o município selecionado
    # I) A execução completa da cadeia determinística continua
    #    funcionando (agora para um município sintético, não só
    #    Rio Claro)
    # -------------------------------------------------

    fd, banco_multi = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _montar_banco_sintetico(banco_multi, incluir_limeira=True)

    try:
        ns_limeira = _rodar_cadeia(banco_multi, "LIMEIRA")
        checar(
            "I) cadeia determinística completa roda sem erro para um "
            "município sintético diferente de Rio Claro (LIMEIRA)",
            True
        )
    except Exception as erro:
        checar(
            f"I) cadeia determinística falhou para LIMEIRA: {erro}", False
        )
        ns_limeira = None

    if ns_limeira is not None:
        conexao = sqlite3.connect(banco_multi)
        mortalidade_limeira = dict(
            conexao.execute(
                "SELECT tipo_cancer, taxa_mortalidade FROM mortalidade"
            ).fetchall()
        )
        conexao.close()

        # Nenhum óbito foi inserido para LIMEIRA -> taxa deve ser 0,
        # nunca contaminada pelos óbitos de Rio Claro
        checar(
            "F) mortalidade calculada para LIMEIRA não herda os óbitos "
            f"de Rio Claro (esperado 0.0%, obtido {mortalidade_limeira.get('MAMA')}%)",
            mortalidade_limeira.get("MAMA") == 0.0
        )

    os.remove(banco_multi)

    # -------------------------------------------------
    # H) O chat/motor de raciocínio recebe o município correto
    #    no contexto (sem depender do chat interativo completo)
    # -------------------------------------------------

    fd, banco_motor = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _montar_banco_sintetico(banco_motor, incluir_limeira=False)
    _rodar_cadeia(banco_motor, "RIO_CLARO")

    cg.BANCO = banco_motor
    os.environ.pop("ESCUDO_MUNICIPIO", None)

    import importlib
    import motor_raciocinio
    importlib.reload(motor_raciocinio)
    motor_raciocinio.BANCO = banco_motor

    contexto = motor_raciocinio.contexto_inteligente(
        "Qual a tendência estadual?", "TENDENCIA_ESTADUAL", None
    )
    checar(
        "H) contexto enviado à IA cita o município correto "
        f"(RIO_CLARO): {'RIO_CLARO' in contexto!r}",
        "RIO_CLARO" in contexto
    )

    os.remove(banco_motor)

    # -------------------------------------------------
    # RESULTADO FINAL
    # -------------------------------------------------

    print("\n=== RESULTADO ===\n")
    print(f"Total de checagens: {total_checagens[0]}")

    if falhas:
        print(f"\n{len(falhas)} checagem(ns) FALHOU(ARAM):\n")
        for descricao in falhas:
            print(f" - {descricao}")
    else:
        print("\nTodas as checagens passaram.")

    return len(falhas) == 0


if __name__ == "__main__":
    ok = testar()
    raise SystemExit(0 if ok else 1)
