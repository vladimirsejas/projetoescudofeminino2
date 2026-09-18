import subprocess
import sys

# =====================================
# CATÁLOGO DE PERGUNTAS
#
# Missão técnica nº 1 (nunca formalizada) +
# Missão nº 10 (teste de entrega), combinadas
# num único script executável. Cobre as
# categorias do sistema e as perguntas típicas
# de cada perfil de usuário (seção 5 da
# Memória Técnica): secretário de saúde,
# secretária da mulher, prefeita, secretário
# da fazenda, gestor hospitalar, pesquisador,
# população.
#
# Formato: (pergunta, categoria_esperada)
# =====================================

CHAT_SCRIPT = "algoritimos/chat_escudo.py"

PERGUNTAS = [
    # --- Panorama geral ---
    ("Como está Rio Claro?", "panorama geral"),
    ("O município está melhorando?", "panorama geral"),
    ("Qual o panorama geral da saúde da mulher?", "panorama geral"),
    ("Dê uma visão geral da situação", "panorama geral"),

    # --- Prioridade / risco ---
    ("Qual câncer merece mais atenção?", "prioridade"),
    ("O que mais preocupa atualmente?", "prioridade"),
    ("Onde devemos investir recursos?", "prioridade"),
    ("Qual câncer é mais grave?", "prioridade"),
    ("Qual é a principal prioridade?", "prioridade"),
    ("Existe algum risco urgente?", "prioridade"),
    ("Se eu pudesse agir em apenas um câncer, qual escolher?", "prioridade"),
    ("Quais problemas exigem ação imediata?", "prioridade"),

    # --- Top / ranking ---
    ("Quais são as 3 maiores prioridades?", "top prioridades"),
    ("Me dê o ranking de prioridades", "top prioridades"),

    # --- Mortalidade ---
    ("Qual câncer mais mata?", "mortalidade"),
    ("Qual tem a maior taxa de mortalidade?", "mortalidade"),
    ("Qual é o mais letal?", "mortalidade"),

    # --- Custo ---
    ("Qual câncer gera maior custo hospitalar?", "custo"),
    ("Onde está o maior gasto?", "custo"),
    ("Quais doenças geram mais custos para o orçamento?", "custo"),

    # --- Permanência hospitalar ---
    ("Qual apresenta maior permanência hospitalar?", "permanencia"),
    ("Qual ocupa mais leitos?", "permanencia"),
    ("Quais doenças ocupam mais leitos do hospital?", "permanencia"),

    # --- Faixa etária ---
    ("Qual faixa etária é mais afetada?", "faixa etaria"),
    ("Quais são as idades mais atingidas?", "faixa etaria"),

    # --- Tendência estadual ---
    ("Qual câncer está acima da tendência estadual?", "tendencia estadual"),
    ("Rio Claro acompanha o comportamento do Estado?", "tendencia estadual"),
    ("O que está crescendo mais rápido que São Paulo?", "tendencia estadual"),

    # --- Anomalias ---
    ("Existem comportamentos anormais?", "anomalias"),
    ("Quais são os principais alertas?", "anomalias"),
    ("Há algo fora do padrão histórico?", "anomalias"),

    # --- Incidência ---
    ("Qual câncer possui mais internações?", "incidencia"),
    ("Qual é o mais comum em Rio Claro?", "incidencia"),
    ("Quais doenças afetam mais mulheres?", "incidencia"),

    # --- Relatório executivo ---
    ("Gere um relatório executivo", "relatorio executivo"),
    ("Quero o relatório completo", "relatorio executivo"),

    # --- Simulação de impacto ---
    ("Simular redução de 20% na MAMA", "simulacao"),
    ("E se reduzirmos 30% dos casos de colo do útero?", "simulacao"),

    # --- Câncer específico / explicação ---
    ("Fale sobre MAMA", "cancer especifico"),
    ("O que você sabe sobre COLO_UTERO?", "cancer especifico"),
    ("Por que a MAMA é um risco?", "cancer especifico"),
    ("Explique a situação do PULMAO", "cancer especifico"),

    # --- Perguntas soltas por perfil (podem ou não ser
    # reconhecidas hoje — servem pra medir a lacuna real
    # de cobertura, não só confirmar o que já funciona) ---
    ("Quais mulheres estão vulneráveis?", "(sem categoria prevista)"),
    ("O que mudou desde o ano passado?", "(sem categoria prevista)"),
    ("Estou de acordo com essa prioridade?", "(sem categoria prevista)"),
]


def rodar_bateria():

    entrada = "1\n" + "\n".join(p for p, _ in PERGUNTAS) + "\nsair\n"

    try:
        resultado = subprocess.run(
            [sys.executable, CHAT_SCRIPT],
            input=entrada,
            capture_output=True,
            text=True,
            timeout=120
        )
    except FileNotFoundError:
        print(
            f"\nERRO: não encontrei '{CHAT_SCRIPT}'. Rode este script "
            f"a partir da raiz do projeto (C:\\projetoescudofeminino2)."
        )
        return
    except subprocess.TimeoutExpired:
        print("\nERRO: o chat_escudo.py não respondeu em 120 segundos.")
        return

    if resultado.returncode != 0 and "ERRO:" in resultado.stdout:
        print("\nO chat_escudo.py acusou tabela faltando:\n")
        print(resultado.stdout)
        return

    marcador = "\nPergunta (digite 'sair' para encerrar): "
    blocos = resultado.stdout.split(marcador)

    respostas = blocos[1:1 + len(PERGUNTAS)]

    if len(respostas) != len(PERGUNTAS):
        print(
            f"\nAVISO: esperava {len(PERGUNTAS)} respostas, recebi "
            f"{len(respostas)}. O chat pode ter encerrado antes do "
            f"esperado — veja a saída bruta abaixo.\n"
        )
        print(resultado.stdout[-2000:])
        return

    reconhecidas = []
    nao_reconhecidas = []

    for (pergunta, categoria), resposta in zip(PERGUNTAS, respostas):

        if "Ainda não compreendi essa pergunta." in resposta:
            nao_reconhecidas.append((pergunta, categoria))
        else:
            reconhecidas.append((pergunta, categoria))

    total = len(PERGUNTAS)
    taxa = len(reconhecidas) / total * 100

    print("\n=== COBERTURA DO CATÁLOGO DE PERGUNTAS ===\n")
    print(f"Total testado: {total}")
    print(f"Reconhecidas: {len(reconhecidas)} ({taxa:.1f}%)")
    print(f"Não reconhecidas: {len(nao_reconhecidas)} ({100 - taxa:.1f}%)")

    if nao_reconhecidas:
        print("\n--- Perguntas NÃO reconhecidas ---\n")
        for pergunta, categoria in nao_reconhecidas:
            print(f"[{categoria}] {pergunta}")
        print(
            "\nEstas são candidatas diretas a novos sinônimos em "
            "classificar_intencao(), dentro de algoritimos\\chat_escudo.py."
        )
    else:
        print("\nTodas as perguntas do catálogo foram reconhecidas.")


if __name__ == "__main__":
    rodar_bateria()
