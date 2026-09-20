import sqlite3
import unicodedata
import re
import pandas as pd
from datetime import datetime
import os

from motor_raciocinio import raciocinar_cancer, contexto_para_ia, contexto_geral_raciocinado, contexto_inteligente
from ia_linguagem import responder_com_ia
from configuracao_geografica import (
    obter_municipio,
    obter_nome_municipio,
    ler_tabela_municipio
)

# =====================================
# CONEXÃO
# =====================================

BANCO = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

conn = sqlite3.connect(BANCO)

# =====================================
# VERIFICAÇÃO DE PRÉ-REQUISITOS
#
# Evita erro confuso no meio do chat: se uma
# tabela que o motor precisa ainda não existe,
# avisa exatamente qual algoritmo rodar antes.
# =====================================

TABELAS_NECESSARIAS = [
    "priorizacao_executiva",
    "tendencia_estadual",
    "anomalias",
    "mortalidade",
    "custos_hospitalares",
    "permanencia_hospitalar",
    "faixa_etaria",
    "base_conhecimento",
    "memoria_ia",
    "internacoes",
]

tabelas_existentes = set(
    row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
)

faltando = [t for t in TABELAS_NECESSARIAS if t not in tabelas_existentes]

if faltando:

    print("\nERRO: as seguintes tabelas ainda não existem no banco:\n")

    for tabela in faltando:
        print(f"  - {tabela}")

    print(
        "\nRode os algoritmos correspondentes (ver seção 4/5 do "
        "relatório de referência) antes de usar este chat."
    )

    conn.close()
    raise SystemExit(1)

# =====================================
# TABELA DE APRENDIZADO DE PERGUNTAS
# (Missão técnica nº 9)
# =====================================

conn.execute("""
CREATE TABLE IF NOT EXISTS perguntas_usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT,
    pergunta TEXT,
    categoria TEXT,
    reconhecida TEXT
)
""")

# se a tabela já existia na versão antiga (só data_hora/pergunta),
# adiciona as colunas novas sem apagar o histórico já registrado
for coluna in ("categoria", "reconhecida"):
    try:
        conn.execute(
            f"ALTER TABLE perguntas_usuarios ADD COLUMN {coluna} TEXT"
        )
    except sqlite3.OperationalError:
        pass  # coluna já existe

conn.commit()

# =====================================
# CARGA DO CONHECIMENTO
# (só leitura — nada é recalculado aqui)
# =====================================

MUNICIPIO = obter_municipio()
NOME_MUNICIPIO = obter_nome_municipio()

# Todas essas tabelas agora são multi-município -- ler sem filtrar
# misturaria o município selecionado com qualquer outro já
# processado (o mesmo problema já corrigido na cadeia determinística,
# só que aqui na camada de leitura do chat).
priorizacao = ler_tabela_municipio(
    "priorizacao_executiva", conn, municipio=MUNICIPIO
)
tendencia = ler_tabela_municipio("tendencia_estadual", conn, municipio=MUNICIPIO)
anomalias_df = ler_tabela_municipio("anomalias", conn, municipio=MUNICIPIO)
mortalidade_df = ler_tabela_municipio("mortalidade", conn, municipio=MUNICIPIO)
custos_df = ler_tabela_municipio("custos_hospitalares", conn, municipio=MUNICIPIO)
permanencia_df = ler_tabela_municipio(
    "permanencia_hospitalar", conn, municipio=MUNICIPIO
)
faixa_df = ler_tabela_municipio("faixa_etaria", conn, municipio=MUNICIPIO)
base_df = ler_tabela_municipio("base_conhecimento", conn, municipio=MUNICIPIO)
memoria = ler_tabela_municipio("memoria_ia", conn, municipio=MUNICIPIO)

# vulnerabilidade é opcional — se ainda não foi gerada
# (algoritimos\vulnerabilidade.py) ou não existe para o município
# selecionado, o chat continua funcionando normalmente, só essa
# categoria de pergunta fica indisponível
vulnerabilidade_df = ler_tabela_municipio(
    "vulnerabilidade", conn, municipio=MUNICIPIO
)
if vulnerabilidade_df.empty:
    vulnerabilidade_df = None

canceres = priorizacao["tipo_cancer"].tolist()


