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
- Todos os indicadores que leem `internacoes` diretamente
  (mortalidade, custos, permanência, faixa etária, score,
  anomalias, tendência estadual) filtram por `obter_municipio()`.
  `priorizador.py` não precisa filtrar -- só consome tabelas já
  filtradas. `tendencia_estadual.py` nomeia sua coluna de variação
  dinamicamente pelo município (SP fica fixo como referência).
- `dashboard/app.py` tem seletor de município na sidebar, populado
  por `listar_municipios_disponiveis()`.
- Municípios disponíveis dependem só dos dados carregados no banco
  -- adicionar uma cidade nova é (1) extrair os CSVs do DATASUS
  seguindo o padrão de pastas de `etl/carga_todas_bases.py`, (2)
  cadastrar o município em `municipios`, (3) rodar a cadeia
  determinística de novo. Nenhum código precisa mudar para isso.

**Pendências conhecidas desta etapa** (arquitetura pronta, mas não
tudo foi migrado -- ver commits para detalhes):
- Textos gerados em `chat_escudo.py`, `base_conhecimento.py`
  (`gerar_motivo`/`gerar_impacto`) e `relatorio_executivo.py` ainda
  escrevem "Rio Claro" fixo nas frases narrativas. Não crasha para
  outro município, mas a frase erra o nome da cidade.
- Comparação entre múltiplos municípios (ex.: "Rio Claro x
  Limeira") foi deliberadamente **não implementada** nesta etapa --
  só a base para isso foi preparada.
- `dashboard/app.py`: trocar o seletor não reprocessa
  `base_conhecimento`/`priorizacao_executiva`/`tendencia_estadual`
  automaticamente -- essas tabelas refletem o município configurado
  na última execução da cadeia determinística via `ESCUDO_MUNICIPIO`.
- Teste de regressão real (rodar a cadeia contra o banco de verdade
  no Windows do autor) ainda não foi feito -- `teste_territorial.py`
  valida a lógica com banco sintético.

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
