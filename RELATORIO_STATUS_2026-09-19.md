# Relatório de status — 19/09/2026

Fechamento do dia de trabalho (Claude + ChatGPT, mais de 24h de sessão
combinada). Este documento existe pra retomar amanhã sem precisar
reconstruir o contexto do zero.

## Onde as coisas estão

**`main`** no GitHub está em `e8fec3b` ("Adiciona comparação direta
entre municípios"). Branches extras que apareceram durante o dia e
ainda não foram limpos: `comparacao-municipios`,
`territorial-dados-estaduais`, `territorial-dados-pretest`,
`territorial-estadual`, `territorial-pretest` (provavelmente
experimentos/staging do ChatGPT — não investigados a fundo, não
parecem sessões ativas).

### O que foi construído e validado (Rio Claro, ponta a ponta)

- Bug de mistura Rio Claro + Estado de SP corrigido em 7 indicadores
  (`mortalidade`, `custos_hospitalares`, `permanencia_hospitalar`,
  `faixa_etaria`, `score_epidemiologico`, `anomalias`,
  `vulnerabilidade`) — testado com dados sintéticos mostrando a
  distorção real (ex.: taxa de mortalidade que parecia 3,6% e era
  30% de verdade).
- Correção do classificador de intenção do chat (ordem de
  `MUDANCA_TEMPORAL` vs `SITUACAO_GERAL` em `classificar_intencao`).
- Arquitetura territorial por código IBGE: tabela `municipios`,
  `configuracao_geografica.py` com `obter_municipio()` /
  `obter_codigo_ibge()` / `obter_nome_municipio()` /
  `listar_municipios_disponiveis()`.
- Todas as 13 tabelas derivadas viraram multi-tenant
  (`salvar_tabela_municipio()` / `ler_tabela_municipio()`) —
  processar um segundo município não apaga o primeiro. Provado com
  teste automatizado (`algoritimos/teste_territorial.py`, 16
  checagens A-J, todas passando com banco sintético).
- Textos fixos "Rio Claro" eliminados das respostas do chat, do
  relatório executivo e da base de conhecimento — tudo usa
  `obter_nome_municipio()` agora.
- Dashboard com seletor de município que realmente filtra os dados
  exibidos (e avisa quando o município escolhido ainda não foi
  processado, em vez de mostrar dado errado).

### O que outra fonte (ChatGPT, direto no `main`) construiu por cima

- `etl/criar_tabela_municipios.py` passou a baixar o catálogo
  oficial de municípios de SP da API do IBGE (~645 cidades, só
  metadado: código, nome, UF — nenhum dado de saúde).
- `etl/carga_todas_bases.py` passou a **desagregar o arquivo
  estadual de SP por município de residência** (usando a coluna
  `MUNIC_RES` que o DATASUS já inclui), gravando o resultado numa
  coluna nova `internacoes.municipio` (+ `codigo_ibge`). Ideia boa:
  os dados de todas as cidades de SP já estavam dentro do CSV
  estadual, nunca foi preciso baixar nada novo por cidade.
- Dashboard ganhou uma seção de "comparação direta entre
  municípios" (`e8fec3b`) que já usa essa coluna `municipio` nova.

## A aresta técnica pendente (não resolvida ainda, achado de hoje)

Minha função `listar_municipios_disponiveis()` ainda filtra pela
coluna **antiga** `internacoes.origem` (que só tem os valores
`"RIO_CLARO"` e `"SP"`), mas o novo ETL identifica cada cidade pela
coluna **nova** `internacoes.municipio`. Na prática, isso quer dizer
que a lista de municípios disponíveis (usada pelo seletor do
dashboard e pela nova comparação) provavelmente só mostra Rio Claro
hoje, mesmo que os dados de outras ~644 cidades já estejam
carregados na tabela.

**Não é urgente corrigir isso amanhã de manhã** — é isolado, tem
causa raiz clara, e não compromete nada do que já foi testado para
Rio Claro. Mas é o primeiro ajuste de backend a fazer antes de
qualquer interface nova poder mostrar mais de uma cidade de verdade.

Também não resolvido: meus 8 scripts que ainda filtram
`internacoes` por `origem` (`mortalidade.py`,
`custos_hospitalares.py`, `permanencia_hospitalar.py`,
`faixa_etaria.py`, `score_epidemiologico.py`, `anomalias.py`,
`vulnerabilidade.py`, `tendencia_estadual.py`) precisam passar a
filtrar por `municipio` para funcionarem com qualquer cidade além de
Rio Claro. Enquanto isso não acontece, a cadeia determinística
completa (a que gera `base_conhecimento`, `priorizacao_executiva`
etc.) só produz resultado correto para Rio Claro.

## Próximo passo combinado: interface

Conversamos bastante sobre isso hoje, sem decidir nada — só
ideias. Resumo do que foi levantado, pra não perder:

### Personas identificadas (cada uma "entra" na ferramenta de um jeito diferente)

- **Gestor de uma cidade específica** (secretário de saúde,
  prefeito) — já sabe qual cidade quer, quer comparar com o Estado
  ou com cidades parecidas.
- **Pesquisador** — parte de uma pergunta/padrão, não de uma
  cidade; **vai fazer comparações entre cidades** (ponto que você
  destacou explicitamente).
- **Investidor** (ex.: decidir onde colocar um plano de saúde) —
  pensa em oportunidade/demanda, não em urgência de política
  pública. Ressalva importante: os dados são só de internações do
  SUS (sistema público), então não capturam quem já tem plano
  privado — isso precisa aparecer na interface se esse público for
  atendido.
- **População em geral** — já existe um modo de linguagem simples
  no chat; pensar se a interface nova preserva isso.

### Tensão em aberto (não decidida)

Interface principal deveria ser **conversa** (chat, escala bem em
variedade de pergunta, mas exige saber o que perguntar) ou
**navegação** (mapa/lista/busca, resolve "não sei o que existe", mas
não escala pra pergunta aberta)? Provável que a resposta seja "as
duas, uma como porta de entrada e outra como aprofundamento" — mas
qual é qual ainda não foi decidido.

### Ideias soltas levantadas (nenhuma escolhida ainda)

- Busca com autocomplete de cidade em vez de lista de 645 itens.
- Mapa de SP clicável, colorido por indicador.
- Seleção múltipla de cidades (checkboxes) + "cesta" de comparação
  salva entre perguntas.
- Tabela lado a lado, um município por coluna.
- Gráfico de dispersão (scatter) posicionando várias cidades de uma
  vez por dois indicadores.
- Comparação relativa a uma cidade-base ("+15% em relação a X") em
  vez de números absolutos soltos.
- Destacar visualmente quando um indicador comparado vem de amostra
  pequena (o selo de confiabilidade que já existe no texto).
- Exportação/CSV para o pesquisador levar a análise pra fora.
- Onboarding de uma pergunta ("você é gestor/pesquisador/outro?")
  que adapta o que aparece depois.
- Alertas proativos ("estas N cidades entraram em alerta esta
  semana") para quem não sabe o que perguntar.

## Perguntas em aberto para amanhã

1. A interface nova é sobre o **dashboard** (Streamlit), o **chat**,
   ou um terceiro formato ainda não escolhido?
2. Porta de entrada: cidade primeiro ou pergunta/problema primeiro?
3. O investidor entra mesmo no escopo do projeto (que nasceu como
   apoio à decisão de política pública), ou fica de fora por
   enquanto?
4. Corrigimos a aresta `origem` x `municipio` antes de desenhar a
   interface, ou desenhamos pensando já no esquema novo (assumindo
   que vai ser corrigido)?
5. O que fazer com os branches soltos (`comparacao-municipios`,
   `territorial-*`) — investigar, mesclar, ou descartar?

---
*Gerado ao final da sessão de 19/09/2026, a pedido do usuário, para
retomada no dia seguinte.*