# =====================================
# ADAPTAÇÃO POR PÚBLICO (Missão técnica nº 7)
#
# Mesmos fatos, dois níveis de linguagem.
# Técnico: para secretário, prefeito, gestor hospitalar,
# pesquisador — todos acostumados a números e termos técnicos.
# Simples: para população em geral — sem jargão, sem
# pontuação, foco em conclusão e ação.
# =====================================

RECOMENDACAO_SIMPLES = {
    "CRITICA": "priorizar esse câncer nas ações de saúde imediatamente.",
    "ALTA": "acompanhar de perto e incluir entre as prioridades de curto prazo.",
    "MEDIA": "manter monitoramento regular, sem urgência no momento.",
    "BAIXA": "manter o acompanhamento de rotina que já é feito.",
}


def gerar_resposta_simples(row):

    texto = (
        f"{row['tipo_cancer']} está com nível de atenção "
        f"{row['nivel_prioridade']} em {NOME_MUNICIPIO}.\n"
    )

    if row["evento"] == "ACIMA_DA_TENDENCIA_ESTADUAL":
        texto += (
            f"\nO número de casos está crescendo mais rápido em "
            f"{NOME_MUNICIPIO} do que na média do Estado de São Paulo."
        )
    elif row["evento"] == "ABAIXO_DA_TENDENCIA_ESTADUAL":
        texto += (
            f"\nO número de casos está crescendo mais devagar em "
            f"{NOME_MUNICIPIO} do que na média do Estado de São Paulo."
        )
    else:
        texto += (
            f"\nO número de casos em {NOME_MUNICIPIO} segue no mesmo "
            f"ritmo do Estado de São Paulo."
        )

    if row["situacao"] == "ANOMALIA_POSITIVA":
        texto += (
            "\nEm 2025 houve um aumento fora do normal nesse tipo "
            "de câncer, que ainda precisa ser investigado."
        )
    elif row["situacao"] == "ANOMALIA_NEGATIVA":
        texto += (
            "\nEm 2025 houve uma queda fora do normal nesse tipo "
            "de câncer, que ainda precisa ser investigada."
        )

    recomendacao = RECOMENDACAO_SIMPLES.get(
        row["nivel_prioridade"], "manter o acompanhamento de rotina."
    )

    texto += f"\n\nO que a cidade deveria fazer: {recomendacao.capitalize()}"

    return texto


print("\nPara adaptar a linguagem das respostas, escolha um perfil:")
print("  [1] Técnico (gestor, secretário, pesquisador) — padrão")
print("  [2] Simples (população em geral, sem termos técnicos)")

escolha_perfil = input("Digite 1 ou 2 (ou Enter para técnico): ").strip()

PERFIL = "SIMPLES" if escolha_perfil == "2" else "TECNICO"

# IA de linguagem: quando ativa, interpreta a pergunta usando o
# conhecimento estruturado do Escudo. Se não houver chave/API, o chat
# continua funcionando pelo motor determinístico já existente.
IA_ATIVA = os.getenv("ESCUDO_IA_ATIVA", "SIM").upper() == "SIM"


def detectar_cancer(pergunta_norm):
    for cancer in canceres:
        cancer_norm = normalizar(cancer.replace("_", " "))
        if cancer in pergunta_norm or cancer_norm in pergunta_norm:
            return cancer
    return None


def tentar_resposta_com_ia(pergunta, pergunta_norm, intencao):
    if not IA_ATIVA:
        return False

    # perguntas que o motor de intenções não reconheceu não têm contexto
    # estruturado confiável — nesse caso a IA não deve ser chamada, para
    # não correr o risco de responder sem base nos dados do Escudo.
    if intencao == "DESCONHECIDA":
        return False

    cancer = detectar_cancer(pergunta_norm) if intencao == "CANCER_ESPECIFICO" else None
    contexto = contexto_inteligente(
        pergunta,
        intencao,
        cancer
    )

    if not contexto:
        return False

    try:
        resposta_ia = responder_com_ia(
            pergunta,
            contexto,
            PERFIL
        )
    except Exception as erro:
        print(f"\nIA de linguagem indisponível: {erro}")
        print("Continuando com o motor determinístico do Escudo.\n")
        return False

    print("\nResposta da IA Escudo Feminino:\n")
    print(resposta_ia)
    return True

# =====================================
# REGISTRO DE USO (Missão nº 9)
# =====================================

