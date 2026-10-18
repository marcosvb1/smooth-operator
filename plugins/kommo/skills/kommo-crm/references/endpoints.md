# Kommo API v4 — Receitas curl

Endpoints da API v4. `DOMAIN` e `TOKEN` vêm do perfil resolvido por `scripts/kommo_env.sh` (domínio no config `kommo.local.json`, token em `KOMMO_ACCESS_TOKEN_<PERFIL>`). Nos exemplos, `TOKEN` é sempre a variável, nunca o valor.

Headers padrão em toda chamada:

```
Authorization: Bearer $TOKEN
Content-Type: application/json
```

**Rate limit:** 7 req/s (doc oficial: developers.kommo.com/docs/limitations). 429 = excedeu; 403 = IP bloqueado por violação repetida. Máx. 250 entidades por página/batch (recomendado 50 em escrita). Em loops, usar `sleep 0.18` entre requests.

**`curl` com `filter[x][]` exige `-g` (`--globoff`).** Sem ele o curl lê `[]` como range, falha com `bad range in URL` e, com `-s`, não imprime nada: parece um 204 legítimo. No zsh, colchetes sem aspas viram glob; use aspas ou URL-encode (`%5B`/`%5D`).

---

## 1. Funis de vendas (pipelines)

### Listar funis
```bash
curl -s -X GET "DOMAIN/api/v4/leads/pipelines" -H "Authorization: Bearer TOKEN"
```

### Criar funil com etapas
```bash
curl -s -X POST "DOMAIN/api/v4/leads/pipelines" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "name": "Nome do Funil",
    "is_main": false,
    "sort": 10,
    "_embedded": {
      "statuses": [
        {"name": "Novo Lead", "sort": 10, "color": "#99ccff"},
        {"name": "Qualificado", "sort": 20, "color": "#ffff99"},
        {"name": "Proposta Enviada", "sort": 30, "color": "#ffcc66"},
        {"name": "Negociação", "sort": 40, "color": "#ff8c69"},
        {"name": "Fechado Ganho", "sort": 50, "color": "#ccff66"}
      ]
    }
  }]'
```

### Editar funil
```bash
curl -s -X PATCH "DOMAIN/api/v4/leads/pipelines/PIPELINE_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Novo Nome"}'
```

### Deletar funil (destrutivo — confirmar antes)
```bash
curl -s -X DELETE "DOMAIN/api/v4/leads/pipelines/PIPELINE_ID" \
  -H "Authorization: Bearer TOKEN"
```

**Limites:** 50 funis/conta, 100 etapas/funil.

---

## 2. Etapas do funil (statuses)

### Listar etapas
```bash
curl -s -X GET "DOMAIN/api/v4/leads/pipelines/PIPELINE_ID/statuses" \
  -H "Authorization: Bearer TOKEN"
```

### Adicionar etapas
```bash
curl -s -X POST "DOMAIN/api/v4/leads/pipelines/PIPELINE_ID/statuses" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"name": "Nova Etapa", "sort": 25, "color": "#99ccff"}]'
```

### Editar etapa
```bash
curl -s -X PATCH "DOMAIN/api/v4/leads/pipelines/PIPELINE_ID/statuses/STATUS_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Nome Atualizado", "color": "#ffcc66"}'
```

### Deletar etapa (destrutivo)
```bash
curl -s -X DELETE "DOMAIN/api/v4/leads/pipelines/PIPELINE_ID/statuses/STATUS_ID" \
  -H "Authorization: Bearer TOKEN"
```

### Cores aceitas em etapas

Use somente a palette oficial de 21 cores em `pipeline-api-quirks.md`. Cores legacy como `#ffff99`, `#ffcc66`, `#99ccff` e `#c1c1c1` ainda podem aparecer em pipelines antigos, mas são rejeitadas ao tentar defini-las via PATCH.

---

## 3. Campos personalizados (custom fields)

### Listar campos
```bash
curl -s -X GET "DOMAIN/api/v4/ENTITY_TYPE/custom_fields" \
  -H "Authorization: Bearer TOKEN"
```

`ENTITY_TYPE`: `leads` | `contacts` | `companies` | `customers`

### Criar campos personalizados
```bash
curl -s -X POST "DOMAIN/api/v4/ENTITY_TYPE/custom_fields" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"name": "Campo Texto", "type": "text"},
    {"name": "Campo Número", "type": "numeric"},
    {"name": "Campo Data", "type": "date"},
    {"name": "Campo Checkbox", "type": "checkbox"},
    {"name": "Campo Select", "type": "select", "enums": [
      {"value": "Opção 1", "sort": 1},
      {"value": "Opção 2", "sort": 2}
    ]},
    {"name": "Campo Multiselect", "type": "multiselect", "enums": [
      {"value": "Tag A", "sort": 1},
      {"value": "Tag B", "sort": 2}
    ]},
    {"name": "Campo URL", "type": "url"},
    {"name": "Campo Textarea", "type": "textarea"}
  ]'
```

