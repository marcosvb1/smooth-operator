# Gates de aprovação e caminhos que a API rejeita

Regras de conduta para qualquer chamada ao Kommo, nas três skills do plugin. Toda escrita
passa por aprovação do usuário; as categorias abaixo dizem quanto detalhe mostrar antes.

## READ (`GET`) — autônomo

Listagem, busca por ID, contagem, dump, snapshot, drift e inventário de IDs. Sem confirmação.

## WRITE individual (`POST`/`PATCH` de 1 entidade) — rascunho + OK

1 lead, 1 tag, 1 tarefa, 1 nota, 1 valor de custom field. Mostrar perfil/conta, endpoint, IDs e
o body essencial; esperar confirmação antes de executar. Qualquer mudança no payload depois do
OK invalida a aprovação.

## Gate explícito (inegociável) — rascunho + OK humano antes de executar

Rascunhar o payload e listar perfil/conta, endpoint, IDs afetados e impacto colateral. Esperar
um "pode fazer" explícito do usuário:

- **Criar pipeline** (`POST /api/v4/leads/pipelines`).
- **Criar etapa** (`POST /api/v4/leads/pipelines/{pipe}/statuses`).
- **Renomear, recolorir ou reordenar etapas em lote** (mais de 1 etapa, ou 1 etapa com impacto
  estrutural, como mudar `sort` e reordenar o funil).
- **DELETE** de qualquer entidade (pipeline, etapa, custom field, fonte, tag). Para etapa:
  migrar os leads, paginar de novo e confirmar contagem zero antes do DELETE.
- **Mover para status terminal** (142 = ganho, 143 = perdido) em mais de 1 lead.
- **Bulk write** (mais de 10 operações em loop, batch ou paginação): mostrar amostra de 3
  operações, total estimado e duração (rate limit 7 req/s); depois do OK, executar com
  progresso visível.
- **Disparar Salesbot** (`/bots/{id}/run`) em leads reais: o bot age sobre eles.
- **Import de Salesbot**: o `validate.py` é gate antes da entrega e o import manual na UI é o
  gate final (skill `kommo-salesbot-builder`). Bots com `change_status`, `distribution` ou
  `change_responsible_user` exigem listar o efeito em produção e confirmar.
- **Desinstalar widget**: revoga o long-lived token da integração e quebra tudo que depende
  dele (Workers, n8n). Upload de nova versão é rotina; desinstalar exige gate explícito
  (skill `kommo-widget-builder`).

## Readback depois de toda mutação

Fazer uma leitura focada dos campos alterados. Não declarar sucesso só pelo status HTTP. Se
`name`, `sort`, `color`, `descriptions`, `pipeline_id` ou `status_id` divergirem do pedido,
parar o lote e diagnosticar antes do próximo item.

Registrar mutações destrutivas num log local (`/tmp/kommo_destructive_<timestamp>.log`) com
perfil, endpoint e IDs.

## Caminhos que a API rejeita (não tentar, não pedir OK)

- `PATCH /api/v4/leads/pipelines/{id}/statuses` em lote (sem `{status_id}`) → **405**. Um PATCH
  por etapa, com `sleep 0.18`.
- `DELETE /api/v4/leads` e `DELETE /api/v4/contacts` → **405**. Não há delete de lead pela API.
  Para teste reversível, usar `unsorted/forms` e depois
  `DELETE /api/v4/leads/unsorted/{uid}/decline?user_id=<ID>` (apaga lead e contato provisórios).
- `PATCH` de cor fora da palette oficial de 21 → **400 NotSupportedChoice** em `path: color`.
- Qualquer `PATCH` em etapa de sistema (`is_editable: false`, inclusive renomear 142/143) →
  **400 NotSupportedChoice** em `path: id`. Renomear pela UI.
- Filtro de custom field em `/api/v4/contacts`: `filter[custom_fields_values]` → **400**;
  `filter[cf][id]` → **200, mas ignorado** (devolve tudo). Filtrar no cliente.
- `filter[contact_id]` e `filter[source_id]` em `/leads` → **ignorados** em silêncio.
- `POST /api/v4/sources` com token de integração comum → **400** "Integration needs widget to
  perform this operation". Precisa de uma integração com widget instalado.
- `/api/v4/sources` com a sessão do admin (client-side) → **400** "Only integrations can access
  this endpoint". Precisa de token de integração no servidor (padrão Worker).
- Merge de contatos: não existe endpoint público (veja `merge-contacts.md`).
- CRUD de Salesbot: não existe; criar/editar bot é pela UI (import de JSON).

## Apresentação

- Mostrar `curl` com `$TOKEN`, nunca o valor. Se o usuário colar um token na conversa, não
  repetir nem gravar; orientar a guardar em variável de ambiente.
- Em sucesso: IDs criados/alterados e a URL do recurso quando fizer sentido.
- Em erro HTTP: tabela de `endpoints.md` (401/402/403/404/429).
