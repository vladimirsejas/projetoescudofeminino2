import re
import unicodedata
from datetime import datetime

from inteligencia import (
    MEDIA_PEQUENA,
    ano_atipico_no_estado,
    anos_fora_do_padrao,
    comparar_com_estado,
    formatar_numero,
    leitura_evolucao,
    nome_doenca,
    projetar,
    resumo_doencas,
    ritmo_anual_pct,
    serie_doenca,
    testar_projecao,
    GRUPO_ESTADO,
)

# Chat inteligente do Escudo Feminino
# -----------------------------------
# Princípio: o LLM NÃO calcula os números. Ele interpreta fatos já
# calculados pelo módulo inteligencia.py.
#
# Esta camada resolve:
# - linguagem natural e sinônimos;
# - perguntas de continuação ("e mama?", "e em 2024?", "e o custo?");
# - múltiplos assuntos na mesma pergunta;
# - respostas para capacidades que o banco ainda não sustenta;
# - memória curta da conversa;
# - fallback para Gemini estruturado quando a classificação local é ambígua.


ASSUNTOS = {
    "METODO": ["COMO CALCUL", "COMO FOI CALCUL", "METODO", "METODOLOGIA", "FONTE",
               "DE ONDE VEM", "CONFIAVEL", "CONFIAR", "DATASUS", "SIH", "COMO LER"],
    "PROJECAO": ["PREVIS", "PREVER", "PREVE", "PROJEC", "FUTURO", "PROXIMOS ANOS",
                 "PROXIMO ANO", "VAI AUMENTAR", "VAI CRESCER", "VAI DIMINUIR",
                 "VAI CAIR", "ESPERAR", "DAQUI"],
    "ATENCAO": ["ATENCAO", "PRIORIDADE", "PRIORIT", "PREOCUP", "URGEN", "INVESTIR",
                "INVESTIMENTO", "ORCAMENT", "RECURSO", "ONDE AGIR", "O QUE FAZER",
                "PLANEJ", "FOCAR", "FOCO"],
    "FORA_PADRAO": ["FORA DO PADRAO", "ANOMALIA", "ATIPIC", "ANORMA", "ESTRANH",
                    "PICO", "SALTO", "SALTOU", "ACIMA DO ESPERADO", "ABAIXO DO ESPERADO"],
    "ESTADO": ["ESTADO", "SAO PAULO", "SP", "ESTADUAL", "COMPARAD", "COMPARAR",
               "COMPARACAO", "RESTO DO ESTADO"],
    "MORTALIDADE": ["MORTALIDADE", "OBITO", "MORTE", "MORRE", "MORREM", "MORRERAM",
                    "MATA", "LETAL", "LETALIDADE", "GRAVE", "GRAVIDADE"],
    "CUSTO": ["CUSTO", "CUSTA", "CUSTOU", "GASTO", "GASTOU", "GASTA", "VALOR",
              "DINHEIRO", "CARO", "REAIS", "R$", "PAGO", "DESPESA"],
    "PERMANENCIA": ["PERMANENCIA", "DIAS", "LEITO", "TEMPO INTERNAD",
                    "FICAM INTERNAD", "FICA INTERNAD", "QUANTO TEMPO"],
    "IDADE": ["IDADE", "FAIXA ETARIA", "FAIXA DE IDADE", "ANOS DE IDADE", "FAIXAS"],
    "INCIDENCIA": ["INCIDENCIA", "CASOS NOVOS", "NOVOS CASOS", "DIAGNOSTICO",
                   "DIAGNOSTICADOS", "QUANTAS MULHERES TEM CANCER"],
    "EVOLUCAO": ["EVOLU", "CRESC", "AUMENT", "DIMINU", "CAIU", "CAINDO",
                 "CAEM", "SUBIU", "MUDOU", "MUDARAM", "AO LONGO", "HISTOR",
                 "TENDENCIA", "ANO A ANO"],
    "PANORAMA": ["GERAL", "PANORAMA", "SITUACAO", "RESUMO", "QUAIS", "MAIS COMUM",
                 "MAIS AFETA", "RANKING", "MAIOR", "MAIORES", "TOTAL", "QUANTAS",
                 "QUANTOS", "COMO ESTAMOS"],
}

