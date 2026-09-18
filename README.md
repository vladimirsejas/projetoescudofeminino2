# Escudo Feminino

Sistema de inteligência analítica sobre saúde da mulher, construído a partir
de dados de internações hospitalares do SUS relacionadas a câncer feminino
no município de Rio Claro (SP), comparado ao Estado de São Paulo.

O projeto é um **Sistema de Apoio à Decisão para Políticas Públicas baseado
em Inteligência Analítica** — o chat é apenas a interface de acesso; o
produto de verdade é o conhecimento estruturado que existe por trás dele.

Trabalho da disciplina de GATEC (graduação em IA) — Fatec Rio Claro, 3º
semestre.

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
