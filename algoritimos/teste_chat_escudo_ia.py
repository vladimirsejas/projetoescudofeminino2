import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

# =====================================
# TESTE DO FLUXO COM IA ATIVA
#
# Achado da revisão cruzada (ChatGPT): teste_chat_escudo.py roda com
# ESCUDO_IA_ATIVA=NAO, então comprova só o motor determinístico --
# nunca testou o caminho real (pergunta -> classificar_intencao() ->
# tentar_resposta_com_ia() -> responder()), onde o Gemini é tentado
# ANTES do determinístico. Esse caminho tinha um bug real: PREVISAO,
# SIMULACAO e VULNERABILIDADE não tinham entrada em
# contexto_inteligente() (motor_raciocinio.py), que devolvia o
# panorama genérico sem os dados específicos -- a IA podia responder
# uma previsão, por exemplo, sem nunca ver a tabela previsao_temporal.
#
# Este teste não chama a API do Gemini de verdade (não há chave
# aqui) -- ele substitui ia_linguagem.responder_com_ia por um dublê
# que só captura o contexto recebido, e verifica que esse contexto
# contém os dados reais e corretos da tabela determinística
# correspondente. Isso prova a parte que importa (o Gemini SÓ pode
# explicar o que está no contexto, e o contexto agora tem o dado
# certo) sem depender de rede ou credencial.
# =====================================

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ORIGINAL = r"C:\projetoescudofeminino2\banco\escudo_feminino.db"

sys.path.insert(0, DIRETORIO_ATUAL)

from teste_chat_escudo import _montar_banco  # noqa: E402


