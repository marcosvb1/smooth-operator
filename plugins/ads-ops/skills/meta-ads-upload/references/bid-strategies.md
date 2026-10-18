---
name: Meta Ads Bidding Strategies & Auction Mechanics
description: Guia operacional e técnico de estratégias de lance (bid_strategy) na Marketing API (v25/v26), mecânica do leilão do Meta, parâmetros obrigatórios por nível e diagnóstico de subentrega.
---

# Estratégias de Lance e Mecânica de Leilão — Meta Ads

Documentação técnica e operacional para configuração do campo `bid_strategy` via Marketing API (v25/v26), baseada na [documentação oficial de Bid Strategy da Meta](https://developers.facebook.com/documentation/ads-commerce/marketing-api/bidding/overview/bid-strategy).

---

## 1. A Equação do Leilão da Meta

Cada impressão é disputada em um leilão em tempo real baseado no **Valor Total (Total Value)**:

**Valor total = lance do anunciante × taxa de ação estimada + valor para o usuário (qualidade do anúncio)**

* **Lance do Anunciante (Bid):** Determinado pela estratégia de lance escolhida (`bid_strategy`) e pelo `bid_amount`.
* **Taxa de Ação Estimada (Estimated Action Rate - EAR):** Probabilidade prevista pelo modelo de machine learning de a pessoa realizar a conversão desejada.
* **Valor do Usuário (Ad Quality & Relevance):** Histórico de engajamento, retenção, taxa de rejeição pós-clique e feedback negativo na arte.

A estratégia de lance define diretamente como a plataforma manipula o componente **Lance do Anunciante** ao longo do dia e entre diferentes usuários.

---

## 2. Catálogo de Estratégias de Lance Ativas

| Enum da API | Nome na UI | Parâmetro Extra | Nível de Controle | Comportamento de Gasto |
|---|---|---|---|---|
| `LOWEST_COST_WITHOUT_CAP` | **Maior Volume** (Automático) | *Nenhum* (`bid_amount` não permitido) | Foco em volume | Gasta 100% do orçamento diário. |
| `LOWEST_COST_WITH_BID_CAP` | **Limite de Lance** (Bid Cap) | `bid_amount` (em centavos) | Controle estrito de lance unitário | Só gasta se o leilão custar ≤ `bid_amount`. Risco alto de subentrega. |
| `COST_CAP` | **Meta de Custo** (Cost Goal) | `bid_amount` (em centavos, atua como CPA alvo) | Controle de custo médio | Flutua os lances buscando manter a média geral próxima ao valor estipulado. |
| `LOWEST_COST_WITH_MIN_ROAS` | **ROAS Mínimo** | `min_roas` (inteiro base 10000) | Controle de retorno sobre investimento | Só dá lance para perfis com valor de compra estimado compatível com a meta. |

*(Nota: o antigo `TARGET_COST` foi permanentemente descontinuado a partir da v9.0).*

---

### A. `LOWEST_COST_WITHOUT_CAP` (Maior Volume / Automático)

* **Objetivo:** Capturar o máximo de resultados possíveis dentro do orçamento estipulado.
* **Mecânica:** O algoritmo ajusta dinamicamente os lances para cima ou para baixo para garantir que todo o orçamento seja consumido no intervalo de 24 horas.
* **Payload:**
  ```json
  {
    "bid_strategy": "LOWEST_COST_WITHOUT_CAP"
  }
  ```
* **Quando usar:**
  - Ponto de partida comum para captação de leads, mensagens (CTWA) e tráfego.
  - Lançamentos e testes de novos criativos onde o objetivo é acelerar a coleta de dados e sair rápido da fase de aprendizado.
* **Riscos / Armadilhas:**
  - Volatilidade de CPA em dias de concorrência atípica (Black Friday, finais de trimestre), pois a plataforma não hesitará em pagar lances mais altos para queimar a verba.

---

### B. `LOWEST_COST_WITH_BID_CAP` (Limite de Lance)

* **Objetivo:** Impedir que o Meta participe de leilões onde o lance individual seja considerado excessivamente caro.
* **Mecânica:** Impõe um teto intransponível no leilão unitário. Se o leilão exigir R$ 10,01 e o teto for R$ 10,00, a oportunidade é descartada.
* **Payload:**
  ```json
  {
    "bid_strategy": "LOWEST_COST_WITH_BID_CAP",
    "bid_amount": 1500
  }
  ```
  *(1500 centavos = R$ 15,00).*
* **Diferença Crítica (lance ≠ CPA final):**
  - O `bid_amount` no Bid Cap controla o **lance no leilão individual**, e **não** o custo por aquisição final. Por exemplo, se a taxa de conversão esperada for de 20%, um lance de R$ 10,00 pode resultar em um CPA real de R$ 50,00.
* **Quando usar:**
  - Mercados muito saturados ou anunciantes com margens brutas milimetricamente calculadas que preferem não veicular nada a pagar acima do teto.
* **Riscos / Armadilhas:**
  - **Subentrega Severa (Zero Gasto):** Se o `bid_amount` for inferior ao piso de mercado, o anúncio fica com status `ACTIVE`, mas registra R$ 0,00 de gasto e 0 impressões.

---

### C. `COST_CAP` (Meta de Custo / CPA Alvo)

* **Objetivo:** Maximizar o volume de conversões mantendo o custo médio ponderado por evento dentro de uma meta financeira estipulada.
* **Mecânica:** Diferente do Bid Cap, o Cost Cap permite que o algoritmo pague mais caro em determinados leilões mais promissores e economize em outros mais baratos, equilibrando a média ao longo da semana.
* **Payload:**
  ```json
  {
    "bid_strategy": "COST_CAP",
    "bid_amount": 2500
  }
  ```
  *(2500 centavos = meta de CPA de R$ 25,00).*
* **Quando usar:**
  - Campanhas de escala contínua (evergreen) onde a conta já possui histórico consolidado de conversões (>50 eventos/semana) e o negócio tem um CAC limite bem definido.
* **Riscos / Armadilhas:**
  - Conforme os públicos mais propensos à conversão se esgotam, o Meta pode desacelerar o ritmo de entrega caso não encontre mais usuários capazes de converter dentro do CPA estipulado.

---

### D. `LOWEST_COST_WITH_MIN_ROAS` (Retorno Mínimo sobre Gastos)

* **Objetivo:** Priorizar o valor financeiro da conversão em vez do número bruto de compras.
* **Mecânica:** O algoritmo avalia o histórico de ticket de compra dos usuários e lhes atribui uma probabilidade de receita. Lances são direcionados para carrinhos com maior potencial de retorno.
* **Payload:**
  ```json
  {
    "bid_strategy": "LOWEST_COST_WITH_MIN_ROAS",
    "min_roas": 20000
  }
  ```
  *(Representação em base 10.000: `20000` equivale a um ROAS mínimo de 2.0×; `15000` = 1.5×).*
* **Pré-requisitos Obrigatórios:**
  - Campanhas com objetivo de vendas (`OUTCOME_SALES`) rastreando o evento `Purchase` com parâmetro `value` e `currency` válidos enviados via Pixel ou Conversions API (CAPI).

---

## 3. Onde Configurar na API: CBO vs. ABO

A declaração correta da estratégia de lance depende da estrutura de orçamento da campanha:

### Em Campanhas CBO (Orçamento na Campanha)
* `daily_budget` reside na Campanha (`POST /act_{id}/campaigns`).
* `bid_strategy` **deve ser enviado exclusivamente na Campanha**.
* Todos os AdSets filhos herdam automaticamente a estratégia; tentar enviar `bid_strategy` no AdSet resulta em erro de validação.

### Em Campanhas ABO (Orçamento no AdSet)
* `daily_budget` reside nos AdSets (`POST /act_{id}/adsets`).
* Na Campanha, passe obrigatoriamente:
  ```json
  {
    "is_adset_budget_sharing_enabled": false
  }
  ```
  *(Omitir gera o erro subcode `4834011`).*
* No AdSet, **é obrigatório declarar `bid_strategy` explicitamente**:
  ```json
  {
    "bid_strategy": "LOWEST_COST_WITHOUT_CAP"
  }
  ```
  *(A campanha ABO não propaga estratégia default; omitir no AdSet gera o erro subcode `2490487`).*

---

## 4. Guia de Diagnóstico: Anúncio "Ativo" com R$ 0 de Gasto

Quando um anúncio com Bid Cap ou Cost Cap nasce `ACTIVE` e não gasta nem entrega impressões após 6 a 12 horas, siga este checklist:

1. **Ajuste de Lance Unitário:**
   - Aumente o `bid_amount` em **20% a 30%** para testar se o lance rompe a barreira de entrada dos leilões do dia.
   - Alternativamente, altere temporariamente para `LOWEST_COST_WITHOUT_CAP` por 24 a 48 horas para identificar o eCPA real de equilíbrio praticado pelo mercado antes de fixar um teto.
2. **Avaliação do Componente de Qualidade (EAR & Ad Quality):**
   - Se o criativo tiver CTR muito baixo ou feedback negativo, o algoritmo reduz a pontuação de qualidade na fórmula do leilão, exigindo lances artificialmente mais altos para vencer. Troque a arte ou melhore o gancho dos primeiros 3 segundos.
3. **Expansão de Audiência:**
   - Segmentações com público muito restrito (<50.000 pessoas) combinadas com Bid Cap ou Cost Cap quase sempre entram em subentrega. Abra a segmentação geográfica ou desative exclusões pontuais.