SINONIMOS_CANCER = {
    "COLORRETAL": ["COLORRETAL", "COLO RETAL", "INTESTINO", "RETO", "COLON"],
    "COLO_UTERO": ["COLO DO UTERO", "COLO UTERO", "UTERO", "CERVICAL", "COLO_UTERO"],
    "MAMA": ["MAMA", "MAMAS", "SEIO", "SEIOS"],
    "PELE_NAO_MELANOMA": ["PELE", "PELE NAO MELANOMA"],
    "PULMAO": ["PULMAO", "PULMOES", "PULMONAR"],
    "OVARIO": ["OVARIO", "OVARIOS"],
    "TIREOIDE": ["TIREOIDE", "TIROIDE"],
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c)).upper()
    return " " + re.sub(r"[^A-Z0-9$ ]+", " ", texto) + " "


def _encontra(texto_norm, termo):
    termo = normalizar(termo).strip()
    return re.search(r"(?<![A-Z0-9])" + re.escape(termo), texto_norm) is not None


def detectar_cancer(texto_norm, disponiveis):
    for codigo, termos in SINONIMOS_CANCER.items():
        if codigo in disponiveis and any(_encontra(texto_norm, t) for t in termos):
            return codigo
    for codigo in disponiveis:
        if _encontra(texto_norm, nome_doenca(codigo)):
            return codigo
    return None


def detectar_ano(texto_norm):
    anos = re.findall(r"(?<![0-9])(20[0-9]{2})(?![0-9])", texto_norm)
    return int(anos[0]) if anos else None


def detectar_assuntos(texto_norm):
    pontos = {}
    for assunto, palavras in ASSUNTOS.items():
        pontos[assunto] = sum(_encontra(texto_norm, p) for p in palavras)
    maior = max(pontos.values(), default=0)
    if maior == 0:
        return [], pontos
    # Mantém todos os assuntos fortes; isso permite "mortalidade e custo".
    selecionados = [a for a, p in pontos.items() if p == maior]
    # Se houver um assunto claramente mais forte, ainda preserva assuntos
    # secundários explicitamente detectados.
    secundarios = [a for a, p in pontos.items() if p > 0 and a not in selecionados]
    if len(selecionados) == 1 and secundarios:
        primeiro = selecionados[0]
        # Só adiciona secundários quando são semanticamente independentes.
        independentes = [a for a in secundarios if a not in {"PANORAMA", "EVOLUCAO"}]
        return [primeiro] + independentes[:3], pontos
    return selecionados[:4], pontos


def ultimo_contexto(historico):
    if not historico:
        return {}
    for item in reversed(historico):
        if not isinstance(item, dict):
            continue
        contexto = item.get("contexto", {})
        if contexto:
            return contexto
    return {}


def entender(pergunta, disponiveis, cancer_em_foco=None, historico=None):
    texto = normalizar(pergunta)
    assuntos, pontos = detectar_assuntos(texto)
    cancer = detectar_cancer(texto, disponiveis)
    ano = detectar_ano(texto)

    anterior = ultimo_contexto(historico or [])

    # Resolve continuação curta:
    # "e mama?", "e em 2024?", "e o custo?", "e esse câncer?"
    if cancer is None and re.search(r"\b(E|ESSE|ESSA|DELE|DELA|TAMBEM)\b", texto):
        cancer = anterior.get("cancer") or (cancer_em_foco if cancer_em_foco in disponiveis else None)
    if cancer is None and cancer_em_foco in disponiveis and len(texto.strip()) < 45:
        cancer = cancer_em_foco

    if ano is None:
        ano = anterior.get("ano")

    if not assuntos:
        if cancer:
            assuntos = ["EVOLUCAO"]
        elif ano:
            assuntos = ["FORA_PADRAO"]
        else:
            assuntos = ["PANORAMA"]

    # Perguntas "quantas internações de mama?" são evolução/panorama da doença.
    if assuntos == ["PANORAMA"] and cancer:
        assuntos = ["EVOLUCAO"]

    return {
        "assunto": assuntos[0],
        "assuntos": assuntos,
        "cancer": cancer,
        "cancer_citado": cancer is not None,
        "cancer_em_foco": cancer_em_foco if cancer_em_foco in disponiveis else None,
        "ano": ano,
        "pontuacao": pontos,
        "ambigua": len(assuntos) > 3,
    }


