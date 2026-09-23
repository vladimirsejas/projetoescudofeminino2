# Escudo Feminino

Sistema de inteligência analítica sobre saúde da mulher, construído a partir
de dados de internações hospitalares do SUS relacionadas a câncer feminino
no município de Rio Claro (SP), comparado ao Estado de São Paulo.

O projeto é um **Sistema de Apoio à Decisão para Políticas Públicas baseado
em Inteligência Analítica** — o chat é apenas a interface de acesso; o
produto de verdade é o conhecimento estruturado que existe por trás dele.

Trabalho acadêmico de graduação em Inteligência Artificial — Fatec Rio
Claro, 3º semestre.

---

## Como rodar o projeto do zero (ordem obrigatória)

Cada script lê o resultado do anterior. Rodar fora de ordem quebra o
script seguinte com erro de "tabela não encontrada" ou "coluna não
encontrada". Rode sempre a partir da raiz do projeto
(`C:\projetoescudofeminino2`), nessa sequência exata:

```powershell
# 1. Indicadores de base (podem rodar em qualquer ordem entre si)
python algoritimos\mortalidade.py
python algoritimos\custos_hospitalares.py
python algoritimos\permanencia_hospitalar.py
python algoritimos\faixa_etaria.py

# 2. Score epidemiológico (usa a tabela internacoes diretamente)
python algoritimos\score_epidemiologico.py

# 3. Tendência estadual e anomalias (precisam vir antes da priorização)
python algoritimos\tendencia_estadual.py
python algoritimos\anomalias.py

# 4. Priorização executiva (junta score + tendência + anomalias)
python algoritimos\priorizador.py

# 5. Perfil epidemiológico (junta priorização + mortalidade + custo + permanência + faixa etária)
python algoritimos\perfil_epidemiologico.py

# 6. Camada de conhecimento e explicação
python algoritimos\base_conhecimento.py
python algoritimos\memoria_ia.py
python algoritimos\fichas_ia.py

# 7. Relatório executivo (gera relatorio_executivo.txt)
python algoritimos\relatorio_executivo.py
```

Depois disso, o chat já pode ser usado:

```powershell
python algoritimos\chat_escudo.py
```

**Quando rodar tudo de novo:** só quando os dados de `internacoes` mudarem
(nova carga do ETL). Se você só editou um script de explicação (por
exemplo, `base_conhecimento.py`), não precisa refazer os passos 1 a 5 —
só rode a partir do passo que você mudou em diante.

### Trocando o recorte de anos dos dados brutos (ex.: 2021-2025 → 2013-2025)

