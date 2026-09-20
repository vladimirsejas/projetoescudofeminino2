import os
import sqlite3
import tempfile

import teste_territorial as tt  # reaproveita _rodar_cadeia/_rodar_script já validados

# =====================================
# TESTE REAL: Santa Gertrudes x Taboão da Serra
#
# Pedido explícito do usuário: confirmar que o projeto lê dados de
# QUALQUER município de SP (não só Rio Claro/Limeira, que eram os
# únicos usados nos testes sintéticos anteriores) e que a comparação
# funciona para um par real e propositalmente assimétrico: uma
# cidade pequena (Santa Gertrudes, ~23 mil habitantes) e uma cidade
# grande da região metropolitana (Taboão da Serra, ~270 mil
# habitantes).
#
# Códigos IBGE confirmados via busca (fontes oficiais
# geoftp.ibge.gov.br / ibge.gov.br), não inventados:
#   Santa Gertrudes   = 3546702
#   Taboão da Serra   = 3552809
# =====================================

IBGE_SANTA_GERTRUDES = 3546702
IBGE_TABOAO_DA_SERRA = 3552809

ANOS = tt.ANOS_HISTORICO  # 5 anos: anomalias.py exige histórico mínimo


def montar_banco(caminho):
    conexao = sqlite3.connect(caminho)

    conexao.execute("""
        CREATE TABLE internacoes (
            tipo_cancer TEXT, origem TEXT, municipio TEXT, codigo_ibge INTEGER,
            ano INTEGER, idade INTEGER, dias_permanencia INTEGER,
            obito INTEGER, valor_total REAL
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
        "INSERT INTO municipios VALUES (?, 'SANTA_GERTRUDES', 'Santa Gertrudes', 'SP')",
        (IBGE_SANTA_GERTRUDES,)
    )
    conexao.execute(
        "INSERT INTO municipios VALUES (?, 'TABOAO_DA_SERRA', 'Taboão da Serra', 'SP')",
        (IBGE_TABOAO_DA_SERRA,)
    )

    linhas = []

    for ano in ANOS:
        # Santa Gertrudes: cidade pequena, volume baixo, taxa de
        # mortalidade de MAMA propositalmente ALTA (25%) em 2025 para
        # o teste conseguir distinguir "taxa isolada correta" de
        # "taxa diluída pelo volume de Taboão da Serra ou de SP".
        if ano == 2025:
            linhas += tt._linhas("MAMA", "SANTA_GERTRUDES", ano, total=8, obitos=2)
        else:
            linhas += tt._linhas("MAMA", "SANTA_GERTRUDES", ano, total=6, obitos=0)
        linhas += tt._linhas("PULMAO", "SANTA_GERTRUDES", ano, total=3, obitos=1)
        linhas += tt._linhas("COLORRETAL", "SANTA_GERTRUDES", ano, total=4, obitos=0)

        # Taboão da Serra: cidade grande, volume bem maior, taxa de
        # mortalidade de MAMA propositalmente BAIXA (2%) -- se algum
        # cálculo vazar entre municípios, essa taxa muda.
        if ano == 2025:
            linhas += tt._linhas("MAMA", "TABOAO_DA_SERRA", ano, total=100, obitos=2)
        else:
            linhas += tt._linhas("MAMA", "TABOAO_DA_SERRA", ano, total=90, obitos=0)
        linhas += tt._linhas("PULMAO", "TABOAO_DA_SERRA", ano, total=60, obitos=12)
        linhas += tt._linhas("COLORRETAL", "TABOAO_DA_SERRA", ano, total=70, obitos=5)

        # Referência estadual (SP) -- necessária para tendencia_estadual.py
        if ano == 2025:
            linhas += tt._linhas("MAMA", "SP", ano, total=500, obitos=1)
        else:
            linhas += tt._linhas("MAMA", "SP", ano, total=500, obitos=0)
        linhas += tt._linhas("PULMAO", "SP", ano, total=200, obitos=40)
        linhas += tt._linhas("COLORRETAL", "SP", ano, total=250, obitos=20)

    linhas_com_territorio = []
    for linha in linhas:
        cancer, origem, ano, idade, dias, obito, valor = linha
        if origem == "SANTA_GERTRUDES":
            municipio, codigo_ibge = "SANTA_GERTRUDES", IBGE_SANTA_GERTRUDES
        elif origem == "TABOAO_DA_SERRA":
            municipio, codigo_ibge = "TABOAO_DA_SERRA", IBGE_TABOAO_DA_SERRA
        else:
            municipio, codigo_ibge = "ESTADO_SP", None

        linhas_com_territorio.append(
            (cancer, origem, municipio, codigo_ibge, ano, idade, dias, obito, valor)
        )

    conexao.executemany(
        "INSERT INTO internacoes VALUES (?,?,?,?,?,?,?,?,?)",
        linhas_com_territorio
    )
    conexao.commit()
    conexao.close()


def testar():
    falhas = []

    def checar(descricao, condicao):
        status = "OK" if condicao else "FALHOU"
        print(f"[{status}] {descricao}")
        if not condicao:
            falhas.append(descricao)

    fd, banco = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    montar_banco(banco)

    # -------------------------------------------------
    # 1) listar_municipios_disponiveis() enxerga as duas cidades
    #    (prova que a lista vem do banco, não de nome hardcoded)
    # -------------------------------------------------
    import configuracao_geografica as cg
    cg.BANCO = banco

    disponiveis = cg.listar_municipios_disponiveis()
    origens_disponiveis = {m["origem"] for m in disponiveis}

    checar(
        f"1) Santa Gertrudes e Taboão da Serra aparecem em "
        f"listar_municipios_disponiveis(): {disponiveis}",
        {"SANTA_GERTRUDES", "TABOAO_DA_SERRA"} <= origens_disponiveis
    )

    # -------------------------------------------------
    # 2) código IBGE real resolve para o município correto
    # -------------------------------------------------
    os.environ["ESCUDO_MUNICIPIO"] = str(IBGE_SANTA_GERTRUDES)
    checar(
        f"2) código IBGE {IBGE_SANTA_GERTRUDES} resolve para SANTA_GERTRUDES",
        cg.obter_municipio() == "SANTA_GERTRUDES"
    )
    checar(
        "2b) nome de apresentação correto para Santa Gertrudes",
        cg.obter_nome_municipio() == "Santa Gertrudes"
    )

    os.environ["ESCUDO_MUNICIPIO"] = str(IBGE_TABOAO_DA_SERRA)
    checar(
        f"2) código IBGE {IBGE_TABOAO_DA_SERRA} resolve para TABOAO_DA_SERRA",
        cg.obter_municipio() == "TABOAO_DA_SERRA"
    )
    checar(
        "2b) nome de apresentação correto para Taboão da Serra",
        cg.obter_nome_municipio() == "Taboão da Serra"
    )

    # -------------------------------------------------
    # 3) comparação direta (a mesma query usada em dashboard/app.py,
    #    seção "Comparação direta entre municípios") isola cada
    #    cidade corretamente, sem misturar volumes
    # -------------------------------------------------
    conexao = sqlite3.connect(banco)
    comparacao = dict(conexao.execute(
        """
        SELECT municipio, COUNT(*) AS internacoes
        FROM internacoes
        WHERE municipio IN (?, ?)
        GROUP BY municipio
        """,
        ("SANTA_GERTRUDES", "TABOAO_DA_SERRA")
    ).fetchall())
    conexao.close()

    total_esperado_sg = 5 * (6 + 3 + 4) + (8 - 6) + 0  # 4 anos padrão + 2025 diferente p/ MAMA
    # cálculo direto e explícito em vez de fórmula genérica:
    total_esperado_sg = (6 * 4 + 8) + (3 * 5) + (4 * 5)
    total_esperado_tds = (90 * 4 + 100) + (60 * 5) + (70 * 5)

    checar(
        f"3) Comparação direta conta Santa Gertrudes corretamente "
        f"(esperado {total_esperado_sg}, obtido {comparacao.get('SANTA_GERTRUDES')})",
        comparacao.get("SANTA_GERTRUDES") == total_esperado_sg
    )
    checar(
        f"3) Comparação direta conta Taboão da Serra corretamente "
        f"(esperado {total_esperado_tds}, obtido {comparacao.get('TABOAO_DA_SERRA')})",
        comparacao.get("TABOAO_DA_SERRA") == total_esperado_tds
    )
    checar(
        "3) Volumes NÃO se misturam entre as duas cidades (uma é ~10x "
        "maior que a outra, exatamente como no mundo real)",
        comparacao.get("SANTA_GERTRUDES") != comparacao.get("TABOAO_DA_SERRA")
        and comparacao.get("TABOAO_DA_SERRA") > comparacao.get("SANTA_GERTRUDES")
    )

    # -------------------------------------------------
    # 4) cadeia determinística completa roda para as duas cidades no
    #    MESMO banco, e uma não contamina/apaga a outra (extensão do
    #    check J de teste_territorial.py para um par real)
    # -------------------------------------------------
    tt._rodar_cadeia(banco, "SANTA_GERTRUDES")

    def snapshot(tabela, municipio):
        conexao = sqlite3.connect(banco)
        try:
            return conexao.execute(
                f"SELECT * FROM {tabela} WHERE municipio = ? ORDER BY tipo_cancer",
                (municipio,)
            ).fetchall()
        finally:
            conexao.close()

    tabelas_finais = ["base_conhecimento", "priorizacao_executiva", "tendencia_estadual"]

    snapshot_sg_antes = {t: snapshot(t, "SANTA_GERTRUDES") for t in tabelas_finais}
    checar(
        "4) Santa Gertrudes gerou linhas nas 3 tabelas finais "
        f"({ {t: len(v) for t, v in snapshot_sg_antes.items()} })",
        all(len(v) > 0 for v in snapshot_sg_antes.values())
    )

    tt._rodar_cadeia(banco, "TABOAO_DA_SERRA")

    snapshot_sg_depois = {t: snapshot(t, "SANTA_GERTRUDES") for t in tabelas_finais}
    for tabela in tabelas_finais:
        checar(
            f"4) Processar Taboão da Serra NÃO alterou os dados de "
            f"Santa Gertrudes em `{tabela}`",
            snapshot_sg_depois[tabela] == snapshot_sg_antes[tabela]
        )

    for tabela in tabelas_finais:
        linhas_tds = snapshot(tabela, "TABOAO_DA_SERRA")
        checar(
            f"4) Taboão da Serra também existe em `{tabela}`, coexistindo "
            f"com Santa Gertrudes ({len(linhas_tds)} linha(s))",
            len(linhas_tds) > 0
        )

    # -------------------------------------------------
    # 5) mortalidade calculada isoladamente bate com o esperado (prova
    #    final de que não houve diluição cruzada entre as duas
    #    cidades nem com o Estado)
    # -------------------------------------------------
    conexao = sqlite3.connect(banco)
    mort_sg = dict(conexao.execute(
        "SELECT tipo_cancer, taxa_mortalidade FROM mortalidade WHERE municipio = 'SANTA_GERTRUDES'"
    ).fetchall())
    mort_tds = dict(conexao.execute(
        "SELECT tipo_cancer, taxa_mortalidade FROM mortalidade WHERE municipio = 'TABOAO_DA_SERRA'"
    ).fetchall())
    conexao.close()

    # taxa de mortalidade é por câncer (mortalidade.py agrupa por
    # tipo_cancer), então o denominador certo é só as internações de
    # MAMA -- não o total das 3 doenças somadas (esse era o erro
    # deste script de teste, não do projeto).
    internacoes_mama_sg = 6 * 4 + 8
    internacoes_mama_tds = 90 * 4 + 100
    taxa_esperada_sg = 2 / internacoes_mama_sg * 100
    taxa_esperada_tds = 2 / internacoes_mama_tds * 100

    checar(
        f"5) Taxa de mortalidade de MAMA em Santa Gertrudes bate com o "
        f"cálculo isolado (esperado {taxa_esperada_sg:.2f}%, obtido "
        f"{mort_sg.get('MAMA'):.2f}%)",
        abs(mort_sg.get("MAMA", -1) - taxa_esperada_sg) < 0.01
    )
    checar(
        f"5) Taxa de mortalidade de MAMA em Taboão da Serra bate com o "
        f"cálculo isolado (esperado {taxa_esperada_tds:.2f}%, obtido "
        f"{mort_tds.get('MAMA'):.2f}%)",
        abs(mort_tds.get("MAMA", -1) - taxa_esperada_tds) < 0.01
    )
    checar(
        "5) As duas taxas são claramente diferentes entre si (prova de "
        "que uma cidade não herdou a taxa da outra nem do Estado)",
        abs(mort_sg.get("MAMA", 0) - mort_tds.get("MAMA", -999)) > 1.0
    )

    os.remove(banco)

    print("\n=== RESULTADO ===\n")
    if falhas:
        print(f"{len(falhas)} checagem(ns) FALHOU(ARAM):\n")
        for descricao in falhas:
            print(f" - {descricao}")
    else:
        print("Todas as checagens passaram.")

    return len(falhas) == 0


if __name__ == "__main__":
    ok = testar()
    raise SystemExit(0 if ok else 1)
