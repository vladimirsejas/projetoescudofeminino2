# Catálogo de Perguntas — Escudo Feminino V2

## Finalidade

Este catálogo formaliza as perguntas já existentes no teste de cobertura da V1 e registra, para cada uma, a intenção e a fonte de conhecimento necessária.

Este arquivo é documentação de teste da V2. Não altera o motor de produção.

## Categorias

- Situação
- Priorização
- Ranking de prioridades
- Mortalidade
- Custo
- Permanência hospitalar
- Faixa etária
- Tendência estadual
- Anomalias
- Incidência
- Relatório executivo
- Simulação
- Câncer específico
- Vulnerabilidade
- Apoio à decisão
- Mudança temporal

## Catálogo

| # | Pergunta | Intenção | Fonte necessária |
|---:|---|---|---|
| 1 | Como está Rio Claro? | Situação | priorizacao_executiva + tendencia_estadual + anomalias |
| 2 | O município está melhorando? | Situação | tendencia_estadual + anomalias |
| 3 | Qual o panorama geral da saúde da mulher? | Situação | priorizacao_executiva + tendencia_estadual + anomalias |
| 4 | Dê uma visão geral da situação | Situação | priorizacao_executiva + tendencia_estadual + anomalias |
| 5 | Qual câncer merece mais atenção? | Priorização | priorizacao_executiva + base_conhecimento |
| 6 | O que mais preocupa atualmente? | Priorização | priorizacao_executiva + base_conhecimento |
| 7 | Onde devemos investir recursos? | Apoio à decisão | priorizacao_executiva + base_conhecimento |
| 8 | Qual câncer é mais grave? | Priorização | priorizacao_executiva + base_conhecimento |
| 9 | Qual é a principal prioridade? | Priorização | priorizacao_executiva + base_conhecimento |
| 10 | Existe algum risco urgente? | Priorização | priorizacao_executiva + base_conhecimento + anomalias |
| 11 | Se eu pudesse agir em apenas um câncer, qual escolher? | Apoio à decisão | priorizacao_executiva + base_conhecimento |
| 12 | Quais problemas exigem ação imediata? | Priorização | priorizacao_executiva + base_conhecimento |
| 13 | Quais são as 3 maiores prioridades? | Ranking de prioridades | priorizacao_executiva |
| 14 | Me dê o ranking de prioridades | Ranking de prioridades | priorizacao_executiva |
| 15 | Qual câncer mais mata? | Mortalidade | mortalidade |
| 16 | Qual tem a maior taxa de mortalidade? | Mortalidade | mortalidade |
| 17 | Qual é o mais letal? | Mortalidade | mortalidade |
| 18 | Qual câncer gera maior custo hospitalar? | Custo | custos_hospitalares |
| 19 | Onde está o maior gasto? | Custo | custos_hospitalares |
| 20 | Quais doenças geram mais custos para o orçamento? | Custo | custos_hospitalares |
| 21 | Qual apresenta maior permanência hospitalar? | Permanência hospitalar | permanencia_hospitalar |
| 22 | Qual ocupa mais leitos? | Permanência hospitalar | permanencia_hospitalar |
| 23 | Quais doenças ocupam mais leitos do hospital? | Permanência hospitalar | permanencia_hospitalar |
| 24 | Qual faixa etária é mais afetada? | Faixa etária | faixa_etaria |
| 25 | Quais são as idades mais atingidas? | Faixa etária | faixa_etaria |
| 26 | Qual câncer está acima da tendência estadual? | Tendência estadual | tendencia_estadual |
| 27 | Rio Claro acompanha o comportamento do Estado? | Tendência estadual | tendencia_estadual |
| 28 | O que está crescendo mais rápido que São Paulo? | Tendência estadual | tendencia_estadual |
| 29 | Existem comportamentos anormais? | Anomalias | anomalias |
| 30 | Quais são os principais alertas? | Anomalias | anomalias |
| 31 | Há algo fora do padrão histórico? | Anomalias | anomalias |
| 32 | Qual câncer possui mais internações? | Incidência hospitalar | internacoes |
| 33 | Qual é o mais comum em Rio Claro? | Incidência hospitalar | internacoes |
| 34 | Quais doenças afetam mais mulheres? | Incidência hospitalar | internacoes |
| 35 | Gere um relatório executivo | Relatório executivo | relatorio_executivo |
| 36 | Quero o relatório completo | Relatório executivo | relatorio_executivo |
| 37 | Simular redução de 20% na MAMA | Simulação | internacoes |
| 38 | E se reduzirmos 30% dos casos de colo do útero? | Simulação | internacoes |
| 39 | Fale sobre MAMA | Câncer específico | base_conhecimento + memoria_ia |
| 40 | O que você sabe sobre COLO_UTERO? | Câncer específico | base_conhecimento + memoria_ia |
| 41 | Por que a MAMA é um risco? | Câncer específico | base_conhecimento + memoria_ia |
| 42 | Explique a situação do PULMAO | Câncer específico | base_conhecimento + memoria_ia |
| 43 | Quais mulheres estão vulneráveis? | Vulnerabilidade | vulnerabilidade |
| 44 | O que mudou desde o ano passado? | Mudança temporal | anomalias + tendencia_estadual |
| 45 | Estou de acordo com essa prioridade? | Apoio à decisão | priorizacao_executiva + base_conhecimento |

## Observações para a V2

1. As perguntas 1–45 vêm do catálogo existente em `algoritimos/teste_cobertura.py`.
2. As categorias acima representam a intenção funcional desejada. Elas não obrigam a implementação atual a mudar neste passo.
3. "Apoio à decisão" é uma intenção funcional transversal: a resposta deve apresentar evidências e recomendações de apoio, sem substituir a decisão do responsável.
4. "Mudança temporal" representa uma lacuna explícita do catálogo atual. A pergunta já existe como teste de cobertura, mas ainda não possui uma categoria própria no classificador.
5. Perguntas de câncer específico dependem do câncer mencionado e usam o conhecimento estruturado correspondente.
6. Perguntas gerais devem utilizar somente as fontes necessárias ao tipo de pergunta; não devem receber tabelas indiscriminadamente.
7. O catálogo será usado nos próximos passos para testar reformulações naturais e qualidade das respostas.
8. Este catálogo não é um mecanismo de aprendizado automático. É uma referência controlada para teste, cobertura e evolução do sistema.
