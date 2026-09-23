# Lia — guia do Escudo Feminino (versão 1.0)

**Lia** é a personagem que conduz a pessoa pelos dados. Nome curto,
fácil e com três leituras que se completam:

- **Leitura Inteligente de Análises** — o lado de dentro: ela lê o que
  a inteligência central calculou;
- **Língua de IA** — o lado de fora: ela traduz os números em conversa;
- **lia**, do verbo ler — "eu lia os dados".

> O Escudo calcula. A Lia lê e traduz. Os dados sustentam. A projeção
> mostra possibilidades. A gestão decide.

## Quem ela é

Pesquisadora de dados em saúde da mulher (**epidemiologia em dados**),
mulher negra, madura, serena e acolhedora. **Não é médica**: não usa
jaleco, não dá orientação clínica. Não usa marca de nenhuma
instituição real (INCA, hospitais, secretarias).

## As regras da Lia

1. **Ela conversa, o Escudo calcula.** Todo número da fala vem de
   `algoritimos/inteligencia.py`, a mesma fonte dos gráficos.
2. **Três níveis, sempre nesta ordem** quando houver tempo envolvido:
   o que aconteceu → o que está acontecendo → o que pode acontecer se
   a tendência continuar.
3. **O painel acompanha a Lia**: a cada resposta, ele vai sozinho
   para a aba, o câncer e a camada certos (sem precisar de um botão
   "ver no gráfico"). **Toda resposta termina com** próximos passos
   (2 ou 3 botões), **[Começar de novo]**, **[← Voltar]** e, quando há
   números por trás, **"Os números por trás"**.
4. **Ela sabe dizer "os dados não permitem"**: causas, casos novos,
   orçamento ideal, diagnóstico, comparação justa entre cidades (sem
   população).
5. **Dinheiro** é sempre "valor hospitalar registrado no SIH/SUS" —
   nunca orçamento. **Projeção** é sempre "projeção de tendência" —
   nunca "previsão de casos".
6. Perguntas pessoais de saúde: ela orienta procurar a unidade de
   saúde.

## As expressões (o rosto mostra a confiança)

| Expressão | Quando | Regra no código |
|---|---|---|
| **Acolhedora** | saudação, escolha de caminho | início e menus |
| **Explicando** | resposta com dado firme | padrão das respostas |
| **Atenta** | encontrou um sinal | há sinal de atenção (crescimento acima do Estado, letalidade acima do Estado, ano acima do esperado) |
| **Cautelosa** | o dado pede cuidado | números pequenos, projeção que erra mais que a média, resposta que depende do ano em investigação |
| **Pensativa** | "por quê?" e método | explicações de cálculo |

A expressão **vem dos dados** (`inteligencia.confiabilidade` e os
sinais), não é enfeite.

## A árvore (3 níveis, e só)

**Nível 0 — saudação**
> "Olá, eu sou a Lia, pesquisadora do Escudo Feminino. Vamos olhar
> juntas os dados de câncer em mulheres de {cidade}? O que você quer
> descobrir?"

**Nível 1 — caminhos**

| Botão | O que a Lia responde | Aba do gráfico |
|---|---|---|
| O que mais aparece? | os 3 cânceres com mais internações e a participação de cada um | Panorama (internações) |
| Está aumentando? | quais cânceres crescem, quanto, e quais crescem mais que o Estado | Evolução |
| Onde prestar atenção? | os cânceres com mais sinais nos dados, com o número de cada sinal | Planejamento |
| Valores hospitalares | onde se concentra o valor registrado e quem pesa mais no valor do que nas internações | Panorama (valor) |
| Comparar com São Paulo | ritmo da cidade x ritmo do Estado, câncer a câncer | Evolução (linha do Estado) |
| Olhar para frente | pede o câncer → projeção de tendência | Evolução (projeção) |
| Anos fora do padrão | todos os anos fora do padrão, e o aviso de quando vários mudam juntos | Investigar |
| Como esses dados funcionam? | fonte, o que é internação, o que os dados não dizem | Método |

**Nível 2 — qual câncer?** Os cânceres da cidade, do maior para o menor.

**Nível 3 — o que quer saber sobre ele?**

| Botão | Resposta | Aba |
|---|---|---|
| Evolução | três níveis: último ano → ritmo → comparação com o Estado | Evolução |
| Óbitos | letalidade hospitalar x Estado, com aviso se poucos óbitos | Panorama (óbitos) |
| Valores | valor registrado, % do total, média por internação x Estado | Panorama (valor) |
| Tempo de internação | dias no total e média por internação x Estado | Panorama (dias) |
| Idade | faixa etária em dois períodos: o que mudou | Investigar |
| Comparar com SP | ritmo x Estado | Evolução (linha do Estado) |
| Projeção | três níveis + faixa + teste de acerto + limites | Evolução (projeção) |
| Por quê? | os números por trás do destaque desse câncer | — |

Sempre com **[Voltar]** e **[Começar de novo]**.

**Sem caixa de texto livre.** Existiu (09/2026) e saiu por decisão
do autor: o motor de texto (`conversa.py`) só entende os mesmos
assuntos que os botões já cobrem, então a caixa respondia o mesmo com
menos precisão e prometia "pergunte qualquer coisa". A Lia conduz só
por botões. O código antigo está no histórico do git (commit
`8d78523`); `conversa.py` continua no repositório, fora do painel.

## O que fica fora da versão 1.0 (de propósito)

Escolha de perfil (gestora / pesquisadora / estudante / cidadã),
comparação entre cidades (precisa da população do IBGE), voz,
animação, memória entre visitas, personalidade gerada pela IA.

## Onde fica no código

- `algoritimos/lia.py` — a árvore: cada nó devolve fala, expressão,
  próximos botões, destino no painel e os números usados. Respostas
  guiadas são determinísticas (rápidas, sem custo, sempre iguais para
  os mesmos dados). Testado por `algoritimos/teste_lia.py`.
- `dashboard/lia_rosto.py` — o rosto (ilustração vetorial) nas 5
  expressões.
- `dashboard/app.py` — boas-vindas no centro no primeiro acesso (com
  4 portas: o que mais aparece, está aumentando, onde prestar atenção,
  olhar para frente), Lia na lateral depois disso (os 8 caminhos), e a
  navegação que ela consegue controlar. As abas viraram um seletor
  (o `st.tabs` do Streamlit não pode ser trocado pelo código), e aba,
  câncer, medida e camadas ficam em chaves próprias do session_state.

## Testes

- `algoritimos/teste_lia.py` percorre a árvore inteira (66 respostas
  com a base real de Rio Claro), clicando em todos os botões, e checa
  as regras (nada de orçamento, três níveis na projeção, expressão
  cautelosa quando o dado pede cuidado, texto livre no formato da Lia).
- Testado no navegador: boas-vindas, clique que leva o painel ao
  Planejamento, projeção, voltar, pergunta digitada levando ao câncer
  certo, foco que persiste ao trocar de aba, troca de cidade.
