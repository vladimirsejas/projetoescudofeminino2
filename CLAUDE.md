# Escudo Feminino

Sistema de apoio à decisão para políticas públicas em saúde da mulher,
construído a partir de dados de internações hospitalares do SUS
relacionadas a câncer feminino no município de Rio Claro (SP), comparado
ao Estado de São Paulo. Trabalho acadêmico de graduação em Inteligência
Artificial — Fatec Rio Claro, 3º semestre.

Veja o `README.md` para a ordem obrigatória de execução dos scripts em
`algoritimos/` (cada um lê o resultado do anterior).

## Autorização permanente de git

O dono deste repositório (Vladimir) autorizou explicitamente: Claude pode
criar/corrigir código para melhorar este projeto e enviar (`git push`)
direto para o branch `main`, sem precisar pedir confirmação a cada vez —
incluindo commitar, fazer merge de outro branch e dar push direto no
`main`. Essa autorização vale de forma permanente para este repositório
específico (não se estende a outros repositórios do usuário nem
dispensa cuidado normal: sempre validar a mudança — rodar `py_compile`,
testar a lógica isoladamente quando possível, revisar o diff — antes do
push, e nunca commitar segredos/credenciais).

## Arquitetura territorial (código IBGE)

O projeto está migrando de "Rio Claro fixo" para "município
configurável", identificado pelo código oficial do IBGE:

- Tabela `municipios` (codigo_ibge, origem, nome, uf) associa
  metadados IBGE a cada valor já usado em `internacoes.origem`.
  `origem` continua sendo o identificador interno usado em todo
  `WHERE origem = ?` do projeto -- a tabela só adiciona código IBGE
  e nome de apresentação em cima dele. Criada por
  `etl/criar_tabela_municipios.py`, hoje só com Rio Claro (IBGE
  3543907). SP não entra nela: é a referência estadual, não um
  município.
- `configuracao_geografica.py` expõe `obter_municipio()` (aceita
  identificador de texto OU código IBGE via `ESCUDO_MUNICIPIO`),
  `obter_codigo_ibge()`, `obter_nome_municipio()`, `obter_uf()` e
  `listar_municipios_disponiveis()` (consulta `municipios ∩
  internacoes`, nunca lista fixa no código).
- Todas as 13 tabelas derivadas (mortalidade, custos, permanência,
  faixa etária, score, tendência estadual, anomalias, priorização,
  base de conhecimento, perfil epidemiológico, memória, fichas,
  vulnerabilidade) são **multi-tenant**: gravadas via
  `salvar_tabela_municipio()` (marca cada linha com uma coluna
  `municipio` e substitui só as linhas desse município, nunca a
  tabela inteira) e lidas via `ler_tabela_municipio()` (sempre
  filtra por município -- ler sem filtrar duplicaria linhas em
  qualquer merge por `tipo_cancer`). Isso permite que os resultados
  de vários municípios já processados coexistam na mesma tabela.
  `tendencia_estadual.py` guarda a variação em colunas fixas
  (`variacao_municipio`/`variacao_sp`, não mais nomeadas
  dinamicamente pelo município) exatamente por isso -- nome de
  coluna dinâmico é incompatível com tabela multi-tenant. SP
  continua fixo como referência estadual.
- `dashboard/app.py` tem seletor de município no topo (populado por
  `listar_municipios_disponiveis()`) e lê tudo de
  `algoritimos/inteligencia.py`, direto de `internacoes` -- não
  depende da cadeia determinística (ver "Painel novo" abaixo).
- Textos narrativos (`chat_escudo.py`, `base_conhecimento.py`,
  `relatorio_executivo.py`, `motor_raciocinio.py`) usam
  `obter_nome_municipio()` dinamicamente -- não há mais "Rio Claro"
  fixo nas frases geradas.
