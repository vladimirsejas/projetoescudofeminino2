from lia import INICIO, Resposta

# =====================================
# APOIO À MULHER — "Encontre um caminho" (combinado com o autor, 09/2026)
#
# Outras lâminas, SEPARADAS do painel de estudo da doença
# (dashboard/app.py continua igual). Aqui a pergunta é outra: "onde a
# mulher encontra ajuda?". A lógica, de cima para baixo:
#   Estado de SP (portal da Saúde, rede oncológica, regulação,
#   carretas) -> o que é útil de verdade para a mulher -> a Lia
#   apresenta, por caminhos (Prevenir, Descobrir, Tratar...).
# Cidades NÃO viram lâmina própria: Campinas, Ribeirão Preto, Rio
# Preto e Piracicaba são fontes de itens que entram nos caminhos. Só
# duas exceções, combinadas com o autor: Rio Claro (a cidade do
# trabalho, com mais detalhe) e Barretos (Hospital de Amor).
#
# Regras deste catálogo:
#   - cada item tem FONTE (página oficial), data em que foi conferido
#     e, quando for o caso, o que ainda falta confirmar ("confirmar");
#   - nada de endereço, telefone ou regra inventada; na dúvida, o item
#     sai ou entra marcado para confirmar;
#   - cada item tem UMA casa (a lâmina dele); os caminhos só apontam
#     para os itens de Rio Claro e Barretos, sem repetir;
#   - a Lia não é médica: mostra onde procurar; quem orienta o caso é
#     a equipe de saúde. As falas são montadas daqui, sem IA.
# Pesquisa feita em 24/09/2026 pela busca na web (trechos das páginas
# oficiais); o ambiente de trabalho não abria os sites do governo, por
# isso vários itens pedem confirmação na própria página.
# =====================================

CONFERIDO = "24/09/2026"
CIDADE = "Rio Claro"
REGIAO = "DRS X Piracicaba / RRAS 14"

LAMINAS = {"caminho": "Encontre um caminho", "rio_claro": "Rio Claro", "barretos": "Barretos",
           "sobre": "Sobre estas informações"}

# (id, rótulo, o que tem dentro, frase da Lia ao abrir)
CAMINHOS = [
    ("prevenir", "Prevenir", "mamografia, preventivo e vacina",
     "Prevenir é o começo de tudo: exames que acham o câncer cedo e a vacina que evita o do colo do útero."),
    ("descobrir", "Descobrir", "exame alterado ou suspeita",
     "Quando um exame vem alterado ou há suspeita, o caminho passa pela unidade de saúde e pela regulação."),
    ("tratar", "Tratar", "rede oncológica e direitos",
     "Com o diagnóstico confirmado, o tratamento pelo SUS acontece nos hospitais habilitados da rede."),
    ("acompanhar", "Acompanhar", "fila da oncologia",
     "Quem aguarda a consulta especializada pode acompanhar a própria fila."),
    ("ir_ate_voce", "Ir até você", "carretas e unidades móveis",
     "Às vezes o exame vai até a mulher: carretas e unidades móveis circulam pelo Estado."),
    ("referencia", "Encontrar referência", "hospitais especializados",
     "Estes são hospitais e centros de referência que a pesquisa encontrou na rede do Estado."),
    ("cuidar", "Cuidar", "saúde da mulher nas cidades",
     "Algumas cidades têm serviços próprios de saúde da mulher. Valem para quem mora nelas."),
    ("proteger", "Proteger", "violência contra a mulher",
     "Se você está em situação de violência, não precisa passar por isso sozinha. Estes canais atendem."),
]
NOME_CAMINHO = {c: r for c, r, _, _ in CAMINHOS}
JORNADA = ["prevenir", "descobrir", "tratar", "acompanhar"]  # a ordem da jornada


def _item(id, caminho, lamina, onde, titulo, resumo, fonte, link, para_quem=None, como=None, levar=None,
          contato=None, confirmar=None, cuidado=None):
    return {"id": id, "caminho": caminho, "lamina": lamina, "onde": onde, "titulo": titulo, "resumo": resumo,
            "para_quem": para_quem, "como": como, "levar": levar, "contato": contato, "fonte": fonte,
            "link": link, "confirmar": confirmar, "cuidado": cuidado}