`etl/carga_todas_bases.py` lê **um único CSV por pasta** em
`dados\cancer_X_territorio\`. Se você baixar um CSV novo com um
recorte de anos maior (ex.: cobrindo 2013-2025) para substituir um
mais antigo (ex.: só 2021-2025), **apague ou mova o CSV antigo para
fora da pasta antes de rodar a carga** — não deixe os dois juntos.
Desde que essa checagem foi adicionada, a carga recusa rodar e avisa
o nome da pasta e dos arquivos em conflito se encontrar mais de um
CSV na mesma pasta, em vez de escolher um dos dois silenciosamente
(o que antes podia carregar o arquivo errado, ou contar o mesmo ano
duas vezes, sem nenhum aviso).

A carga também detecta sozinha se o CSV usa `;` (padrão do extrato
bruto do DATASUS) ou `,` (visto em arquivos consolidados por outra
ferramenta, ex.: pysus) -- olhando só a coluna `ANO_CMPT` no
cabeçalho. Se nenhum dos dois separadores encontrar essa coluna, a
carga avisa e mostra o cabeçalho real do arquivo, em vez de estourar
um `KeyError` sem explicação.

A carga **pula a pasta de uma cidade** (ex.: `cancer_mama_rio_claro`)
quando existe a pasta estadual do mesmo câncer (`cancer_mama_sp`): o
arquivo estadual já traz as mesmas internações, com o município de
residência, e carregar os dois contava a cidade em dobro. A carga
mostra `PULADA: ...` para cada pasta assim e, no fim, avisa se ainda
sobrou alguma cidade com internações de duas fontes.

Depois de trocar os arquivos, rode a carga e a cadeia inteira de novo
(passos 1 a 7 acima) e confira os testes antes de considerar a troca
concluída:

```powershell
python etl\carga_todas_bases.py
python algoritimos\teste_territorial.py
python algoritimos\teste_par_real_municipios.py
```

### Série temporal anual (base para uma futura camada preditiva)

`algoritimos\serie_temporal.py` é um passo **adicional e opcional** —
não faz parte da ordem obrigatória acima e pode ser rodado a
qualquer momento depois que `internacoes` estiver carregada. Ele
agrega internações e óbitos por `tipo_cancer x ano` (todos os anos
que existirem no banco, não só os dois mais recentes) e grava em
`serie_temporal_anual`, multi-tenant como as demais tabelas
derivadas. Nada hoje consome essa tabela ainda — ela existe para
servir de matéria-prima ao primeiro modelo preditivo (regressão,
random forest etc.), quando o histórico de anos for suficiente para
isso fazer sentido metodologicamente.

```powershell
python algoritimos\serie_temporal.py
```

### Painel novo e inteligência central

O dashboard (`dashboard\app.py`) foi reescrito do zero em 09/2026: o
anterior tinha 7 abas que repetiam os mesmos números. O novo tem uma
tela só, organizada por perguntas:

1. **Quais cânceres mais levam as mulheres da cidade ao hospital?**
   (barras; clicar numa barra escolhe o câncer)
2. **Como as internações desse câncer mudaram?** (linha de 2013 a
   2025, com camadas que liga/desliga: ritmo do Estado de SP, anos
   fora do padrão e projeção exploratória)

Embaixo de cada gráfico vem a leitura em texto, e o chat fica no
painel lateral (`algoritimos\conversa.py`: entende a pergunta,
calcula os fatos com a mesma inteligência dos gráficos e pede ao
Gemini só a redação; sem Gemini, responde direto com os fatos). A tela não calcula nada: tudo vem de
`algoritimos\inteligencia.py`, que lê `internacoes` direto (não
depende da cadeia de scripts acima) e é testado sem o banco:

```powershell
python algoritimos\teste_inteligencia.py
python algoritimos\teste_conversa.py
py -m streamlit run dashboard\app.py
```

Dois cuidados que a inteligência central já aplica:
- **Uma fonte por cidade.** As moradoras de Rio Claro podem estar em
  `internacoes` duas vezes (arquivo de Rio Claro + arquivo estadual,
  ambos com `municipio = 'RIO_CLARO'`); somar tudo contaria em dobro.
  Usa-se só o arquivo estadual (o mesmo para todas as cidades).
- **2025 em investigação.** No Estado inteiro, 6 dos 7 cânceres
  saltaram ao mesmo tempo em 2025 -- mais provável efeito de
  registro/processamento (o ano gravado é `ANO_CMPT`, competência da
  AIH) do que de adoecimento. O painel avisa isso ao lado do gráfico.

---

## Estrutura do projeto

```
algoritimos/     → todos os scripts de indicadores, conhecimento e chat
analises/        → scripts de análise pontual (não fazem parte do pipeline oficial)
banco/           → escudo_feminino.db (não versionado — está no .gitignore)
dashboard/       → app Streamlit
docs/            → documentação adicional
etl/             → carga e limpeza dos dados brutos no banco
relatorios/      → relatórios exportados
relatorio_executivo.txt → gerado automaticamente por algoritimos/relatorio_executivo.py
```

## O motor de chat (`algoritimos/chat_escudo.py`)

É o único ponto de entrada do sistema de perguntas — substitui
`motor_respostas.py`, `orquestrador_ia.py` e `perguntas_negocio.py`, que
continuam no projeto só como referência histórica e não devem mais ser
rodados diretamente.

Ao abrir, ele pergunta o perfil de linguagem:

- **Técnico** (padrão): para gestor, secretário, pesquisador — resposta
  completa com motivo, impacto e recomendação.
- **Simples**: para população em geral — mesma informação, sem jargão
  nem número técnico solto.

Categorias de pergunta reconhecidas: nome de um câncer específico,
panorama geral, prioridade/atenção/risco, top 3, mortalidade, custo,
permanência, faixa etária, tendência estadual, anomalias, incidência,
relatório executivo. O reconhecimento é por palavra-chave (com
normalização de acento) — não é um modelo de linguagem natural.

Toda pergunta feita é registrada na tabela `perguntas_usuarios`. Para ver
quais perguntas o motor ainda não reconhece (e priorizar novos
sinônimos), rode:

```powershell
python algoritimos\analise_perguntas.py
```

## Limitação conhecida e decisão pendente

O motor de intenções atual é baseado em regras (palavra-chave). Ele não
entende sinônimos que não foram previstos, nem reformulações livres da
pergunta. Resolver isso de verdade exige contratar uma IA de linguagem
via API (paga por token) — essa é uma decisão de orçamento do grupo,
ainda não tomada. Enquanto isso não acontece, o caminho de melhoria é
observar `perguntas_usuarios` e ir cobrindo os sinônimos mais frequentes
manualmente em `classificar_intencao()`.

## Metodologia — limites que o sistema respeita

- Nenhuma resposta afirma causa a partir de uma correlação ou tendência.
- Quando um percentual de variação é calculado sobre uma base pequena de
  casos (menos de 10 internações no ano-base), o sistema marca a linha
  como de baixa confiabilidade estatística em vez de apresentar o número
  como fato sólido.
- Toda recomendação é apoio à decisão — a responsabilidade final é do
  gestor responsável.