- Municípios disponíveis dependem só dos dados carregados no banco
  -- adicionar uma cidade nova é (1) extrair os CSVs do DATASUS
  seguindo o padrão de pastas de `etl/carga_todas_bases.py`, (2)
  cadastrar o município em `municipios`, (3) rodar a cadeia
  determinística de novo (`ESCUDO_MUNICIPIO=<origem_ou_ibge>`).
  Nenhum código precisa mudar para isso, e processar um município
  novo não apaga os já processados (`teste_territorial.py` prova
  essa coexistência).

**Pendências conhecidas desta etapa** (arquitetura pronta, mas não
tudo foi feito -- ver commits para detalhes):
- Comparação entre múltiplos municípios: a aba "Comparar" do painel
  antigo (só 2 cidades, números absolutos) saiu junto com ele. A
  comparação nova depende de trazer a população do IBGE (gráfico de
  funil) -- ver "Painel novo" abaixo.
- Teste de regressão real (rodar a cadeia contra o banco de verdade
  no Windows do autor) ainda não foi feito -- `teste_territorial.py`
  valida a lógica com banco sintético/temporário.

## Painel novo (09/2026) — decisões combinadas com o autor

Depois do retorno da Secretaria da Mulher, o autor (com Claude e
ChatGPT) decidiu **reduzir** o Escudo: uma inteligência central com
poucas portas de entrada, não cinco sistemas. Regras:

- **Toda funcionalidade nova precisa responder uma pergunta que o
  Escudo ainda não responde.** Se não responder, não entra.
- **Cada informação tem uma casa só** no painel; não repetir números
  em várias telas.
- **Todo gráfico = pergunta (título) + gráfico + leitura em texto.**
- **A inteligência calcula, o Gemini explica.** Nunca atribuir
  causa; detectar ≠ explicar.
- **Nada de orçamento em reais.** O Escudo aponta o que merece
  atenção no planejamento, com evidências; quem decide é o gestor.
  (A aba "Onde investir", commit `273fbe5`, foi descartada por isso.)
- Usuários: gestores (Secretaria é uma delas), pesquisadores,
  estudantes, população (via modo simples do chat).
- **Pensar e combinar antes de codar.** O autor pediu explicitamente
  para não sair implementando sem conversar.

Estado atual:
- `algoritimos/inteligencia.py`: única fonte dos números do painel
  (série anual cidade + Estado, anos fora do padrão, ritmo do Estado
  na escala da cidade, projeção exploratória com teste de acerto,
  frases de leitura). Testado por `teste_inteligencia.py`.
