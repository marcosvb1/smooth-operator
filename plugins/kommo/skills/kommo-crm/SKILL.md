---
name: kommo-crm
description: >-
  This skill should be used to operate the Kommo CRM (ex-amoCRM) through API v4,
  for any configured account: queries and single-record CRUD, read-only funnel
  reports (volume per stage, snapshot, cohort, drift against a baseline),
  structural pipeline redesign with lead migration, conversations (talks,
  events, message history), lead-source creation and lead ingestion from forms
  or n8n via leads/complex, running/stopping a Salesbot on leads, and contact
  merge. Use whenever the request involves Kommo leads, contacts, companies,
  tags, tasks, notes, custom fields, pipelines, stages, stage hints, volumes,
  SLA, lead sources or cleanup — e.g. "quantos leads tem em cada etapa do
  funil", "mover lead de etapa no Kommo", "reorganizar o pipeline", "limpar
  etapas do funil", "buscar contato no Kommo", "unir contatos duplicados", "SLA
  de primeira resposta no Kommo", "criar fonte de lead", "mandar leads do n8n
  pro Kommo com a fonte certa", "list Kommo leads", "Kommo API v4 error on
  leads/contacts/pipelines". Includes approval gates before any write and
  readback after mutations. NOT for building or validating Salesbot JSON
  (kommo-salesbot-builder) nor for building widgets, Workers or private
  integration UIs (kommo-widget-builder).
---

# Kommo CRM

Skill operacional para o Kommo, em qualquer conta configurada. Classifique o pedido em um dos
modos e carregue só os recursos indicados. Credenciais, gates, paginação e validação valem para
todos os modos. Os caminhos abaixo são relativos a `${CLAUDE_PLUGIN_ROOT}/skills/kommo-crm/`.

## Roteamento

| Pedido | Modo | Recursos |
|---|---|---|
| Buscar/listar/criar/alterar uma entidade; mover um lead; tag, nota ou tarefa | **Operação pontual** | `references/endpoints.md`; para filtros, `references/pitfalls.md` |
| Volume por etapa, snapshot, baseline, cohort, export ou drift | **Relatório read-only** | seção "Modo relatório" + `references/report-spec.md` |
| Redesenhar/organizar funil; mexer em várias etapas; migrar leads; consolidar ou excluir etapas | **Pipeline design** | `references/pipeline-design-principles.md`, `references/pipeline-workflow.md`, `references/pipeline-api-quirks.md` |
| Conversas, mensagens, SLA, entrada × saída, histórico de eventos | **Conversas** | `references/talks-and-events.md` |
| Criar fontes de lead, atribuir lead a uma fonte, ingestão de formulário/n8n | **Fontes** | `references/sources-forms.md` |
| Unir contatos duplicados | **Merge** | `references/merge-contacts.md` |

Pedidos simples continuam simples: não carregue o workflow de pipeline para uma operação unitária
nem faça diagnóstico estratégico quando o pedido é só extração.

## Conta e credenciais

O config fica fora do plugin e **nunca guarda token**. É procurado em `$KOMMO_CONFIG`, depois
`./.claude/kommo.local.json` e por fim `~/.claude/kommo.local.json`:

```json
{
  "default_profile": "cliente-a",
  "profiles": {
    "cliente-a": { "domain": "cliente-a.kommo.com" }
  }
}
```

- Token: só em variável de ambiente, `KOMMO_ACCESS_TOKEN_<PERFIL>` ou `KOMMO_ACCESS_TOKEN`
  (`<PERFIL>` em maiúsculas, `-` vira `_`: `cliente-a` → `KOMMO_ACCESS_TOKEN_CLIENTE_A`).
- Domínio: `KOMMO_DOMAIN_<PERFIL>` > `profiles.<perfil>.domain` > `KOMMO_DOMAIN`.
- Se houver mais de um perfil e o pedido não deixar claro qual, **pergunte**. Nunca escolha por
  recência, volume ou palpite. O mesmo vale para marca e pipeline: uma conta pode abrigar várias
  marcas, e marca não é conta.
- Sem config, peça o subdomínio e sugira `/kommo:setup`. Se faltar o token, diga qual variável
  definir. Se o usuário colar um token na conversa, não grave nem repita.

Os scripts carregam tudo com `scripts/kommo_env.sh`:

```bash
source "${CLAUDE_PLUGIN_ROOT}/skills/kommo-crm/scripts/kommo_env.sh"
kommo_load_credentials <perfil>     # exporta DOMAIN e TOKEN sem imprimir o token
kommo_get "$DOMAIN/api/v4/account"  # GET com retry em 429
kommo_request PATCH "$DOMAIN/api/v4/leads/<ID>" '<json>'   # escrita, sem retry
```

Headers: `Authorization: Bearer $TOKEN` e `Content-Type: application/json`. Rate limit 7 req/s:
em loops, `sleep 0.18`; em 429, esperar 1s e fazer no máximo um retry. Com `curl`, use `-g` em
URLs com `filter[...][]`.

## Gates (resumo; regra completa em `references/safety-gates.md`)

- **READ (`GET`)**: autônomo. Listagens, buscas, contagens, dumps, snapshots e drift.
- **WRITE de 1 entidade**: mostrar perfil, endpoint, IDs e payload final; esperar OK explícito.
  Mudou o payload, pede de novo.
- **Gate explícito**: criar pipeline ou etapa; renomear/recolorir/reordenar etapas em lote;
  qualquer DELETE; status terminal (142/143) em mais de 1 lead; bulk de mais de 10 operações
  (amostra de 3 + total + duração); disparar Salesbot em leads reais.
- **Readback** depois de cada mutação. Não declare sucesso só pelo HTTP 2xx; se `name`, `sort`,
  `color`, `descriptions`, `pipeline_id` ou `status_id` divergirem, pare o lote.