**Tipos válidos:** `text`, `numeric`, `checkbox`, `select`, `multiselect`, `date`, `date_time`, `url`, `textarea`, `radiobutton`, `streetaddress`, `smart_address`, `birthday`, `legal_entity`, `price`, `multitext`.

**Limite:** batches de 40 fields/POST.

### Editar campo
```bash
curl -s -X PATCH "DOMAIN/api/v4/ENTITY_TYPE/custom_fields/FIELD_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Novo Nome"}'
```

### Deletar campo (destrutivo — apaga dados)
```bash
curl -s -X DELETE "DOMAIN/api/v4/ENTITY_TYPE/custom_fields/FIELD_ID" \
  -H "Authorization: Bearer TOKEN"
```

---

## 4. Leads

### Listar leads (whitelist de filtros)
```bash
curl -s -X GET "DOMAIN/api/v4/leads?with=contacts&limit=50&page=1" \
  -H "Authorization: Bearer TOKEN"
```

**Filtros aceitos em `/leads` (outros são ignorados silenciosamente — ver `pitfalls.md`):**
- `filter[id][]=LEAD_ID` — por ID
- `filter[name]=substring` — busca por nome
- `filter[price]=N` ou `filter[price][from]=N&filter[price][to]=N`
- `filter[statuses][N][pipeline_id]=PID` + `filter[statuses][N][status_id]=SID` — por etapa
- `filter[pipeline_id][]=PID` — por funil
- `filter[created_at][from/to]`, `filter[updated_at][from/to]`, `filter[closed_at][from/to]` (epoch)
- `filter[responsible_user_id][]=USER_ID`
- `filter[custom_fields_values][FIELD_ID]=value`
- `query=text` — busca full-text (forma documentada). `filter[query]=` também funciona: testado em 12/10/2026, mesmos resultados, mas não é documentado

### Buscar lead por ID com embeds
```bash
curl -s -X GET "DOMAIN/api/v4/leads/LEAD_ID?with=contacts,catalog_elements,loss_reason,source_id" \
  -H "Authorization: Bearer TOKEN"
```

Embeds (`with=`) suportados: `contacts`, `catalog_elements`, `loss_reason`, `source_id`, `is_price_modified_by_robot`, `only_deleted` (separados por vírgula).

### Criar lead
```bash
curl -s -X POST "DOMAIN/api/v4/leads" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "name": "Nome do Lead",
    "price": 5000,
    "pipeline_id": 123,
    "status_id": 456,
    "responsible_user_id": 789,
    "custom_fields_values": [
      {"field_id": 111, "values": [{"value": "texto"}]}
    ],
    "_embedded": {
      "tags": [{"name": "IA"}]
    }
  }]'
```

### Mover lead de etapa
```bash
curl -s -X PATCH "DOMAIN/api/v4/leads/LEAD_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status_id": NOVO_STATUS_ID, "pipeline_id": PIPELINE_ID}'
```

### Atualizar campos do lead
```bash
curl -s -X PATCH "DOMAIN/api/v4/leads/LEAD_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "custom_fields_values": [
      {"field_id": 111, "values": [{"value": "novo valor"}]}
    ]
  }'
```

### Adicionar/remover tags de lead
```bash
curl -s -X PATCH "DOMAIN/api/v4/leads/LEAD_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tags_to_add": [{"name": "nova_tag"}],
    "tags_to_delete": [{"name": "tag_antiga"}]
  }'
```

---

## 5. Contatos

### Listar contatos
```bash
curl -s -X GET "DOMAIN/api/v4/contacts?limit=50" \
  -H "Authorization: Bearer TOKEN"
```

### Buscar contato por ID com leads vinculados
```bash
curl -s -X GET "DOMAIN/api/v4/contacts/CONTACT_ID?with=leads,customers,catalog_elements" \
  -H "Authorization: Bearer TOKEN"
```

### Listar todos os leads de um contato
Substitui `filter[contact_id]` que NÃO funciona em `/leads` (ver `pitfalls.md`).

```bash
curl -s -X GET "DOMAIN/api/v4/contacts/CONTACT_ID?with=leads" \
  -H "Authorization: Bearer TOKEN" | jq '._embedded.leads'
```

### Criar contato
```bash
curl -s -X POST "DOMAIN/api/v4/contacts" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "name": "Nome do Contato",
    "first_name": "Nome",
    "last_name": "Sobrenome",
    "custom_fields_values": [
      {"field_code": "PHONE", "values": [{"value": "+5511999999999", "enum_code": "WORK"}]},
      {"field_code": "EMAIL", "values": [{"value": "email@example.com", "enum_code": "WORK"}]}
    ]
  }]'
```

### Atualizar contato
```bash
curl -s -X PATCH "DOMAIN/api/v4/contacts/CONTACT_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Novo Nome"}'
```

---

## 6. Empresas

### Listar empresas
```bash
curl -s -X GET "DOMAIN/api/v4/companies?limit=50" \
  -H "Authorization: Bearer TOKEN"
```