def registrar_pergunta(pergunta, categoria, reconhecida):

    conn.execute(
        """
        INSERT INTO perguntas_usuarios
        (data_hora, pergunta, categoria, reconhecida)
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            pergunta,
            categoria,
            reconhecida
        )
    )

    conn.commit()


# =====================================
# NORMALIZAÇÃO DE TEXTO
#
# Remove acentos antes de comparar, para que
# "atenção" e "atencao" sejam tratados como
# a mesma coisa — sem precisar listar as duas
# formas em cada categoria.
# =====================================

def normalizar(texto):

    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(
        c for c in sem_acento if not unicodedata.combining(c)
    )

    return sem_acento.upper()


# =====================================
# MOTOR DE INTENÇÕES
#
# União de todas as palavras-chave que estavam
# espalhadas em chat_escudo.py, motor_respostas.py,
# orquestrador_ia.py e perguntas_negocio.py.
#
# As listas abaixo usam só a forma SEM acento —
# a normalização já cuida do resto.
# =====================================

def classificar_intencao(pergunta_norm):

    # simulação precisa vir antes da checagem de nome de câncer,
    # senão "simular reducao de 20% na MAMA" cairia como
    # CANCER_ESPECIFICO em vez de SIMULACAO
    if any(p in pergunta_norm for p in (
        "SIMULAR", "SIMULACAO", "E SE REDUZIRMOS", "SE REDUZIR",
        "SE DIMINUIR"
    )):
        return "SIMULACAO"

    if any(p in pergunta_norm for p in (
        "VULNERAVEL", "VULNERAVEIS", "VULNERABILIDADE",
        "GRUPO DE RISCO", "QUEM ESTA EM RISCO", "MAIS EM RISCO"
    )):
        return "VULNERABILIDADE"

    for cancer in canceres:
        cancer_norm = normalizar(cancer.replace("_", " "))
        if cancer in pergunta_norm or cancer_norm in pergunta_norm:
            return "CANCER_ESPECIFICO"

    # mudança temporal precisa vir antes de SITUACAO_GERAL: perguntas
    # como "como estão os números comparados ao ano passado?" contêm
    # "COMO ESTA" (SITUACAO_GERAL) e também "COMPARADOS AO ANO
    # PASSADO" (MUDANCA_TEMPORAL) — sem essa ordem, SITUACAO_GERAL
    # sempre venceria e a intenção temporal nunca seria alcançada
    if any(p in pergunta_norm for p in (
        "O QUE MUDOU", "MUDOU DESDE", "MUDANCAS DESDE",
        "COMPARAR COM O ANO PASSADO", "COMPARADOS AO ANO PASSADO",
        "COMPARADO AO ANO PASSADO", "COMPARACAO COM O ANO PASSADO",
        "EM RELACAO AO ANO PASSADO", "ANO ANTERIOR"
    )):
        return "MUDANCA_TEMPORAL"

    # perguntas panorâmicas — precisam vir antes de PRIORIDADE_MAXIMA,
    # senão "como está Rio Claro" nunca seria alcançada
    if any(p in pergunta_norm for p in (
        "COMO ESTA", "SITUACAO GERAL", "VISAO GERAL", "PANORAMA",
        "MELHORANDO", "PIORANDO"
    )):
        return "SITUACAO_GERAL"

    if any(p in pergunta_norm for p in (
        "ESTOU DE ACORDO", "FAZ SENTIDO ESSA PRIORIDADE",
        "POR QUE ESSA PRIORIDADE", "COMO DECIDIR",
        "ONDE DEVEMOS INVESTIR", "SE EU PUDESSE AGIR",
        "ESCOLHER APENAS UM", "APOIAR A DECISAO"
    )):
        return "APOIO_DECISAO"

    if any(p in pergunta_norm for p in (
        "ATENCAO", "PRIORIDADE", "PRIORITARIO", "RISCO", "GRAVE",
        "GRAVIDADE", "PREOCUPA", "PREOCUPANTE", "URGENTE", "URGENCIA",
        "SERIO", "INVESTIR", "RECURSOS", "ONDE AGIR", "O QUE FAZER",
        "ESCOLHER", "EXIGEM ACAO", "EXIGE ACAO"
    )):
        return "PRIORIDADE_MAXIMA"

    if any(p in pergunta_norm for p in (
        "TOP", "3 MAIORES", "TRES MAIORES", "RANKING"
    )):
        return "TOP_PRIORIDADES"

    if any(p in pergunta_norm for p in (
        "MORTALIDADE", "OBITO", "MATA", "MORTE", "MORTAL", "LETAL",
        "LETALIDADE"
    )):
        return "MORTALIDADE"

    if any(p in pergunta_norm for p in (
        "CUSTO", "CUSTOS", "GASTO", "GASTOS", "FINANCEIRO",
        "ORCAMENTO", "DINHEIRO", "CARO"
    )):
        return "CUSTO"

    if any(p in pergunta_norm for p in (
        "PERMANENCIA", "LEITO", "LEITOS", "INTERNADO",
        "DIAS INTERNADO", "OCUPACAO"
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

    if "RELATORIO" in pergunta_norm:
        return "RELATORIO_EXECUTIVO"

    return "DESCONHECIDA"


# =====================================
# RESPOSTAS
# =====================================

def responder(intencao, pergunta_norm):

    if intencao == "VULNERABILIDADE":

        if vulnerabilidade_df is None:
            print(
                "\nEsse indicador ainda não foi calculado. Rode "
                "algoritimos\\vulnerabilidade.py antes de perguntar "
                "sobre grupos vulneráveis."
            )
            return

        top = vulnerabilidade_df.sort_values(
            "taxa_mortalidade_faixa", ascending=False
        ).iloc[0]

        print("\nResposta:\n")
        print(
            f"O grupo mais vulnerável identificado é: mulheres de "
            f"{top['faixa_mais_vulneravel']} anos com {top['tipo_cancer']}, "
            f"com taxa de mortalidade de "
            f"{top['taxa_mortalidade_faixa']:.1f}% dentro desse recorte "
            f"etário ({int(top['obitos_faixa'])} óbitos em "
            f"{int(top['internacoes_faixa'])} internações)."
        )

        if top["confiabilidade"] != "OK":
            print(f"\nAtenção: {top['confiabilidade']}.")

        print(
            "\nEsta é a faixa etária com maior taxa de mortalidade "
            "proporcional dentro de cada câncer — não significa "
            "necessariamente o maior número absoluto de casos."
        )

        return

    if intencao == "SIMULACAO":

        numeros = re.findall(r"\d+", pergunta_norm)
        reducao_pct = int(numeros[0]) if numeros else 20
        reducao_pct = max(0, min(reducao_pct, 100))

        cancer_encontrado = next(
            (
                c for c in canceres
                if c in pergunta_norm
                or normalizar(c.replace("_", " ")) in pergunta_norm
            ),
            None
        )

        if cancer_encontrado is None:
            cancer_encontrado = priorizacao.sort_values(
                "pontuacao_final", ascending=False
            ).iloc[0]["tipo_cancer"]

        dados_sim = pd.read_sql(
            """
            SELECT
                COUNT(*) AS internacoes,
                SUM(obito) AS obitos,
                SUM(valor_total) AS custo_total
            FROM internacoes
            WHERE tipo_cancer = ? AND municipio = ? AND ano = 2025
            """,
            conn,
            params=(cancer_encontrado, obter_municipio())
        )

        internacoes_atual = int(dados_sim.iloc[0]["internacoes"] or 0)
        obitos_atual = int(dados_sim.iloc[0]["obitos"] or 0)
        custo_atual = float(dados_sim.iloc[0]["custo_total"] or 0)

        print(
            f"\nSimulação: {cancer_encontrado}, redução de "
            f"{reducao_pct}% nas internações de 2025 em {NOME_MUNICIPIO}.\n"
        )

        if internacoes_atual == 0:
            print(
                f"Não há internações registradas para "
                f"{cancer_encontrado} em {NOME_MUNICIPIO} em 2025 — "
                f"sem base para simular."
            )
            return

        fracao_reduzida = reducao_pct / 100

        internacoes_evitadas = internacoes_atual * fracao_reduzida
        obitos_evitados = obitos_atual * fracao_reduzida
        economia = custo_atual * fracao_reduzida

        print(
            f"Internações evitadas/ano: {internacoes_evitadas:.0f} "
            f"(de {internacoes_atual} atuais)"
        )
        print(
            f"Óbitos evitados/ano (estimado): {obitos_evitados:.1f} "
            f"(de {obitos_atual} atuais)"
        )
        print(f"Economia estimada/ano: R$ {economia:,.2f}")

        print(
            "\nEsta é uma estimativa proporcional simples — assume "
            "que óbitos e custo caem na mesma proporção das "
            "internações. Não é uma previsão epidemiológica precisa, "
            "apenas uma ordem de grandeza para apoiar a discussão."
        )

        return

    if intencao == "CANCER_ESPECIFICO":

        cancer = next(
            c for c in canceres
            if c in pergunta_norm
            or normalizar(c.replace("_", " ")) in pergunta_norm
        )

        if PERFIL == "SIMPLES":
            linha = base_df[base_df["tipo_cancer"] == cancer]

            if linha.empty:
                print(f"\nAinda não há dados registrados para {cancer}.")
                return

            print("\n")
            print(gerar_resposta_simples(linha.iloc[0]))
            return

        linha = memoria[memoria["tipo_cancer"] == cancer]

        if linha.empty:
            print(f"\nAinda não há memória registrada para {cancer}.")
            return

        print("\n")
        print(linha.iloc[0]["memoria"])
        return

    if intencao == "SITUACAO_GERAL":

        total = len(priorizacao)

        criticos_altos = priorizacao[
            priorizacao["nivel_prioridade"].isin(["CRITICA", "ALTA"])
        ]

        anomalias_ativas = anomalias_df[
            anomalias_df["situacao"] != "NORMAL"
        ]

        acima_tendencia = tendencia[tendencia["desvio"] > 0]

        print(f"\nPanorama geral de {NOME_MUNICIPIO}:\n")

        print(
            f"De {total} cânceres monitorados, "
            f"{len(criticos_altos)} estão em nível CRÍTICO ou ALTA "
            f"de prioridade."
        )

        print(
            f"{len(anomalias_ativas)} apresentam anomalia "
            f"(comportamento fora do padrão histórico observado "
            f"nos anos anteriores)."
        )

        print(
            f"{len(acima_tendencia)} estão crescendo mais rápido "
            f"em {NOME_MUNICIPIO} do que no Estado de São Paulo."
        )

        top3 = priorizacao.sort_values(
            "pontuacao_final", ascending=False
        ).head(3)

        print("\nTOP 3 PRIORIDADES:\n")

        for i, (_, row) in enumerate(top3.iterrows(), start=1):
            print(
                f"{i}º {row['tipo_cancer']} — "
                f"{row['nivel_prioridade']} "
                f"({row['pontuacao_final']:.2f})"
            )

        print(
            "\nPergunte pelo nome de um câncer específico para "
            "ver o motivo, o impacto e a recomendação completos."
        )
        return

    if intencao == "PRIORIDADE_MAXIMA":

        r = priorizacao.sort_values(
            "pontuacao_final", ascending=False
        ).iloc[0]

        if PERFIL == "SIMPLES":
            linha = base_df[base_df["tipo_cancer"] == r["tipo_cancer"]]

            print(
                f"\nO câncer que merece maior atenção agora "
                f"é {r['tipo_cancer']}.\n"
            )

            if not linha.empty:
                print(gerar_resposta_simples(linha.iloc[0]))

            return

        print("\nResposta:\n")
        print(
            f"O câncer que merece maior atenção atualmente "
            f"é {r['tipo_cancer']}."
        )
        print(f"Classificação: {r['nivel_prioridade']}.")
        print(f"Pontuação final: {r['pontuacao_final']:.2f}.")

        linha = memoria[memoria["tipo_cancer"] == r["tipo_cancer"]]

        if not linha.empty:
            print("\n")
            print(linha.iloc[0]["memoria"])

        return

    if intencao == "TOP_PRIORIDADES":

        top3 = priorizacao.sort_values(
            "pontuacao_final", ascending=False
        ).head(3)

        print("\nTOP 3 PRIORIDADES:\n")

        for i, (_, row) in enumerate(top3.iterrows(), start=1):
            print(
                f"{i}º {row['tipo_cancer']} — "
                f"{row['nivel_prioridade']} "
                f"({row['pontuacao_final']:.2f})"
            )

        print(
            "\nPergunte pelo nome de um câncer específico para "
            "ver o motivo, o impacto e a recomendação."
        )
        return

    if intencao == "MORTALIDADE":

        r = mortalidade_df.sort_values(
            "taxa_mortalidade", ascending=False
        ).iloc[0]

        print("\nResposta:\n")
        print(
            f"{r['tipo_cancer']} possui a maior taxa de "
            f"mortalidade ({r['taxa_mortalidade']:.2f}%)."
        )
        return

    if intencao == "CUSTO":

        r = custos_df.sort_values(
            "valor_total", ascending=False
        ).iloc[0]

        print("\nResposta:\n")
        print(f"{r['tipo_cancer']} apresenta o maior custo hospitalar.")
        print(f"Valor total: R$ {r['valor_total']:,.2f}")
        return

    if intencao == "PERMANENCIA":

        r = permanencia_df.sort_values(
            "permanencia_media", ascending=False
        ).iloc[0]

        print("\nResposta:\n")
        print(
            f"{r['tipo_cancer']} apresenta a maior "
            f"permanência hospitalar."
        )
        print(f"Média: {r['permanencia_media']:.2f} dias.")
        return

    if intencao == "FAIXA_ETARIA":

        dominante = (
            faixa_df
            .sort_values("internacoes", ascending=False)
            .drop_duplicates("tipo_cancer")
        )

        print("\nResposta:\n")

        for _, row in dominante.iterrows():
            print(f"{row['tipo_cancer']} -> {row['faixa_etaria']}")

        return

    if intencao == "TENDENCIA_ESTADUAL":

        r = tendencia.sort_values(
            "desvio", ascending=False
        ).iloc[0]

        print("\nResposta:\n")

        if r["desvio"] >= 0:
            print(
                f"{r['tipo_cancer']} está {r['desvio']:.2f}% "
                f"acima da tendência estadual."
            )
        else:
            print(
                f"{r['tipo_cancer']} está {abs(r['desvio']):.2f}% "
                f"abaixo da tendência estadual."
            )

        if r.get("confiabilidade", "OK") != "OK":
            print(f"\nAtenção: {r['confiabilidade']}.")

        return

    if intencao == "ANOMALIAS":

        df = anomalias_df[anomalias_df["situacao"] != "NORMAL"]

        print("\nResposta:\n")

        if df.empty:
            print("Nenhuma anomalia identificada.")
        else:
            for _, row in df.iterrows():
                print(f"{row['tipo_cancer']} - {row['situacao']}")

        return

    if intencao == "INCIDENCIA":

        df = pd.read_sql("""
        SELECT tipo_cancer, COUNT(*) AS total
        FROM internacoes
        WHERE municipio = ?
        GROUP BY tipo_cancer
        ORDER BY total DESC
        LIMIT 1
        """, conn, params=(MUNICIPIO,))

        r = df.iloc[0]

        print("\nResposta:\n")
        print(
            f"O câncer com maior volume de internações hospitalares "
            f"é {r['tipo_cancer']}."
        )
        return

    if intencao == "RELATORIO_EXECUTIVO":

        try:
            with open(
                "relatorio_executivo.txt", "r", encoding="utf-8"
            ) as arquivo:
                print("\n")
                print(arquivo.read())

        except FileNotFoundError:
            print(
                "\nArquivo relatorio_executivo.txt não encontrado "
                "na pasta atual."
            )

        return

    print("\nAinda não compreendi essa pergunta.")
    print(
        "Tente perguntar sobre: panorama geral, prioridade, "
        "mortalidade, custo, permanência, faixa etária, tendência "
        "estadual, anomalias, incidência, relatório executivo, "
        "simular redução de X% (ex.: 'simular reducao de 20% na "
        "MAMA'), grupos vulneráveis, ou o nome de um câncer "
        "específico (ex.: MAMA, COLO_UTERO)."
    )


# =====================================
# CHAT
# =====================================

print("\n=== CHAT ESCUDO FEMININO ===\n")

while True:

    pergunta = input(
        "\nPergunta (digite 'sair' para encerrar): "
    )

    if pergunta.lower() == "sair":
        break

    pergunta_norm = normalizar(pergunta)

    intencao = classificar_intencao(pergunta_norm)

    if not tentar_resposta_com_ia(pergunta, pergunta_norm, intencao):
        responder(intencao, pergunta_norm)

    registrar_pergunta(
        pergunta,
        intencao,
        "SIM" if intencao != "DESCONHECIDA" else "NAO"
    )

conn.close()

print("\nChat encerrado.")