def _plural(n, singular, plural):
    return f"{formatar_numero(n)} {singular if n == 1 else plural}"


def _pct(parte, total):
    return parte / total * 100 if total else 0.0


def _taxa(serie, cancer, grupo, campo_num, campo_den="internacoes"):
    dados = serie_doenca(serie, cancer, grupo)
    den = dados[campo_den].sum()
    return (dados[campo_num].sum() / den if den else 0.0), dados[campo_num].sum(), den


def fatos_panorama(serie, cidade, _cancer):
    resumo = resumo_doencas(serie)
    total = resumo["internacoes"].sum()
    ano_ini, ano_fim = int(serie["ano"].min()), int(serie["ano"].max())
    fatos = [f"De {ano_ini} a {ano_fim}, mulheres de {cidade} tiveram "
             f"{formatar_numero(total)} internações no SUS pelos "
             f"{len(resumo)} tipos de câncer acompanhados, com "
             f"{formatar_numero(resumo['obitos'].sum())} óbitos durante a internação."]
    for i, linha in resumo.head(3).iterrows():
        fatos.append(f"{i + 1}º lugar: {linha['doenca']}, com "
                     f"{formatar_numero(linha['internacoes'])} internações "
                     f"({formatar_numero(_pct(linha['internacoes'], total))}% do total).")
    return fatos, "Veja o panorama de cânceres no primeiro gráfico do painel."


def fatos_evolucao(serie, cidade, cancer, ano=None):
    dados = serie_doenca(serie, cancer)
    if dados.empty:
        return [f"Não há dados de {nome_doenca(cancer)} para {cidade}."], ""
    fatos = [f"Câncer de {nome_doenca(cancer).lower()} em {cidade}:"]
    fatos += leitura_evolucao(serie, cancer)
    pico = dados.loc[dados["internacoes"].idxmax()]
    fatos.append(f"O ano com mais internações foi {int(pico['ano'])} "
                 f"({formatar_numero(pico['internacoes'])}).")
    if ano is not None and ano in set(dados["ano"]):
        valor = dados.loc[dados["ano"] == ano, "internacoes"].iloc[0]
        fatos.append(f"Em {ano} foram {formatar_numero(valor)} internações.")
    return fatos, "Veja o gráfico de evolução com o câncer selecionado."


def fatos_estado(serie, cidade, cancer):
    if cancer:
        comp = comparar_com_estado(serie, cancer)
        fatos = [f"Câncer de {nome_doenca(cancer).lower()}: em {cidade}, "
                 f"ritmo de {formatar_numero(comp['ritmo_municipio'], 1)}% ao ano; "
                 f"no Estado de SP, {formatar_numero(comp['ritmo_estado'] or 0, 1)}% ao ano."]
        return fatos + [f for f in leitura_evolucao(serie, cancer) if "Estado" in f],             "Veja o gráfico com 'Comparar com o Estado de SP' ligado."
    fatos = ["Ritmo das internações, município x Estado de SP:"]
    for codigo in resumo_doencas(serie)["tipo_cancer"]:
        comp = comparar_com_estado(serie, codigo)
        dif = comp["ritmo_municipio"] - (comp["ritmo_estado"] or 0)
        situacao = ("mais rápido que o Estado" if dif > 1.5 else
                    "mais lento que o Estado" if dif < -1.5 else "parecido com o Estado")
        fatos.append(f"{nome_doenca(codigo)}: {formatar_numero(comp['ritmo_municipio'], 1)}% ao ano "
                     f"({situacao}; Estado: {formatar_numero(comp['ritmo_estado'] or 0, 1)}%).")
    return fatos, "Veja o gráfico de evolução com a comparação estadual ligada."