### Criar empresa
```bash
curl -s -X POST "DOMAIN/api/v4/companies" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"name": "Nome da Empresa"}]'
```

---

## 7. Tags

### Listar tags
```bash
curl -s -X GET "DOMAIN/api/v4/ENTITY_TYPE/tags" \
  -H "Authorization: Bearer TOKEN"
```

### Criar tags
```bash
curl -s -X POST "DOMAIN/api/v4/ENTITY_TYPE/tags" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"name": "Tag Nova", "color": "option1"}]'
```

---

## 8. Tarefas

### Listar tarefas
```bash
curl -s -X GET "DOMAIN/api/v4/tasks?limit=50" \
  -H "Authorization: Bearer TOKEN"
```

### Criar tarefa
```bash
curl -s -X POST "DOMAIN/api/v4/tasks" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "text": "Descrição da tarefa",
    "complete_till": 1735689600,
    "entity_id": 123,
    "entity_type": "leads",
    "task_type_id": 1,
    "responsible_user_id": 789
  }]'
```

`task_type_id`: 1=Ligação, 2=Reunião, 3=Email.

---

## 9. Notas

### Listar notas de um lead
```bash
curl -s -X GET "DOMAIN/api/v4/leads/LEAD_ID/notes" \
  -H "Authorization: Bearer TOKEN"
```

### Adicionar nota
```bash
curl -s -X POST "DOMAIN/api/v4/leads/LEAD_ID/notes" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "note_type": "common",
    "params": {"text": "Texto da nota"}
  }]'
```

---

## 10. Webhooks

### Listar webhooks
```bash
curl -s -X GET "DOMAIN/api/v4/webhooks" \
  -H "Authorization: Bearer TOKEN"
```

### Criar webhook
```bash
curl -s -X POST "DOMAIN/api/v4/webhooks" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"destination": "https://meu-servidor.com/webhook", "settings": ["add_lead", "update_lead", "status_lead"]}'
```

---

## 11. Conta

### Info da conta
```bash
curl -s -X GET "DOMAIN/api/v4/account?with=users_groups,task_types" \
  -H "Authorization: Bearer TOKEN"
```

### Listar usuários
```bash
curl -s -X GET "DOMAIN/api/v4/users" \
  -H "Authorization: Bearer TOKEN"
```

---

## 12. Catálogos / produtos

### Listar catálogos
```bash
curl -s -X GET "DOMAIN/api/v4/catalogs" \
  -H "Authorization: Bearer TOKEN"
```

### Criar catálogo
```bash
curl -s -X POST "DOMAIN/api/v4/catalogs" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"name": "Produtos", "type": "regular"}]'
```

### Listar itens de um catálogo
```bash
curl -s -X GET "DOMAIN/api/v4/catalogs/CATALOG_ID/elements" \
  -H "Authorization: Bearer TOKEN"
```

---

## 13. Links entre entidades

### Vincular contato a lead
```bash
curl -s -X POST "DOMAIN/api/v4/leads/LEAD_ID/links" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"to_entity_id": CONTACT_ID, "to_entity_type": "contacts"}]'
```

### Listar links de uma entidade
```bash
curl -s -X GET "DOMAIN/api/v4/ENTITY_TYPE/ENTITY_ID/links" \
  -H "Authorization: Bearer TOKEN"
```

---

## 14. Salesbot

Não existe CRUD de bot pela API (criar/editar é pela UI; veja a skill `kommo-salesbot-builder`). O que existe:

- `GET /api/v4/bots`: lista; a coleção vem em `_embedded.items` (não `.bots`), com paginação real (`_page`/`_page_count`). Filtros: `filter[type_functionality][]` (`regular`/`greeting`/`marketing`/`nps`), `filter[id][]`, `with=favorite`.
- `GET /api/v4/bots/{id}`: só metadata, sem o fluxo.
- `POST /api/v4/bots/{id}/run`: dispara 1 bot. Body `entity_id` + `entity_type` (`leads`, `contacts` ou `customers`; `customers` exige o modo Clientes ativo na conta).
- `POST /api/v4/bots/run`: lote de até 100 `{bot_id, entity_id, entity_type}`, resposta 202.
- `POST /api/v4/bots/{id}/stop`: para o bot rodando na entidade (só `leads`).

### Disparar salesbot
```bash
curl -s -X POST "DOMAIN/api/v4/bots/BOT_ID/run" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"entity_id": LEAD_ID, "entity_type": "leads"}]'
```

Disparar bot em lead real é WRITE (o bot age sobre o lead); em mais de 10 leads, é BULK.

---

## Tratamento de erros

| HTTP | Significado | Ação |
|---|---|---|
| 401 | Token inválido/expirado | Gerar novo token na integração do Kommo e atualizar a variável de ambiente |
| 402 | Plano não suporta | Informar limitação ao solicitante |
| 403 | IP bloqueado (rate limit excedido) | Esperar; reduzir frequência |
| 404 | Entidade não encontrada | Validar ID |
| 429 | Rate limit (>7 req/s) | Sleep 1s e retry |
