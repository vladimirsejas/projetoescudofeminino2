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
- `dashboard/app.py` tem seletor de município na sidebar (populado
  por `listar_municipios_disponiveis()`) e agora filtra
  `base_conhecimento`/`tendencia_estadual` pelo município
  selecionado de verdade -- se esse município ainda não foi
  processado pela cadeia determinística, mostra aviso claro em vez
  de dado errado ou vazio.
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
- Comparação entre múltiplos municípios (ex.: "Rio Claro x
  Limeira") já existe na aba "Comparar" do `dashboard/app.py`
  (commit `5100b20`), mas só compara internações/óbitos/valor/
  permanência agregados direto de `internacoes`, município a
  município escolhido em um seletor -- não usa as 13 tabelas
  derivadas (mortalidade, score, anomalias etc.), não aparece no
  chat (`chat_escudo.py` não tem intenção de comparar duas
  cidades) e compara só duas cidades por vez, nunca uma lista. Hoje
  só Rio Claro está cadastrado em `municipios`, então a aba mostra
  "não há outro município" até uma segunda cidade ser carregada.
- Teste de regressão real (rodar a cadeia contra o banco de verdade
  no Windows do autor) ainda não foi feito -- `teste_territorial.py`
  valida a lógica com banco sintético/temporário.

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