def _alerta_estado(serie):
    ano_fim = int(serie["ano"].max())
    fora, total = ano_atipico_no_estado(serie, ano_fim)
    if total and fora >= total / 2:
        return (f"Atenção: em {ano_fim}, {fora} dos {total} cânceres tiveram "
                f"comportamento atípico simultaneamente no Estado de SP. "
                f"Isso pode indicar mudança no registro/processamento das AIHs; "
                f"não permite concluir mudança no adoecimento.")
    return None


def fatos_fora_padrao(serie, cidade, cancer):
    canceres = [cancer] if cancer else list(resumo_doencas(serie)["tipo_cancer"])
    fatos = []
    for codigo in canceres:
        fora = anos_fora_do_padrao(serie_doenca(serie, codigo))
        for _, linha in fora.iterrows():
            aviso = " (números pequenos: comparação frágil)" if linha["numeros_pequenos"] else ""
            fatos.append(f"{nome_doenca(codigo)}: {linha['ano']} ficou {linha['direcao']} "
                         f"do esperado ({formatar_numero(linha['observado'])} internações; "
                         f"esperado cerca de {formatar_numero(linha['esperado'])}){aviso}.")
    if not fatos:
        fatos.append(f"Não foi identificado ano fora do padrão pela regra atual para "
                     f"{nome_doenca(cancer).lower() if cancer else 'os cânceres acompanhados'} em {cidade}.")
    alerta = _alerta_estado(serie)
    if alerta:
        fatos.append(alerta)
    fatos.append("Um ano fora do padrão é um sinal para investigação; não demonstra a causa.")
    return fatos, "Veja o gráfico com 'Destacar anos fora do padrão' ligado."


def fatos_projecao(serie, cidade, cancer):
    canceres = [cancer] if cancer else list(resumo_doencas(serie)["tipo_cancer"].head(3))
    fatos = []
    for codigo in canceres:
        dados = serie_doenca(serie, codigo)
        if len(dados) < 3:
            continue
        proj = projetar(dados).iloc[-1]
        teste = testar_projecao(dados)
        fatos.append(f"{nome_doenca(codigo)}: se a tendência de {int(dados['ano'].min())}–"
                     f"{int(dados['ano'].max())} continuar, a projeção para {int(proj['ano'])} "
                     f"é de cerca de {formatar_numero(proj['internacoes'])} internações "
                     f"(faixa exploratória de {formatar_numero(proj['minimo'])} a "
                     f"{formatar_numero(proj['maximo'])}).")
        if teste:
            melhor = "menor" if teste["erro_tendencia"] <= teste["erro_media"] else "maior"
            fatos.append(f"No teste retrospectivo, o erro médio da tendência foi "
                         f"{formatar_numero(teste['erro_tendencia'], 1)}; a média de referência "
                         f"teve erro de {formatar_numero(teste['erro_media'], 1)} ({melhor} erro).")
        if dados["internacoes"].mean() < MEDIA_PEQUENA:
            fatos.append(f"{nome_doenca(codigo)} tem poucos registros anuais; a projeção é frágil.")
    alerta = _alerta_estado(serie)
    if alerta:
        fatos.append(alerta)
    fatos.append("É projeção exploratória de internações, não previsão clínica, incidência futura nem causalidade.")
    return fatos, "Veja o gráfico com 'Projeção exploratória' ligado."