- `dashboard/app.py`: portas em abas, cada informação numa casa só --
  **Panorama** (barras medidas por internações / valor hospitalar
  registrado / óbitos / dias + ficha "o que chama atenção" do câncer
  em foco), **Evolução** (linha com camadas Estado / fora do padrão /
  projeção de tendência + caixa de confiabilidade), **Investigar**
  (anos fora do padrão de todos os cânceres, "quando cada câncer
  aparece", faixa etária em dois períodos, download CSV),
  **Planejamento** (quadrante crescimento x letalidade relativa +
  evidências por câncer com pressão projetada em internações, dias e
  valor registrado, e linha de ação do INCA), **Método**. Chat na
  lateral.
- Dinheiro sempre como **"valor hospitalar registrado no SIH/SUS"**
  (VAL_TOT das AIHs): não é orçamento municipal nem custo total do
  tratamento. Projeção sempre como **"projeção de tendência"**, nunca
  "IA preditiva". Óbitos não são projetados (poucos por ano).
- **Lia** (`algoritimos/lia.py`, `dashboard/lia_rosto.py`,
  `docs/LIA.md`): guia do Escudo, pesquisadora negra madura (não
  médica, sem marca de instituição real). Árvore de 3 níveis
  (caminhos -> câncer -> ação), falas determinísticas montadas com
  `inteligencia.py`, expressão do rosto escolhida pela confiabilidade
  do dado (acolhedora / explicando / atenta / cautelosa / pensativa);
  texto livre passa por `conversa.py` e volta no formato dela. O
  painel acompanha a Lia (aba, câncer, medida, camadas). Testado por
  `teste_lia.py`. **Armadilha do Streamlit resolvida no painel:**
  widgets que somem e voltam (abas desenhadas só quando abertas)
  devolviam o valor antigo; por isso cada widget tem chave atrelada
  ao valor (`chave_widget`) e o estado real fica em chaves próprias
  (`definir`). Não voltar a usar `key="doenca"` direto.
- **Divisão de trabalho (09/2026):** o ChatGPT cuida de
  `conversa.py`/`teste_conversa.py`; Claude cuida de `inteligencia.py`
  e do painel (o autor passou a Lia para o Claude). Pendências do
  chat para acompanhar o painel: trocar
  "valor pago pelo SUS" por "valor hospitalar registrado no SIH/SUS";
  trocar "Projeção exploratória" por "Projeção de tendência" nos
  textos de "onde ver"; usar `inteligencia.evidencias_planejamento`,
  `ficha_cancer`, `destaques_cancer` e `LINHAS_DE_ACAO` em vez das
  cópias locais (`sinais_de_atencao`, `LINHAS_DE_ACAO` em
  `conversa.py`), para chat e painel não divergirem; usar
  `inteligencia.cancer_de()` ("câncer colorretal", sem "de").
- **Contagem em dobro de Rio Claro: confirmada e corrigida.** No
  banco real havia 1.668 internações de Rio Claro com origem
  RIO_CLARO e as mesmas 1.668 com origem SP (a pasta estadual já traz
  todas as cidades). Todo total por `municipio = 'RIO_CLARO'` nos
  scripts antigos saía dobrado (taxas e médias não). Correção na
  carga: `pastas_para_carregar()` pula a pasta municipal quando existe
  a estadual do mesmo câncer, e `municipios_duplicados()` confere no
  fim (teste: `etl/teste_carga_duplicidade.py`). Com isso, as
  moradoras de Rio Claro passam a ter `origem = 'SP'` como as de
  qualquer cidade; nenhum script dependia de `origem = 'RIO_CLARO'`.
  Precisa rodar a carga + cadeia de novo no Windows.
- **Chat do painel: `algoritimos/conversa.py`** (substituiu
  `chat_servico.py`). Entender (assunto por PONTUAÇÃO de palavras-
  chave, não "primeiro if que der match"; câncer por sinônimos com
  palavra inteira) -> calcular (fatos de `inteligencia.py`, nunca das
  13 tabelas antigas) -> explicar (Gemini via `ia_linguagem`; se
  falhar, resposta direta com os fatos). Perguntas de orçamento
  recebem sinais de atenção com evidência, nunca valores em R$.
  Testado por `teste_conversa.py`. O chat de terminal
  (`chat_escudo.py`) ainda usa o motor antigo.
- Próximos passos combinados, nesta ordem: investigar 2025
  (`ANO_CMPT` x `DT_INTER` nos CSVs brutos); população do IBGE para
  comparar cidades (gráfico de funil, cidades semelhantes); decidir
  o destino de `chat_escudo.py`/`motor_raciocinio.py` e das 13
  tabelas antigas.

## Notas de contexto do domínio

- Banco de dados: `banco/escudo_feminino.db` (SQLite). Caminho hardcoded
  em alguns scripts como `C:\projetoescudofeminino2\banco\...` — isso é
  esperado, o projeto roda no Windows do autor.
- `algoritimos/chat_escudo.py` é a interface de chat: classifica a
  intenção da pergunta (`classificar_intencao`) e monta contexto
  estruturado para a IA (Gemini) responder com base nos dados, nunca por
  conta própria.
- Ordem dos blocos `if` em `classificar_intencao()` importa: o primeiro
  bloco cujas palavras-chave derem match "vence". Ao adicionar novas
  palavras-chave a uma intenção, verificar se algum bloco anterior no
  arquivo não vai capturar a pergunta antes de chegar na intenção nova.
