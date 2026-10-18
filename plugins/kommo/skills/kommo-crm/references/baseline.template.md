# Baseline de pipeline — <NOME DO PIPELINE>

Modelo de baseline para o `scripts/pipeline_drift.sh`. Copie para
`./kommo-baselines/<perfil>_<pipeline_id>.md` (ou passe o caminho como 3º argumento)
e preencha com os dados conferidos na API. O script lê:

- a linha `**Pipeline:**`, usando o primeiro texto entre crases como nome do pipeline;
- a **última** tabela cujo cabeçalho começa com `| sort | id | nome`. Tabelas antigas
  podem ficar acima, como histórico; colunas extras depois de `nome` são ignoradas.

**Pipeline:** `<Nome exato do pipeline na API>`
**Pipeline ID:** `<PIPELINE_ID>`
**Conferido em:** <AAAA-MM-DD>, via `GET /api/v4/leads/pipelines/<PIPELINE_ID>/statuses?with=descriptions`

## Estrutura atual

| sort | id | nome | cor | hint (newbie) |
|---:|---:|---|---|---|
| 10 | <ID_INCOMING> | Incoming leads | `#c1c1c1` | (system) |
| 20 | <STATUS_ID> | <Etapa 1> | `#e6e8ea` | <estado + ação + transição> |
| 30 | <STATUS_ID> | <Etapa 2> | `#d6eaff` | <estado + ação + transição> |
| 10000 | 142 | <nome da etapa de ganho> | `#CCFF66` | (system) |
| 11000 | 143 | <nome da etapa de perda> | `#D5D8DB` | (system) |

## Volumes na data do baseline (opcional)

| etapa | leads |
|---|---:|
| <Etapa 1> | <N> |

## Modelo operacional

- Quem move os leads (manual, Salesbot, Pipeline Digital) e em que momento.
- Convenção de nome dos leads (ex.: `[CICLO] <Nome do contato>`).
- O que é custom field e não etapa (estados paralelos à decisão de compra).

## Pendências

- <CFs propostos e não criados, automações a ajustar, hints de system stages a preencher pela UI>