def fatos_mortalidade(serie, cidade, cancer):
    canceres = [cancer] if cancer else list(resumo_doencas(serie)["tipo_cancer"])
    linhas = []
    for codigo in canceres:
        taxa, obitos, intern = _taxa(serie, codigo, "MUNICIPIO", "obitos")
        taxa_sp, _, _ = _taxa(serie, codigo, GRUPO_ESTADO, "obitos")
        linhas.append((taxa, codigo, obitos, intern, taxa_sp))
    linhas.sort(reverse=True)
    fatos = [f"Óbitos durante a internação (letalidade hospitalar), {cidade} x Estado de SP:"]
    for taxa, codigo, obitos, intern, taxa_sp in linhas:
        aviso = " (poucos óbitos: comparação frágil)" if obitos < 10 else ""
        fatos.append(f"{nome_doenca(codigo)}: {_plural(obitos, 'óbito', 'óbitos')} em "
                     f"{formatar_numero(intern)} internações = {formatar_numero(taxa * 100, 1)}%; "
                     f"Estado: {formatar_numero(taxa_sp * 100, 1)}%{aviso}.")
    fatos.append("Isto mede óbitos ocorridos durante as internações registradas, não a mortalidade populacional.")
    return fatos, "Os óbitos também aparecem no panorama do painel."


def fatos_custo(serie, cidade, cancer):
    canceres = [cancer] if cancer else list(resumo_doencas(serie)["tipo_cancer"])
    fatos = []
    total = 0.0
    for codigo in canceres:
        _, valor, intern = _taxa(serie, codigo, "MUNICIPIO", "valor_total")
        _, valor_sp, intern_sp = _taxa(serie, codigo, GRUPO_ESTADO, "valor_total")
        medio = valor / intern if intern else 0
        medio_sp = valor_sp / intern_sp if intern_sp else 0
        total += valor
        fatos.append(f"{nome_doenca(codigo)}: R$ {formatar_numero(valor)} em "
                     f"{formatar_numero(intern)} internações (média de R$ {formatar_numero(medio)} "
                     f"por internação; média estadual R$ {formatar_numero(medio_sp)}).")
    fatos.insert(0, f"Valores hospitalares registrados nas AIHs de {cidade}, no período: "
                    f"R$ {formatar_numero(total)}.")
    fatos.append("Esse valor é o registrado nas AIHs/SIH para internações; não representa todo o orçamento "
                 "municipal da saúde e não inclui toda a assistência ambulatorial.")
    return fatos, "O painel atual ainda não tem gráfico financeiro próprio; o chat consulta os valores calculados."


def fatos_permanencia(serie, cidade, cancer):
    canceres = [cancer] if cancer else list(resumo_doencas(serie)["tipo_cancer"])
    fatos = [f"Tempo médio de permanência hospitalar em {cidade}:"]
    for codigo in canceres:
        media, _, intern = _taxa(serie, codigo, "MUNICIPIO", "dias_permanencia")
        media_sp, _, _ = _taxa(serie, codigo, GRUPO_ESTADO, "dias_permanencia")
        fatos.append(f"{nome_doenca(codigo)}: {formatar_numero(media, 1)} dias por internação "
                     f"(Estado: {formatar_numero(media_sp, 1)} dias; {formatar_numero(intern)} internações).")
    return fatos, "Esses dados ainda não têm gráfico próprio no painel."


def fatos_idade(_serie, cidade, _cancer):
    return [f"O Escudo possui uma etapa analítica de faixa etária, mas essa informação "
            f"não está exposta pela inteligência central desta versão do chat para {cidade}.",
            "Não vou inventar uma faixa etária a partir de dados que não foram fornecidos ao chat."],            "A faixa etária pode ser incorporada como ferramenta do mesmo núcleo de inteligência."


def fatos_incidencia(_serie, cidade, _cancer):
    return [f"O Escudo não calcula incidência de câncer em {cidade}.",
            "A base principal usada pelo chat é o SIH/SUS, que registra internações hospitalares. "
            "Internações não equivalem a casos novos nem permitem, sozinhas, calcular incidência populacional."],            "Para incidência, seria necessário integrar outra fonte e denominadores populacionais adequados."