ITENS = [
    # ---------------- PREVENIR ----------------
    _item("mulheres_de_peito", "prevenir", "caminho", "Estado de SP",
          "Mamografia gratuita pelo Programa Mulheres de Peito",
          "mamografia gratuita em mais de 300 serviços do Estado; de 50 a 69 anos, sem pedido médico",
          "Governo do Estado de SP (Programa Mulheres de Peito) e Poupatempo",
          "https://www.poupatempo.sp.gov.br/carta/4CC55F40-E724-4158-BD99-EE33B4D9B29E",
          para_quem="Foco nas mulheres de 50 a 69 anos, que não precisam de pedido médico.",
          como="Agendar pela central da Secretaria da Saúde, 0800 779 0000 (segunda a sexta, 8h às 17h), ou pelo "
               "Poupatempo (site ou aplicativo). O exame é feito em AMEs, hospitais estaduais e clínicas conveniadas.",
          confirmar="A página do programa que a busca mostrou não tinha data visível: confirme o telefone e a faixa "
                    "de idade ao agendar."),
    _item("colo_utero", "prevenir", "caminho", "SUS (todo o Brasil)",
          "Exame preventivo do colo do útero (Papanicolau e teste de DNA-HPV)",
          "de 25 a 64 anos, na unidade de saúde; o teste de DNA-HPV está substituindo o Papanicolau aos poucos",
          "Ministério da Saúde",
          "https://www.gov.br/saude/pt-br/assuntos/noticias/2025/agosto/ministerio-da-saude-oferta-tecnologia-"
          "inovadora-100-nacional-para-detectar-cancer-do-colo-do-utero-no-sus",
          para_quem="Mulheres de 25 a 64 anos.",
          como="Na unidade de saúde do bairro (UBS ou USF). O SUS está trocando, aos poucos, o Papanicolau pelo teste "
               "de DNA-HPV, que é mais sensível; São Paulo está entre os estados que já têm o teste. Com o teste de "
               "DNA-HPV negativo, o próximo exame é em 5 anos.",
          confirmar="A troca é gradual: pergunte na sua unidade qual exame ela faz hoje."),
    _item("vacina_hpv", "prevenir", "caminho", "SUS (todo o Brasil)",
          "Vacina contra o HPV",
          "dose única de 9 a 14 anos; protege contra o vírus que causa o câncer do colo do útero",
          "Ministério da Saúde",
          "https://www.gov.br/saude/pt-br/assuntos/noticias/2025/dezembro/ministerio-da-saude-amplia-prazo-de-"
          "resgate-vacinal-contra-hpv-para-jovens-de-15-a-19-anos-ate-2026",
          para_quem="Meninas e meninos de 9 a 14 anos, em dose única. Houve um resgate para jovens de 15 a 19 anos "
                    "não vacinados, prorrogado até o 1º semestre de 2026.",
          como="Nas unidades de saúde (e em ações em escolas e outros locais).",
          confirmar="Confirme na unidade se o resgate de 15 a 19 anos ainda está valendo."),

    # ---------------- DESCOBRIR ----------------
    _item("caminho_do_exame", "descobrir", "caminho", "Estado de SP",
          "O caminho do exame pelo SUS começa na unidade de saúde",
          "consulta na unidade → pedido do exame → regulação do município agenda o serviço",
          "Secretaria de Estado da Saúde de SP",
          "https://saude.sp.gov.br/coordenadoria-de-controle-de-doencas/noticias/10102024-outubro-rosa-veja-como-"
          "agendar-exame-de-mamografia-em-sp-de-forma-gratuita",
          como="Procure a UBS mais próxima e passe por uma consulta. Se o exame for indicado, o encaminhamento é "
               "feito no sistema de regulação do município, que agenda o serviço."),
    _item("lei_30_dias", "descobrir", "caminho", "SUS (todo o Brasil)",
          "Direito: exames de diagnóstico em até 30 dias",
          "com suspeita de câncer, os exames que confirmam o diagnóstico devem sair em até 30 dias",
          "Lei federal 13.896/2019 (Câmara dos Deputados)",
          "https://www2.camara.leg.br/legin/fed/lei/2019/lei-13896-30-outubro-2019-789326-norma-pl.html",
          para_quem="Pessoas com suspeita de câncer atendidas no SUS.",
          como="A lei garante que os exames necessários para confirmar o diagnóstico sejam feitos em até 30 dias, "
               "contados do pedido médico."),
    _item("mater_ribeirao", "descobrir", "caminho", "Ribeirão Preto",
          "MATER – Centro de Referência da Saúde da Mulher",
          "mamografia alterada vai rápido para biópsia; atende os 26 municípios da região de Ribeirão Preto",
          "MATER / FAEPA – HC da Faculdade de Medicina de Ribeirão Preto (USP)",
          "https://mater.faepa.br/",
          para_quem="Mulheres com alteração na mama dos 26 municípios da região de Ribeirão Preto.",
          como="Encaminhamento rápido de mamografias alteradas para biópsia, tratamento dos casos benignos e "
               "encaminhamento ao serviço de referência quando o câncer se confirma. O acesso é pela rede pública da "
               "região.",
          contato="Rua Wanderley Taffo, 330 – Quintino Facci II, Ribeirão Preto.",
          cuidado="Vale para a região de Ribeirão Preto; quem mora em outra região segue a referência da sua."),

    # ---------------- TRATAR ----------------
    _item("lei_60_dias", "tratar", "caminho", "SUS (todo o Brasil)",
          "Direito: começar o tratamento em até 60 dias",
          "com o câncer confirmado, o tratamento pelo SUS deve começar em até 60 dias do laudo",
          "Lei federal 12.732/2012 (Planalto)",
          "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12732.htm",
          para_quem="Pacientes com câncer diagnosticado no SUS.",
          como="A lei dá prazo máximo de 60 dias, contados do laudo patológico, para começar o tratamento (cirurgia, "
               "quimioterapia ou radioterapia). Somada à lei dos 30 dias, da suspeita ao início do tratamento são no "
               "máximo 90 dias."),
    _item("rede_oncologica", "tratar", "caminho", "Estado de SP",
          "Rede de Atenção Oncológica do Estado de São Paulo",
          "a lista oficial dos hospitais habilitados para tratar câncer pelo SUS, por região",
          "Fundação Oncocentro de São Paulo (FOSP)",
          "https://fosp.saude.sp.gov.br/fosp/diretoria-adjunta-de-informacao-e-epidemiologia/rede-de-atencao-"
          "oncologica-do-estado-de-sao-paulo/",
          como="Os hospitais são habilitados como CACON (alta complexidade) ou UNACON, com ou sem radioterapia e "
               "hematologia. O acesso é pela regulação: a unidade de saúde ou o especialista encaminha. A lista "
               "serve para saber quais são as referências da sua região."),

    # ---------------- ACOMPANHAR ----------------
    _item("lista_regulacao", "acompanhar", "caminho", "Estado de SP",
          "Lista de Regulação de Oncologia",
          "quem aguarda a consulta especializada em oncologia pelo SUS-SP consulta a própria fila",
          "Secretaria de Estado da Saúde de SP e Poupatempo (Lei estadual 17.745/2023)",
          "https://servicos.sp.gov.br/fcarta/4F97BB19-93B6-4198-A5C2-ED4265E7F724",
          para_quem="Pacientes com diagnóstico ou suspeita forte de câncer, atendidas no SUS-SP, que aguardam o "
                    "agendamento da consulta especializada em oncologia.",
          como="Consultar pelo Poupatempo (site ou aplicativo) ou pelo portal Saúde Digital da Secretaria "
               "(saudedigital.saude.sp.gov.br). A lista traz os pedidos registrados no SIRESP, o sistema de "
               "regulação usado pelo Estado e pelos municípios.",
          levar="Nenhum documento; é gratuito e na hora."),

    # ---------------- IR ATÉ VOCÊ ----------------
    _item("carretas_estado", "ir_ate_voce", "caminho", "Estado de SP",
          "Carretas da Mamografia (Programa Mulheres de Peito)",
          "a partir de 35 anos, sem mamografia nos últimos 12 meses; itinerário no Poupatempo",
          "Poupatempo / Secretaria de Estado da Saúde de SP",
          "https://www.poupatempo.sp.gov.br/carta/B7ED6C20-6D1B-481B-8693-35AD62D16E42",
          para_quem="Mulheres a partir de 35 anos que não fizeram mamografia nos últimos 12 meses.",
          levar="De 50 a 74 anos: RG e cartão SUS. De 35 a 49 e acima de 74 anos: também o pedido médico do SUS.",
          como="Consultar o itinerário no Poupatempo (site ou aplicativo). Atendimento de segunda a sexta, das 8h às "
               "17h, e aos sábados, das 8h às 12h, com senhas limitadas. Gratuito.",
          confirmar="O itinerário muda todo mês: consulte antes de ir."),

    # ---------------- ENCONTRAR REFERÊNCIA ----------------
    _item("santa_casa_piracicaba", "referencia", "caminho", "Piracicaba (região de Rio Claro)",
          "Santa Casa de Piracicaba",
          "UNACON com radioterapia, na mesma região de saúde de Rio Claro",
          "FOSP – boletim da RRAS 14 (DRS Piracicaba)",
          "https://fosp.saude.sp.gov.br/wp-content/uploads/Boletim-RRAS14.pdf",
          como="Hospital habilitado como UNACON com serviço de radioterapia. Faz parte da RRAS 14, a mesma de Rio "
               "Claro. O acesso é pela regulação do SUS."),
    _item("fornecedores_cana", "referencia", "caminho", "Piracicaba (região de Rio Claro)",
          "Hospital dos Fornecedores de Cana de Piracicaba",
          "UNACON com radioterapia e hematologia, na mesma região de saúde de Rio Claro",
          "FOSP – boletim da RRAS 14 (DRS Piracicaba)",
          "https://fosp.saude.sp.gov.br/wp-content/uploads/Boletim-RRAS14.pdf",
          como="Hospital habilitado como UNACON com radioterapia e hematologia. Faz parte da RRAS 14, a mesma de Rio "
               "Claro. O acesso é pela regulação do SUS."),
    _item("santa_casa_limeira", "referencia", "caminho", "Limeira (região de Rio Claro)",
          "Santa Casa de Limeira",
          "citada como UNACON com radioterapia na região de Rio Claro (a confirmar)",
          "FOSP – boletim da RRAS 14 (DRS Piracicaba)",
          "https://fosp.saude.sp.gov.br/wp-content/uploads/Boletim-RRAS14.pdf",
          como="O acesso é pela regulação do SUS.",
          confirmar="Não consegui abrir o boletim da FOSP inteiro para confirmar a habilitação de Limeira."),
    _item("caism_unicamp", "referencia", "caminho", "Campinas",
          "CAISM Unicamp – Hospital da Mulher",
          "maior hospital de saúde da mulher do interior; câncer ginecológico e de mama; só SUS",
          "CAISM – Unicamp",
          "https://www2.caism.unicamp.br/",
          como="Atende só pelo SUS. Tem ambulatórios de oncologia ginecológica (vulva, vagina, colo e corpo do útero, "
               "ovário) e de mastologia, referência para Campinas e região. As consultas são agendadas pelas "
               "unidades básicas de saúde e pela rede pública.",
          cuidado="Campinas é outra região de saúde: para quem mora em Rio Claro, o caminho normal é a referência "
                  "da própria região."),
    _item("hospital_base_rio_preto", "referencia", "caminho", "São José do Rio Preto",
          "Hospital de Base – Centro de Oncologia",
          "um dos hospitais que mais diagnosticam câncer no Estado; atende SUS com encaminhamento",
          "Hospital de Base de São José do Rio Preto",
          "https://hospitaldebase.com.br/servicos/centro-de-oncologia",
          como="Atende gratuitamente pacientes do SUS encaminhados pela unidade básica de saúde da cidade de origem, "
               "pela Central de Agendamento de Consultas. Equipe com médicos, enfermagem, farmácia, serviço social, "
               "psicologia, nutrição e outras áreas.",
          cuidado="É referência da região de Rio Preto; quem mora em outra região segue a referência da sua."),

    # ---------------- CUIDAR ----------------
    _item("sp_por_todas", "cuidar", "caminho", "Estado de SP",
          "SP por Todas – serviços para mulheres",
          "portal do Estado com serviços de saúde, proteção e autonomia para mulheres",
          "Governo do Estado de SP (Agência SP)",
          "https://www.spportodas.sp.gov.br/sp-por-todas/saude/outubrorosa",
          como="Reúne, num lugar só, serviços estaduais para mulheres: saúde (como o Outubro Rosa), proteção e "
               "autonomia."),
    _item("piracicaba_cesm", "cuidar", "caminho", "Piracicaba",
          "Centro Especializado em Saúde da Mulher (CESM) e mamografia agendada online",
          "Piracicaba agenda mamografia pela internet e ampliou o rastreamento para 40 a 49 anos",
          "Prefeitura de Piracicaba",
          "https://piracicaba.sp.gov.br/noticias/piracicaba-atualiza-recomendacoes-para-acesso-a-mamografia-e-"
          "amplia-faixa-etaria-de-rastreamento/",
          para_quem="Moradoras de Piracicaba.",
          como="O programa municipal de saúde da mulher é coordenado pelo CESM. Desde 2024 a mamografia pode ser "
               "agendada online (sistema SISS Saúde); mulheres de 40 a 49 anos têm acesso ao exame com avaliação "
               "profissional. Há também uma unidade móvel de saúde da mulher."),
    _item("campinas_craim", "cuidar", "caminho", "Campinas",
          "Mamografia em Campinas: CRAIM e agendamento pelo 160",
          "no Outubro Rosa de 2025, moradoras agendaram mamografia pelo Disque Saúde 160, sem pedido médico",
          "Prefeitura de Campinas",
          "https://www.campinas.sp.gov.br/governo/saude/atencao-a-saude/saudeDaMulher_protocolos_espec_mamografia.php",
          para_quem="Moradoras de Campinas: de 40 a 49 anos com o último exame há mais de 1 ano e de 50 a 74 com o "
                    "último há mais de 2 anos (regra da campanha de 2025).",
          como="Agendamento pelo Disque Saúde 160. Exames no Centro de Referência e de Assistência Integral à Mulher "
               "(CRAIM), no CAISM Unicamp, em clínica conveniada e na carreta do Hospital de Amor.",
          confirmar="Regra da campanha de outubro de 2025: veja se há campanha neste ano."),
    _item("ribeirao_agendamento", "cuidar", "caminho", "Ribeirão Preto",
          "Mamografia agendada pelo site da Prefeitura de Ribeirão Preto",
          "moradoras de 50 a 69 anos sem mamografia há 2 anos ou mais agendam pela internet",
          "Prefeitura de Ribeirão Preto",
          "https://www.ribeiraopreto.sp.gov.br/portal/sassom/prevencao-cancer-mama",
          para_quem="Moradoras de Ribeirão Preto de 50 a 69 anos sem mamografia há 2 anos ou mais.",
          como="Agendar no site da Prefeitura; quem não conseguir pode pedir na unidade de saúde mais próxima."),
    _item("rio_preto_mamografia", "cuidar", "caminho", "São José do Rio Preto",
          "Mamografia de rastreamento em Rio Preto a partir dos 40 anos",
          "pedido na UBS; rastreamento a cada 2 anos para mulheres a partir de 40 anos",
          "Prefeitura de São José do Rio Preto (Secretaria de Saúde)",
          "https://www.riopreto.sp.gov.br/secretarias/saude",
          para_quem="Moradoras de São José do Rio Preto a partir de 40 anos.",
          como="O pedido é feito na UBS, e o médico emite a guia de agendamento na rede pública.",
          confirmar="A regra dos 40 anos veio de uma portaria citada na busca: confirme na UBS."),

    # ---------------- PROTEGER ----------------
    _item("ligue_180", "proteger", "caminho", "Todo o Brasil",
          "Ligue 180 – Central de Atendimento à Mulher",
          "gratuito, 24 horas, todos os dias; também por WhatsApp. Em perigo agora: ligue 190",
          "Ministério das Mulheres",
          "https://www.gov.br/mulheres/pt-br/ligue180",
          como="Orienta sobre leis, direitos e serviços da rede, registra denúncias e encaminha aos órgãos "
               "competentes. Em perigo imediato, ligue 190 (Polícia Militar).",
          contato="Telefone 180; WhatsApp (61) 9610-0180."),
    _item("sp_mulher_segura", "proteger", "caminho", "Estado de SP",
          "Aplicativo SP Mulher Segura",
          "boletim de ocorrência, pedido de medida protetiva e botão do pânico pelo celular",
          "Governo do Estado de SP (Agência SP)",
          "https://www.agenciasp.sp.gov.br/sp-mulher-segura-conheca-o-aplicativo-que-permite-denunciar-violencia-"
          "domestica-e-acionar-botao-do-panico-contra-agressores/",
          como="Permite registrar boletim de ocorrência, pedir medida protetiva de urgência e, para quem já tem "
               "medida protetiva, acionar o botão do pânico, que envia a localização em tempo real. Android e iOS; "
               "entra com a conta gov.br."),
    _item("delegacia_eletronica", "proteger", "caminho", "Estado de SP",
          "Delegacia Eletrônica – violência doméstica contra a mulher",
          "registrar ocorrência pela internet, 24 horas, e pedir medida protetiva",
          "Polícia Civil do Estado de SP",
          "https://www.delegaciaeletronica.policiacivil.sp.gov.br/",
          como="Em \"Comunicar Ocorrência\", escolher \"Violência Doméstica Contra Mulher\". Dá para anexar fotos e "
               "mensagens e pedir medida protetiva de urgência no mesmo formulário."),

    # ================ LÂMINA RIO CLARO (a cidade do trabalho) ================
    _item("rc_unidades", "prevenir", "rio_claro", "Rio Claro",
          "Unidades de Saúde da Família (USF) e UBS",
          "a porta de entrada: preventivo do colo do útero, exame das mamas e pré-natal",
          "Fundação Municipal de Saúde de Rio Claro",
          "https://www.saude-rioclaro.org.br/enderecos.htm",
          para_quem="Moradoras de Rio Claro.",
          como="A Prefeitura informa 17 Unidades de Saúde da Família e 4 UBS, das 7h às 17h. A consulta é marcada "
               "na própria unidade, que é onde se faz o preventivo e se pede a mamografia. Algumas equipes têm "
               "ginecologista.",
          confirmar="O número de unidades e o horário vêm de páginas antigas da Prefeitura: confira a lista de "
                    "endereços."),
    _item("rc_central_vagas", "descobrir", "rio_claro", "Rio Claro",
          "Central de Vagas da Fundação Municipal de Saúde (mamografia com pedido médico)",
          "com o pedido médico em mãos, a mamografia é agendada na Central de Vagas",
          "Fundação Municipal de Saúde de Rio Claro (informativo)",
          "https://www.saude-rioclaro.org.br/informativos/Rio%20Claro%20faz%20agendamento%20de%20exame%20de%20mama.htm",
          levar="O pedido médico.",
          contato="Rua 10, esquina com a Via da Saudade. Telefones 3524-1463 e 3534-0026. Segunda a sexta, das 7h "
                  "às 16h.",
          confirmar="É um informativo antigo da Fundação: confirme endereço, telefones e se o agendamento ainda é "
                    "feito ali."),
    _item("rc_carreta_hospital_de_amor", "ir_ate_voce", "rio_claro", "Rio Claro",
          "Carreta do Hospital de Amor em Rio Claro",
          "ação com a Prefeitura: mamografia (40 a 69 anos) e Papanicolau (25 a 65), com agendamento nas USF",
          "Prefeitura de Rio Claro",
          "https://rioclaro.sp.gov.br/fundacao-de-saude/rc-faz-300-exames-de-papanicolau-e-mamografia-em-carreta-"
          "do-hospital-do-amor/",
          como="Na ação noticiada foram 180 vagas de mamografia para mulheres de 40 a 69 anos e 120 de Papanicolau "
               "para 25 a 65 anos, com agendamento prévio nas Unidades de Saúde da Família.",
          confirmar="Foi uma ação com data marcada, não um serviço fixo: pergunte na sua USF se haverá nova vinda."),
    _item("rc_santa_casa", "tratar", "rio_claro", "Rio Claro",
          "Santa Casa de Rio Claro – oncologia (UNACON) e Centro Oncológico Santa Ágata",
          "hospital habilitado para tratar câncer pelo SUS na própria cidade",
          "FOSP (boletim da RRAS 14) e Santa Casa de Rio Claro",
          "https://www.santacasaderioclaro.com.br/",
          como="Habilitada como UNACON. O Centro Oncológico Santa Ágata tem 24 poltronas de quimioterapia, 6 leitos e "
               "11 consultórios. É referência em câncer de cabeça e pescoço para os 26 municípios da DRS X. O acesso "
               "pelo SUS é pela regulação (encaminhamento da unidade ou do especialista)."),
    _item("rc_cram", "proteger", "rio_claro", "Rio Claro",
          "Centro de Referência de Atendimento à Mulher (CRAM) Dona Ângela Gonzaga",
          "acolhimento e orientação para mulheres, das 8h às 17h",
          "Prefeitura de Rio Claro (Desenvolvimento Social)",
          "https://rioclaro.sp.gov.br/desenvolvimento-social/casa-aberta-no-centro-de-referencia-de-atendimento-a-"
          "mulher/",
          contato="Rua 17, nº 30 (anexo ao Centro Social Urbano \"Mitiko Nevoeiro\"), entre as avenidas 23 e 35. "
                  "Telefones 3532-4014 e 3525-1366. Das 8h às 17h.",
          confirmar="Endereço e telefones vêm de uma página da Prefeitura sem data visível na busca."),

    # ================ LÂMINA BARRETOS (Hospital de Amor) ================
    _item("ha_quem_e", "referencia", "barretos", "Barretos",
          "Hospital de Amor (Fundação Pio XII)",
          "hospital filantrópico dedicado ao câncer, fundado em 1962 em Barretos; atende pelo SUS",
          "Hospital de Amor",
          "https://hospitaldeamor.com.br/conheca-mais-sobre-nossa-historia/",
          como="Hospital filantrópico mantido pela Fundação Pio XII, dedicado à prevenção e ao tratamento do câncer, "
               "com unidades em várias regiões do Brasil. O atendimento é gratuito pelo SUS.",
          confirmar="A habilitação como CACON aparece na rede estadual, mas não consegui abrir a lista da FOSP para "
                    "confirmar."),
    _item("ha_prevencao", "prevenir", "barretos", "Barretos",
          "Prevenção do Hospital de Amor",
          "Instituto de Prevenção em Barretos e unidades fixas de prevenção, inclusive em Campinas",
          "Hospital de Amor",
          "https://hospitaldeamor.com.br/prevencao/",
          para_quem="Mulheres de 40 a 69 anos nas ações de mamografia.",
          como="O Instituto de Prevenção de Barretos faz mamografia, Papanicolau, exame da boca, teste FIT (intestino) "
               "e teledermatologia (pele). Há unidades fixas de prevenção no Estado em Barretos, Campinas e "
               "Fernandópolis.",
          confirmar="Os detalhes do Instituto vieram de reportagem: confirme na página de Prevenção do hospital."),
    _item("ha_moveis", "ir_ate_voce", "barretos", "Barretos",
          "Unidades móveis do Hospital de Amor",
          "carretas que percorrem o país em ações com as prefeituras; já estiveram em Rio Claro",
          "Hospital de Amor",
          "https://hospitaldeamor.com.br/prevencao/",
          para_quem="Mulheres de 40 a 69 anos.",
          como="As unidades móveis chegam por parceria com a prefeitura. Para agendar, procure a unidade de saúde "
               "mais próxima.",
          levar="Cópia do RG, CPF, cartão SUS e comprovante de residência."),
    _item("ha_primeiro_atendimento", "tratar", "barretos", "Barretos",
          "Primeiro atendimento no Hospital de Amor",
          "com o câncer confirmado por exame, o primeiro agendamento é feito com os documentos pelo WhatsApp",
          "Hospital de Amor",
          "https://hospitaldeamor.com.br/primeiro-atendimento/",
          levar="Encaminhamento médico, cópia da biópsia, exames realizados, cartão SUS, RG, CPF e comprovante de "
                "residência. Os exames precisam confirmar o tumor maligno.",
          como="Os pacientes chegam encaminhados pela rede pública dos 18 municípios do DRS de Barretos ou pelos "
               "próprios serviços do hospital, conforme os fluxos do SUS.",
          contato="Documentos pelo WhatsApp (17) 3321-5403; dúvidas pelo (17) 3321-5400. Segunda a quinta, 8h às "
                  "17h; sexta, 8h às 16h.",
          cuidado="Para quem mora em Rio Claro, o caminho do SUS passa primeiro pela referência da própria região "
                  "(RRAS 14). Converse com a equipe que acompanha você."),
]
POR_ID = {i["id"]: i for i in ITENS}