def _rodar_chat_com_ia_capturada(caminho_banco, perguntas):
    """
    Roda chat_escudo.py de verdade com ESCUDO_IA_ATIVA=SIM, mas com
    ia_linguagem.responder_com_ia substituída por um dublê que só
    registra o contexto recebido para cada pergunta, na mesma ordem.
    Devolve a lista de contextos capturados (um por pergunta) e a
    transcrição completa (para checar que o texto do fallback
    determinístico -- "Resposta:" impresso por responder() -- não
    apareceu, confirmando que o caminho da IA foi realmente tomado).
    """

    respostas = ["1"] + perguntas + ["sair"]
    fila = iter(respostas)

    def input_stub(prompt=""):
        return next(fila)

    contextos_capturados = []

    def responder_com_ia_stub(pergunta, contexto, perfil="TECNICO"):
        contextos_capturados.append(contexto)
        return f"[RESPOSTA-IA-SIMULADA para: {pergunta}]"

    import ia_linguagem
    ia_linguagem.responder_com_ia = responder_com_ia_stub

    # motor_raciocinio.py mantém seu próprio BANCO hardcoded,
    # independente do de chat_escudo.py -- em produção real os dois
    # apontam pro mesmo arquivo (mesma string literal), mas aqui
    # cada um precisa ser apontado pro banco sintético separadamente,
    # senão contexto_inteligente() tenta ler do caminho original
    # (inexistente neste ambiente) e cai silenciosamente no contexto
    # vazio/genérico
    import motor_raciocinio
    motor_raciocinio.BANCO = caminho_banco

    caminho_script = os.path.join(DIRETORIO_ATUAL, "chat_escudo.py")
    codigo_fonte = open(caminho_script, encoding="utf-8-sig").read()
    codigo_fonte = codigo_fonte.replace(
        CAMINHO_ORIGINAL, caminho_banco.replace("\\", "\\\\")
    )

    os.environ["ESCUDO_MUNICIPIO"] = "RIO_CLARO"
    os.environ["ESCUDO_IA_ATIVA"] = "SIM"

    if "configuracao_geografica" in sys.modules:
        sys.modules["configuracao_geografica"].BANCO = caminho_banco

    saida = io.StringIO()

    import builtins
    input_original = builtins.input
    builtins.input = input_stub

    try:
        with redirect_stdout(saida):
            exec(
                compile(codigo_fonte, "chat_escudo.py", "exec"),
                {"__name__": "__teste_chat_escudo_ia__"}
            )
    finally:
        builtins.input = input_original

    return contextos_capturados, saida.getvalue()


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
        "previsao do cancer de mama",
        "quais previsoes apresentaram ganho em relacao ao metodo simples",
        "grupos vulneraveis",
        "simular reducao de 20% na mama",
        "mortalidade do cancer de mama",
    ]

    try:
        _montar_banco(banco)
        contextos, transcricao = _rodar_chat_com_ia_capturada(
            banco, perguntas
        )
    finally:
        os.remove(banco)

    checar(
        "a IA foi chamada para as 5 perguntas (nenhuma caiu no "
        "fallback determinístico por engano)",
        len(contextos) == len(perguntas)
    )

    checar(
        "nenhuma resposta veio do motor determinístico por engano "
        "(responder() imprime 'Resposta:' -- com a IA ativa e "
        "respondendo, esse texto não deve aparecer)",
        "Resposta:" not in transcricao
    )

    if len(contextos) != len(perguntas):
        raise SystemExit(
            f"Só {len(contextos)} de {len(perguntas)} perguntas "
            f"geraram contexto -- não dá pra continuar as checagens "
            f"de conteúdo com segurança."
        )

    contexto_previsao_mama = contextos[0]
    checar(
        "previsão do câncer de mama -> o contexto entregue à IA "
        "contém o número real da tabela previsao_temporal (100), "
        "não só o panorama genérico (achado da revisão cruzada: "
        "PREVISAO não tinha entrada em contexto_inteligente())",
        "100" in contexto_previsao_mama
        and "PREVISÃO TEMPORAL" in contexto_previsao_mama
    )
    checar(
        "o contexto de previsão também traz OVARIO com o erro real "
        "de validação (50) -- prova que é a tabela inteira, não um "
        "resumo inventado",
        "50" in contexto_previsao_mama
    )

    contexto_previsao_ganho = contextos[1]
    checar(
        "'quais previsões tiveram ganho' -> o contexto ainda é a "
        "tabela real de previsao_temporal (a IA decide o recorte "
        "sozinha em cima do dado real, não recebe uma lista "
        "pré-filtrada -- mas precisa ver supera_baseline para poder "
        "responder direito)",
        "supera_baseline" in contexto_previsao_ganho
    )

    contexto_vulnerabilidade = contextos[2]
    checar(
        "'grupos vulneráveis' -> o contexto contém o dado real da "
        "tabela vulnerabilidade (faixa 60-79), não o panorama "
        "genérico (achado da revisão cruzada: VULNERABILIDADE não "
        "tinha entrada em contexto_inteligente())",
        "60-79" in contexto_vulnerabilidade
        and "VULNERABILIDADE" in contexto_vulnerabilidade
    )

    contexto_simulacao = contextos[3]
    checar(
        "'simular redução de 20% na mama' -> o contexto contém o "
        "resultado JÁ CALCULADO (internações evitadas, economia), "
        "não pede pra IA calcular nada (achado da revisão cruzada: "
        "SIMULACAO não tinha entrada em contexto_inteligente() e "
        "arriscava a IA inventar o cálculo)",
        "MAMA" in contexto_simulacao
        and "REDUÇÃO SIMULADA: 20%" in contexto_simulacao
        and "ECONOMIA ESTIMADA" in contexto_simulacao
    )

    contexto_mortalidade = contextos[4]
    checar(
        "mortalidade do câncer de mama (categoria que já funcionava "
        "antes desta correção) continua trazendo o dado real -- "
        "prova que a correção não quebrou o caminho que já existia",
        "10.0" in contexto_mortalidade or "10.00" in contexto_mortalidade
    )

    if falhas:
        raise SystemExit(f"{len(falhas)} checagem(ns) falharam: {falhas}")

    print(
        "\nTodas as checagens do fluxo com IA ativa passaram -- "
        "PREVISAO, SIMULACAO e VULNERABILIDADE agora entregam dado "
        "real à IA, nunca o panorama genérico."
    )


if __name__ == "__main__":
    testar()