- **A API rejeita** (não tente, não peça OK): PATCH de etapas em lote (405), DELETE de lead (405),
  cor fora da palette de 21 (400), qualquer PATCH em etapa de sistema, inclusive renomear 142/143
  (400), filtro de custom field em `/contacts`. Lista completa em `references/safety-gates.md`.

## Modo operação pontual

1. Identificar perfil e entidade.
2. Classificar como READ, WRITE, DELETE ou BULK e aplicar o gate.
3. Ler a receita em `references/endpoints.md`. Antes de qualquer query filtrada, ler
   `references/pitfalls.md`: filtros desconhecidos são ignorados em silêncio e devolvem dados que
   parecem certos.
4. Executar, fazer readback e devolver IDs e URL do recurso quando fizer sentido.

## Modo relatório (só `GET`)

| Modo | Comando | Resultado |
|---|---|---|
| Snapshot | `scripts/funnel_snapshot.sh <perfil> <pipeline_id>` | JSON, CSV e resumo Markdown |
| Cohort | `scripts/funnel_snapshot.sh <perfil> <pipeline_id> --with-leads` | Snapshot + CSV de leads ativos (PII) |
| Drift | `scripts/pipeline_drift.sh <perfil> <pipeline_id> [baseline.md]` | API × baseline em Markdown |
| Dump de contatos | `scripts/dump_contacts.sh <perfil> [saida.jsonl]` | JSONL com custom fields (PII) |

1. Resolver perfil e pipeline (`GET /api/v4/leads/pipelines` se o usuário só deu o nome).
2. Rodar drift antes do snapshot quando houver baseline (`./kommo-baselines/<perfil>_<pipeline_id>.md`,
   modelo em `references/baseline.template.md`).
3. O snapshot pagina cada etapa até `_links.next` sumir.
4. Mostrar o resumo e os caminhos gerados (`./kommo-reports/`, ou `$REPORT_DIR`).
5. Havendo drift, separar o que é fato da API do que está no baseline e sugerir a atualização; não
   editar o baseline sozinho.

Drift: exit `0` sincronizado, `1` drift encontrado (não é falha), `2` pré-requisito ausente ou
falha técnica. O `_leads.csv` e o dump contêm PII: não reproduza no resumo e confirme que
`kommo-reports/` está no `.gitignore` do projeto.

## Modo pipeline design

Use para qualquer mudança estrutural, mesmo quando o usuário diz só "organizar etapas" ou "limpar
o funil". Princípio: etapa é um estado exclusivo da decisão de compra; o que pode coexistir com
outro estado tende a ser custom field.

1. Snapshot inicial da estrutura, descriptions e volumes (rollback).
2. Diagnóstico de naming, duplicações, ordem, cores, hints, etapas paralelas e órfãs.
3. Proposta explícita antiga → nova, com `sort`, cor, hint, migração e exclusões; esperar OK.
4. PATCH estrutural uma etapa por vez, em ordem **decrescente** de `sort`, sempre com
   `name + sort + color + descriptions`.
5. Migrar os leads das etapas removidas e confirmar origem vazia.
6. Excluir só com contagem zero; snapshot final comparado com a proposta aprovada.
7. Atualizar o baseline e listar as pendências para o usuário.

Etapas de sistema (`is_editable: false`, inclusive 142/143) são read-only pela API. Cores só da
palette oficial de 21.

## Dados de uma conta específica

Mapas de pipelines, custom fields, enums e canais de uma conta são do usuário, não do plugin. Se
o projeto tiver um mapa (modelo em `references/account-map.template.md`), leia antes de operar e
trate como snapshot datado: confirme na API antes de afirmar o estado atual.

## Saída

- Comandos com `$TOKEN`, nunca o valor.
- Separar fato verificado, associação observada e hipótese.
- Informar a cobertura da paginação e o horário real da coleta.
- Não transformar volume por etapa em diagnóstico estratégico sem pedido.
- Em erro HTTP, usar a tabela de `references/endpoints.md`.

## Recursos

- `references/endpoints.md` — receitas da API v4, bots e tabela de erros.
- `references/pitfalls.md` — filtros ignorados e falhas silenciosas.
- `references/safety-gates.md` — gates completos e caminhos que a API rejeita.
- `references/report-spec.md` — contratos de JSON, CSV e Markdown dos relatórios.
- `references/pipeline-design-principles.md` — etapa × custom field, naming, hints e cores.
- `references/pipeline-workflow.md` — execução detalhada do refactor de pipeline.
- `references/pipeline-api-quirks.md` — restrições empíricas da API de etapas.
- `references/talks-and-events.md` — conversas, texto de mensagens, eventos e SLA.
- `references/sources-forms.md` — fontes de lead, `leads/complex` e tokens.
- `references/merge-contacts.md` — merge de contatos pela sessão da UI.
- `references/baseline.template.md` e `references/account-map.template.md` — modelos para o
  projeto do usuário.
- `scripts/kommo_env.sh` — resolução de credenciais e helpers HTTP.
- `scripts/funnel_snapshot.sh`, `scripts/pipeline_drift.sh`, `scripts/dump_contacts.sh` e
  `scripts/extract_pipeline_baseline.awk`.
- `scripts/test_scripts.sh` — testes locais sem credenciais nem rede.

## Fora deste escopo

- Salesbot (gerar, adaptar, validar JSON de import): `kommo-salesbot-builder`.
- Widget, integração privada, Worker e UI para gerenciar fontes dentro do Kommo:
  `kommo-widget-builder`. Criar a fonte pela API e ingerir leads com ela continua aqui
  (`references/sources-forms.md`).