def itens(caminho=None, lamina=None):
    return [i for i in ITENS if (caminho is None or i["caminho"] == caminho)
            and (lamina is None or i["lamina"] == lamina)]


# ---------- ações (o que um botão faz) ----------

def caminho(id):
    return {"tipo": "apoio_caminho", "id": id}


def item(id):
    return {"tipo": "apoio_item", "id": id}


def lamina(id):
    return {"tipo": "apoio_lamina", "id": id}


SOBRE = {"tipo": "apoio_sobre"}

AVISO = (f"Conferi em {CONFERIDO} nas páginas oficiais. Regras, endereços e telefones mudam: confirme antes de "
         "ir. Eu não sou médica; quem orienta o seu caso é a equipe de saúde.")


def _proximo(c):
    """O próximo passo da jornada (Prevenir → Descobrir → Tratar → Acompanhar)."""
    if c in JORNADA and JORNADA.index(c) < len(JORNADA) - 1:
        seguinte = JORNADA[JORNADA.index(c) + 1]
        return [(f"Próximo passo: {NOME_CAMINHO[seguinte]}", caminho(seguinte))]
    return []


def _nas_laminas(c):
    """Os itens de Rio Claro e Barretos deste caminho: a casa deles é a
    lâmina própria; aqui o caminho só aponta (sem repetir o texto)."""
    return [i for i in ITENS if i["caminho"] == c and i["lamina"] in ("rio_claro", "barretos")]


