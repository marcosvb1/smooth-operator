# Templates — esqueletos de IR de referência (sem copy)

Cada template é um **esqueleto de IR sem copy**, extraído da *estrutura* de um bot real que
importou sem erro. Serve como ponto de partida estrutural; **não é conteúdo para entregar**.
Quem decide copy e fluxo é o chamador; o template só dá a forma do grafo já provada (topologia,
`goto`, `block_uuid` e o espelhamento `text` ↔ `positions` preservados).

Estrutura de um template:

- `meta` — `name`, `pattern`, `description`, `channels` e `source_bot` (nome do arquivo-fonte
  que o `roundtrip_templates.py` procura no corpus; no corpus sintético do `tests/run_all.sh`,
  é o próprio template compilado com valores fictícios).
- `slots` — o que preencher: `name`, `kind`, `required`, `hint` e, nos numéricos, `sentinel`.
- `lir` — o esqueleto. Slots de texto aparecem como a string `"<<nome>>"`; slots numéricos (IDs,
  delays) aparecem como o inteiro negativo do `sentinel` (ex.: `-901`).

## Tipos de slot

- **copy** (`text`): texto livre (mensagens, nome do bot). Vem do chamador, sempre.
- **id** (`chat_source`, `status`, `pipeline`, `user`, `custom_field`, `enum`): resolvido na
  conta-alvo com `resolve_ids.py`. Nunca reusar ID de outra conta.
- **delay**: segundos.
- **raw**: valor inserido como está (ex.: placeholder `{{lead.cf.<FIELD_ID>}}`).

Compilar: `python3 scripts/compile.py templates/<nome>.json --values vals.json --inventory
/tmp/inv.<perfil>.json --out bot.json` (o `compile.py` roda o `validate.py` no fim).

## Lista

| Template | Forma | Slots principais |
|---|---|---|
| `welcome-redirect` | 1 mensagem de boas-vindas + fim | `welcome_text`, `chat_source` |
| `cadence-followup` | mensagem → espera (timer/resposta) → lembrete → espera → ramifica (status/campo) | `reminder_text`, canais, delays, status/pipeline, campos |
| `post-sale-nurture` | sequência de 5 mensagens com timers + encerra conversa | `msg_1..5`, `delay_1..4_s` |
| `set-lead-name` | define o nome do lead a partir do primeiro nome do contato | `bot_name` |
