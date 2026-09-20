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

O Escudo agora trabalha com dois níveis territoriais distintos:

- `origem = SP`: referência estadual, correspondente ao arquivo estadual completo.
- `municipio`: identificador interno do município de residência de cada registro.
- `codigo_ibge`: código oficial do município associado ao registro.
- `municipios`: catálogo com código IBGE, identificador interno, nome e UF.

O catálogo é preenchido por `etl/criar_tabela_municipios.py` a partir da
tabela de municípios do IBGE. São Paulo município é o código **3550308**;
Rio Claro é **3543907**. O Estado de São Paulo continua sendo a referência
estadual e não é tratado como o município da capital.

O carregador `etl/carga_todas_bases.py` preserva o município nos registros
estaduais. Ele reconhece campos de código municipal da fonte, converte códigos
de 6 ou 7 dígitos para o catálogo IBGE e interrompe a carga se os registros
estaduais não puderem ser identificados territorialmente. O recorte da pasta
de Rio Claro permanece Rio Claro, sem reclassificação.

`configuracao_geografica.py` aceita identificador ou código IBGE em
`ESCUDO_MUNICIPIO` e `listar_municipios_disponiveis()` retorna somente
municípios que possuem dados em `internacoes`.

Os indicadores municipais filtram por `internacoes.municipio`.
`tendencia_estadual.py` compara o município selecionado com o agregado
estadual definido por `internacoes.origem = 'SP'`.

O dashboard possui seletor dinâmico de município e chama
`algoritimos/executar_cadeia.py` quando a seleção muda, garantindo que
priorização, tendência, anomalias, base de conhecimento e relatório
correspondam ao município exibido.

### Testes

- `algoritimos/teste_territorial.py`: regressão da cadeia determinística
  com banco sintético e múltiplos municípios.
- `etl/teste_carga_territorial.py`: identificação por código IBGE,
  códigos de 6/7 dígitos, códigos desconhecidos e preservação do recorte
  de Rio Claro.
- `.github/workflows/testes-territoriais.yml`: executa os testes no
  GitHub Actions.

### Limites atuais

- A comparação direta entre dois municípios (ex.: Rio Claro x Limeira) ainda
  não é o objetivo desta etapa. O foco é município selecionado x Estado de SP.
- A expansão depende de os arquivos estaduais realmente conterem o código
  municipal de residência. Se a fonte não trouxer esse campo, o ETL para em
  vez de fabricar uma classificação.
- A regressão contra o banco real do Windows do autor ainda depende da
  execução local da nova carga, porque o banco SQLite real não está
  versionado no GitHub.

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