def saudacao():
    return Resposta(
        fala=f"Você está em **{CIDADE}**. O que você precisa? Escolha um caminho e eu mostro onde procurar, "
             "com as páginas oficiais.",
        expressao="acolhedora",
        botoes=[(r, caminho(c)) for c, r, _, _ in CAMINHOS]
        + [("Rio Claro: o que tem aqui", lamina("rio_claro")), ("Barretos: Hospital de Amor", lamina("barretos")),
           ("De onde vêm estas informações?", SOBRE)],
        destino={"aba": LAMINAS["caminho"]},
    )


def responder_caminho(c):
    _, rotulo, _, abertura = next(x for x in CAMINHOS if x[0] == c)
    lista = itens(caminho=c, lamina="caminho")
    fala = f"**{rotulo}.** {abertura}\n\n" + "\n".join(f"- **{i['titulo']}** · {i['onde']}: {i['resumo']}."
                                                        for i in lista)
    apontados = _nas_laminas(c)
    if apontados:
        fala += "\n\nTambém para este caminho: " + "; ".join(
            f"{i['titulo']} (lâmina {LAMINAS[i['lamina']]})" for i in apontados) + "."
    return Resposta(
        fala=fala,
        expressao="acolhedora" if c == "proteger" else "explicando",
        botoes=[(i["titulo"], item(i["id"])) for i in lista + apontados] + _proximo(c),
        destino={"aba": LAMINAS["caminho"], "caminho": c},
        numeros=[f"{i['titulo']}: {i['fonte']}" for i in lista],
    )


