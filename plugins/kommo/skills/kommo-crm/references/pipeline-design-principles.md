# Princípios de desenho de pipeline Kommo

## Etapa = jornada de decisão de compra

Cada etapa do funil representa **onde o lead está na decisão de comprar**. Não é checkpoint burocrático, não é registro administrativo, não é status de processo paralelo.

### Teste rápido pra decidir "vira etapa ou vira CF?"

Pergunte: *"esse estado pode acontecer SIMULTANEAMENTE com outro?"*

- Se **sim** (lead pode estar em "Em negociação" E ter "Documentação enviada") → **Custom Field**.
- Se **não** (lead só pode estar em 1 lugar) → **Etapa**.

### Exemplo (funil comercial com apresentação/reunião)

| Conceito | Vira | Por quê |
|---|---|---|
| Lead respondeu? | Etapa ("Em contato") | Estado exclusivo da jornada |
| Apresentação marcada? | Etapa ("Apresentação agendada") | Estado exclusivo |
| Lead pagou? | Etapa terminal ("Venda ganha") | Estado exclusivo |
| Prova/avaliação/vistoria agendada ou realizada? | CF | Processo paralelo à negociação |
| Documentação enviada/completa? | CF | Processo paralelo |
| Reagendamento? | CF (contador) + tag | Lead continua na etapa, ganha sinal histórico |

## Naming consistente dos leads

Quando o cliente tem múltiplas campanhas/ciclos no mesmo funil, adotar prefixo unificado: `[CICLO] <Nome do contato>`.

Exemplos:
- `[PROD-26.2] Ana Souza` (produto PROD, ciclo 2026.2)
- `[EVT-26.1] João Lima` (evento EVT, ciclo 2026.1)

**Sempre pegar o nome do contato vinculado**, não o campo `name` do lead — porque imports podem ter contaminado o lead.name com origem do canal.

### Bug recorrente: campo `name` contaminado

Imports automáticos (panfletagem, formulário, disparo) podem subir leads com a origem do canal no campo `name` em vez do nome real. Sintomas:
- `panfletagem MARIA` (origem + nome)
- `PROMO VERAO` (nome de campanha em vez de pessoa)
- `Lead #12345678` (placeholder gerado quando nome veio vazio)

Quando detectar em batch, avisar o usuário pra corrigir a **fonte do import** (n8n, Typebot, formulário, import manual), não só renomear retroativamente.

## Tom dos hints (descriptions): "slack post", não "DM"

Vendedor lê o hint pra saber **o que fazer naquele estágio**. Não é DM individual, é instrução em mural — informa o time todo.

### Estrutura por hint

1. **Estado** ("lead respondeu", "tem data marcada") — situa o vendedor sobre onde o lead está
2. **Ação** ("marcar a apresentação", "confirmar presença") — o que fazer agora
3. **Transição** ("mover pra Y com data confirmada") — pra onde levar e quando

### Anti-patterns

| Anti-pattern | Por quê | Correção |
|---|---|---|
| 2ª pessoa direta ("Você tá tentando contato...") | Soa DM, não broadcast | "Atendimento em andamento, sem resposta…" |
| Mencionar gestor/auditoria | Vendedor lê pra agir, não pra entender arquitetura | Remover. Hint diz **o que fazer**, não **por que existe**. |
| Imperativo casual ("move pra X assim que ele responder") | Inconsistente com tom formal | "Mover pra X quando o lead responder." |
| Hint genérico ("Lead nesta etapa") | Não orienta ação | Sempre incluir estado + ação + transição. |
| Hint > 1000 chars | Tooltip ilegível | Cortar pelo essencial. O limite do Kommo é 1000, mas o alvo é ~200-400. |

### Níveis disponíveis

Kommo aceita 3 níveis de description por etapa: `newbie`, `candidate`, `master`. Default usar `newbie` (vendedor novo no time). Adicionar `master` se houver atalhos/decisões avançadas que confundiriam o júnior.

## Cores semânticas

Palette Kommo tem 21 cores. Usar gradiente que reflete progresso na decisão:

| Faixa | Cores | Quando |
|---|---|---|
| Cinza neutro | `#e6e8ea`, `#f2f3f4` | Entrada/intocado/limbo |
| Azul (pálido → forte) | `#d6eaff` → `#c1e0ff` → `#98cbff` | Processo iniciando, em movimento |
| Amarelo | `#fffeb2`, `#fffd7f` | Atenção leve, aguardando |
| Laranja | `#ffce5a`, `#ffdc7f` | Atenção/urgência, evento próximo |
| Rosa/coral | `#ffc8c8`, `#ff8f92` | Decisão iminente, momento da verdade |
| Magenta/lilás | `#eb93ff`, `#f3beff` | Alta atenção, próximo do fim |
| Verde sistema | `#CCFF66` (fixo) | Venda ganha — não escolhe |
| Cinza sistema | `#D5D8DB` (fixo) | Venda perdida — não escolhe |

Lista completa em `pipeline-api-quirks.md`.

**Pegadinha:** pipelines antigos têm cores LEGACY (`#ffff99`, `#ffcc66`, `#99ccff`, `#c1c1c1`) que existem no schema mas a API rejeita SETAR via PATCH. Sempre usar da palette oficial.

## Quando consolidar vs criar etapa

### Sinais pra CONSOLIDAR (mergear 2 etapas)

- Nomes semanticamente próximos (`Reunião inicial` + `COMPARECEU NA REUNIÃO`)
- Vendedores ficam em dúvida entre as duas
- Uma das duas tem fluxo de leads quase nulo
- Estados não exclusivos

### Sinais pra CRIAR etapa nova

- O gestor precisa visualizar um sub-estado com X leads parados
- Há automação/decisão diferente dependendo do estado (tipo "tentativa de contato" vs "em contato": automação roda só num)
- Estado é EXCLUSIVO (lead não pode estar em outro simultaneamente)

### Quando hesitar

Sub-estados burocráticos (`Avaliação`, `Documentação`) são tentação de virar etapa porque parecem milestone. Resistir — eles são processos PARALELOS à decisão, viram CF. Cf. teste rápido lá no topo.