def sinais_de_atencao(serie, codigo):
    dados = serie_doenca(serie, codigo)
    comp = comparar_com_estado(serie, codigo)
    sinais = []
    if comp["ritmo_municipio"] >= 3:
        sinais.append(f"internações crescem {formatar_numero(comp['ritmo_municipio'], 1)}% ao ano")
    if comp["ritmo_estado"] is not None and comp["ritmo_municipio"] - comp["ritmo_estado"] > 1.5:
        sinais.append(f"cresce mais rápido que o Estado ({formatar_numero(comp['ritmo_estado'], 1)}% ao ano)")
    taxa, obitos, _ = _taxa(serie, codigo, "MUNICIPIO", "obitos")
    taxa_sp, _, _ = _taxa(serie, codigo, GRUPO_ESTADO, "obitos")
    if obitos >= 5 and taxa_sp > 0 and taxa > taxa_sp * 1.2:
        sinais.append(f"letalidade hospitalar de {formatar_numero(taxa * 100, 1)}%, acima do Estado "
                      f"({formatar_numero(taxa_sp * 100, 1)}%)")
    ano_fim = int(dados["ano"].max())
    recentes = anos_fora_do_padrao(dados)
    recentes = recentes[(recentes["direcao"] == "acima") &
                        (recentes["ano"] >= ano_fim - 2) &
                        (recentes["ano"] < ano_fim)]
    for _, linha in recentes.iterrows():
        sinais.append(f"{linha['ano']} ficou acima do esperado")
    return sinais


def fatos_atencao(serie, cidade, cancer):
    canceres = [cancer] if cancer else list(resumo_doencas(serie)["tipo_cancer"])
    avaliados = [(sinais_de_atencao(serie, c), c) for c in canceres]
    com_sinal = [(s, c) for s, c in avaliados if s]
    fatos = ["Sinais observáveis nos dados que podem merecer investigação ou entrar "
             "na discussão de planejamento; não são uma ordem de gasto."]
    for sinais, codigo in com_sinal:
        fatos.append(f"{nome_doenca(codigo)}: " + "; ".join(sinais) + ".")
    if not com_sinal:
        fatos.append("Nenhum dos critérios atuais produziu um sinal de atenção.")
    fatos.append("A decisão de recursos precisa considerar também orçamento, filas, capacidade instalada "
                 "e outras informações que não estão nesta base.")
    alerta = _alerta_estado(serie)
    if alerta:
        fatos.append(alerta)
    return fatos, "Veja as tendências e os anos atípicos para investigar os sinais."


def fatos_metodo(serie, cidade, _cancer):
    return [
        f"Fonte: internações do SUS (SIH/SUS, DATASUS) de mulheres residentes em {cidade}, "
        f"{int(serie['ano'].min())}–{int(serie['ano'].max())}.",
        "Internação não é caso novo: a mesma mulher pode ter mais de uma AIH.",
        "O ano usado é o de competência/processamento da AIH.",
        "Tendência e projeção são cálculos estatísticos; o Gemini apenas redige a explicação.",
        "Ano fora do padrão indica um ponto para investigação, não uma causa comprovada.",
        "Valores financeiros são valores hospitalares registrados nas AIHs, não todo o gasto público em saúde.",
    ], "Veja também 'Como ler estes dados' no painel."


CALCULOS = {
    "PANORAMA": fatos_panorama,
    "EVOLUCAO": fatos_evolucao,
    "ESTADO": fatos_estado,
    "FORA_PADRAO": fatos_fora_padrao,
    "PROJECAO": fatos_projecao,
    "MORTALIDADE": fatos_mortalidade,
    "CUSTO": fatos_custo,
    "PERMANENCIA": fatos_permanencia,
    "IDADE": fatos_idade,
    "INCIDENCIA": fatos_incidencia,
    "ATENCAO": fatos_atencao,
    "METODO": fatos_metodo,
}