def responder_item(id):
    i = POR_ID[id]
    partes = [f"**{i['titulo']}** · {i['onde']}"]
    for rotulo, chave in (("Para quem", "para_quem"), ("O que levar", "levar"), ("Como funciona", "como"),
                          ("Onde e contato", "contato")):
        if i[chave]:
            partes.append(f"**{rotulo}:** {i[chave]}")
    if i["cuidado"]:
        partes.append(f"**Atenção:** {i['cuidado']}")
    if i["confirmar"]:
        partes.append(f"**A confirmar:** {i['confirmar']}")
    partes.append(f"[Abrir a página oficial]({i['link']})")
    partes.append(AVISO)
    return Resposta(
        fala="\n\n".join(partes),
        expressao="cautelosa" if i["confirmar"] else ("acolhedora" if i["caminho"] == "proteger" else "explicando"),
        botoes=[(f"Voltar a {NOME_CAMINHO[i['caminho']]}", caminho(i["caminho"]))] + _proximo(i["caminho"]),
        destino={"aba": LAMINAS[i["lamina"]], "caminho": i["caminho"], "item": id},
        numeros=[f"Fonte: {i['fonte']}", f"Página: {i['link']}", f"Conferido em {CONFERIDO}"],
    )


def responder_lamina(id):
    lista = itens(lamina=id)
    if id == "rio_claro":
        fala = (f"**Rio Claro** é a cidade do trabalho do Escudo. Aqui estão as portas da própria cidade. Rio Claro "
                f"faz parte da **{REGIAO}**: as referências de câncer da região ficam em Rio Claro e em Piracicaba "
                "(caminho Encontrar referência).")
    else:
        fala = ("**Barretos** tem um bloco especial pelo **Hospital de Amor**, que junta prevenção, unidades móveis "
                "e tratamento do câncer. Uma ligação com a nossa cidade: a carreta do hospital já esteve em Rio Claro.")
    fala += "\n\n" + "\n".join(f"- **{i['titulo']}**: {i['resumo']}." for i in lista)
    extra = [("Referências na região de Rio Claro", caminho("referencia"))] if id == "rio_claro" else \
            [("Rio Claro: o que tem aqui", lamina("rio_claro"))]
    return Resposta(
        fala=fala,
        expressao="explicando",
        botoes=[(i["titulo"], item(i["id"])) for i in lista] + extra,
        destino={"aba": LAMINAS[id]},
        numeros=[f"{i['titulo']}: {i['fonte']}" for i in lista],
    )


def responder_sobre():
    pendentes = [i["titulo"] for i in ITENS if i["confirmar"]]
    return Resposta(
        fala=(f"Juntei estas informações em {CONFERIDO}, a partir do portal da Saúde do Estado de SP, da rede "
              "oncológica da FOSP, da Fundação Municipal de Saúde de Rio Claro, das prefeituras de Campinas, "
              "Ribeirão Preto, Rio Preto e Piracicaba e do Hospital de Amor. Cada item traz a página oficial. "
              f"{len(pendentes)} de {len(ITENS)} itens ainda pedem confirmação na própria página: estão marcados. "
              "Isto é um guia de onde procurar, não orientação médica nem garantia de vaga."),
        expressao="pensativa",
        botoes=[("Começar por Prevenir", caminho("prevenir"))],
        destino={"aba": LAMINAS["sobre"]},
        numeros=[f"A confirmar: {t}" for t in pendentes],
    )


def responder(acao):
    """Executa um botão da Lia no apoio. Toda resposta termina com [Começar de novo]."""
    tipo = acao.get("tipo")
    if tipo == "apoio_caminho" and acao.get("id") in NOME_CAMINHO:
        r = responder_caminho(acao["id"])
    elif tipo == "apoio_item" and acao.get("id") in POR_ID:
        r = responder_item(acao["id"])
    elif tipo == "apoio_lamina" and acao.get("id") in ("rio_claro", "barretos"):
        r = responder_lamina(acao["id"])
    elif tipo == "apoio_sobre":
        r = responder_sobre()
    else:
        return saudacao()
    r.botoes = r.botoes + [("Começar de novo", INICIO)]
    return r