def calcular(entendido, serie, cidade):
    resultados = []
    cancer = entendido["cancer"]
    if cancer is None and entendido["assunto"] == "EVOLUCAO":
        cancer = entendido["cancer_em_foco"]

    for assunto in entendido["assuntos"]:
        if assunto == "EVOLUCAO":
            fn = fatos_evolucao if cancer else fatos_panorama
            fatos, onde = fn(serie, cidade, cancer, entendido["ano"]) if cancer else fn(serie, cidade, None)
        else:
            fn = CALCULOS.get(assunto, fatos_panorama)
            fatos, onde = fn(serie, cidade, cancer)
        resultados.append((assunto, fatos, onde))

    fatos_finais = []
    onde_finais = []
    for assunto, fatos, onde in resultados:
        if len(resultados) > 1:
            fatos_finais.append(f"[{assunto}]")
        fatos_finais.extend(fatos)
        if onde:
            onde_finais.append(onde)

    return fatos_finais, " ".join(dict.fromkeys(onde_finais))


def resposta_direta(fatos, onde_ver):
    if not fatos:
        return "Não encontrei informação suficiente na base para responder."
    texto = fatos[0]
    if len(fatos) > 1:
        texto += "\n\n" + "\n".join(f"- {f}" for f in fatos[1:])
    if onde_ver:
        texto += f"\n\n_{onde_ver}_"
    return texto


def montar_memoria(historico, pergunta, contexto):
    itens = []
    for item in (historico or [])[-6:]:
        if not isinstance(item, dict):
            continue
        itens.append({
            "pergunta": item.get("pergunta", ""),
            "assunto": item.get("assunto", ""),
            "cancer": item.get("contexto", {}).get("cancer"),
            "ano": item.get("contexto", {}).get("ano"),
        })
    itens.append({
        "pergunta": pergunta,
        "assunto": contexto.get("assunto"),
        "cancer": contexto.get("cancer"),
        "ano": contexto.get("ano"),
    })
    return itens


def responder(pergunta, serie, cidade, cancer_em_foco=None, perfil="SIMPLES",
              explicar=None, historico=None):
    disponiveis = set(serie["tipo_cancer"].unique())
    entendido = entender(pergunta, disponiveis, cancer_em_foco, historico)
    fatos, onde_ver = calcular(entendido, serie, cidade)

    if explicar is None:
        try:
            from ia_linguagem import responder_com_ia as explicar
        except Exception:
            explicar = None

    contexto = "\n".join(f"- {f}" for f in fatos)
    memoria = montar_memoria(historico, pergunta, entendido)

    texto = None
    usou_ia = False
    if explicar is not None:
        try:
            texto = explicar(pergunta, contexto, perfil, memoria=memoria)
            usou_ia = bool(texto and texto.strip())
        except TypeError:
            # Compatibilidade com a assinatura antiga.
            try:
                texto = explicar(pergunta, contexto, perfil)
                usou_ia = bool(texto and texto.strip())
            except Exception:
                texto = None
        except Exception:
            texto = None

    if not usou_ia:
        texto = resposta_direta(fatos, onde_ver)
    elif onde_ver:
        texto = texto.strip() + f"\n\n_{onde_ver}_"

    contexto_salvar = {
        "assunto": entendido["assunto"],
        "assuntos": entendido["assuntos"],
        "cancer": entendido["cancer"] or entendido["cancer_em_foco"],
        "ano": entendido["ano"],
    }

    return {
        "texto": texto,
        "assunto": entendido["assunto"],
        "assuntos": entendido["assuntos"],
        "cancer": entendido["cancer"] or entendido["cancer_em_foco"],
        "fatos": fatos,
        "usou_ia": usou_ia,
        "contexto": contexto_salvar,
        "memoria": memoria,
    }


def registrar_pergunta(banco, pergunta, assunto):
    try:
        import sqlite3
        conn = sqlite3.connect(banco)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS perguntas_usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_hora TEXT, pergunta TEXT, categoria TEXT, reconhecida TEXT
                )
            """)
            conn.execute(
                "INSERT INTO perguntas_usuarios "
                "(data_hora, pergunta, categoria, reconhecida) VALUES (?, ?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pergunta, assunto, "SIM"),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
