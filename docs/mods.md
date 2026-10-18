# Mods do Claude Code: guia de estudo

Resumo da documentação oficial ([Mods overview](https://code.claude.com/docs/en/plugins/mods/overview) e subpáginas), lida em 2026-10-11 com o Claude Code v2.1.296. Os eventos e métodos mudam entre versões: quando este guia e os tipos gerados (`.claude-plugin/types/claude-code/index.d.ts`) discordarem, valem os tipos.

## O que é um mod

Um mod é um **plugin** cujo `hooks/hooks.json` tem a chave `modules`, apontando para um arquivo JS/TS (o *hooks module*). Esse arquivo exporta `register(on, options)` e registra funções que o Claude Code chama **dentro do próprio processo** quando algo acontece: uma tool call, um prompt enviado, um pedaço da interface sendo desenhado.

A diferença para o resto:

| | Mod | Settings hook | Skill | MCP |
| --- | --- | --- | --- | --- |
| O que é | Funções JS/TS rodando dentro do Claude Code | Comando shell/HTTP/prompt em `settings.json` | `SKILL.md` que o Claude lê | Processo externo que dá tools |
| Desenha na interface | Sim | Não | Não | Não |
| Use quando | Quer painel, faixa acima do prompt, comando próprio, ou reescrever um evento | Só bloquear/permitir/logar com um script | Instruções que você repete | Acesso a sistema externo |

Um mesmo plugin pode ter mod, skills e MCP juntos.

**Requisitos**: Claude Code v2.1.287+ no terminal (v2.1.286+ no Desktop). Mods vêm ligados por padrão. Não precisa de Node, bundler nem build: o Claude Code carrega `.js`/`.ts`/`.tsx` direto.

## Estrutura mínima

```
meu-mod/
  .claude-plugin/plugin.json   # manifest normal; mods não exigem campos extras
  hooks/hooks.json             # { "modules": ["./register.js"] }  (um caminho só)
  hooks/register.js            # export function register(on, options) { ... }
  types/index.d.ts             # só se usar $.state ou adicionar namespace ao $
  tests/*.test.ts              # opcional, rodados por `claude plugin test`
```

`options` traz os valores do `userConfig` declarado no manifest.

## O modelo: middleware

Cada hook recebe `($, e, next)`:

- `$`: a API do mod (`$.ui`, `$.fs`, `$.model`...). **Única** forma de sair do próprio código: o módulo não tem Node, `setTimeout`, rede nem disco.
- `e`: o evento, congelado (imutável). Para mudar, passe uma cópia ao `next`.
- `next(e)`: chama o próximo mod da cadeia e, no fim, o comportamento normal do Claude Code.

Com isso o hook faz uma de três coisas:

- **Observar**: faz algo e `return next(e)`.
- **Reescrever**: `return next({ ...e, text: e.text.trim() })`.
- **Responder**: retorna um resultado sem chamar `next` (ex.: `{ deny: 'motivo' }`), e nada depois roda.

Filtros (*matchers*) no 2º argumento: `on('tool.call', { tool: ['Edit', 'Write'] }, fn)`, aceitam valor, array ou regex (`/^mcp__github__/`).

Exemplo completo (conta tool calls, mostra no spinner, comando `/tally`):

```js
let calls = 0
export function register(on) {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'tally', description: 'Quantas tool calls' })
    return next(e)
  })
  on('tool.call', async ($, e, next) => {
    calls += 1
    $.ui.invalidate('ui.render')
    return next(e)
  })
  on('command.run', { command: 'tally' }, async () => ({ text: `${calls} tool calls` }))
  on('ui.render', { component: 'Spinner' }, async ($, e, next) =>
    next({ ...e, props: { ...e.props, suffix: ` · tool calls: ${calls}…` } }))
}
```

## Eventos principais

| Grupo | Eventos | O que dá para fazer |
| --- | --- | --- |
| Tools | `tool.call`, `tool.check`, `tool.describe` | Negar (`{ deny }`), responder sem rodar (`{ result }`), mudar argumentos, tentar de novo, esconder o resultado; em `tool.check`, decidir `allow`/`ask`/`deny` depois das regras de permissão |
| Prompts | `prompt.submit`, `prompt.compose`, `prompt.section`, `prompt.context`, `prompt.attachment`, `prompt.mention`, `skill.prompt`, `attribution.text` | Reescrever o prompt, anexar contexto só para o Claude (`context`), descartar (`{ drop }`), editar seções do system prompt |
| Turnos | `turn.start`, `turn.step`, `turn.complete` | Ler uso de tokens por request, trocar de modelo/effort num request, mostrar uma linha sob a resposta |
| Sessão | `session.start`, `session.end`, `session.compact`, `session.receive`, `session.send`, `session.append`, `session.measure` | Registrar comandos/tools no início, impedir compactação, filtrar mensagens entre sessões |
| Subagents | `agent.offer`, `agent.spawn` | Esconder um tipo de subagent, escolher o modelo ou negar |
| Comandos/config | `command.run`, `command.describe`, `config.set`, `config.describe` | Comandos próprios, esconder ou travar linhas do `/config` |
| Interface | `ui.render`, `ui.press`, `ui.input`, `ui.select`, `ui.close`... | Desenhar e reagir a cliques e digitação |
| Outros mods | `plugin.register`, `engine.create` | Recusar mods, estender o `$` com namespace próprio |
| Settings hooks | `classic.<Evento>` (ex.: `classic.Stop`) | Recebe o mesmo JSON que um settings hook recebe no stdin |

Toda chamada da API também é um evento (`fs.read`, `model.complete`...), então um mod anterior na cadeia pode observar ou recusar o que um mod posterior faz.

## API (`$`)

- **Comandos e tools**: `$.command.register` (com `immediate: true` roda mesmo com o Claude trabalhando) e `$.tool.register` (o Claude vê como `mcp__<plugin>__<nome>`; trate em `tool.call` com esse nome). Registre em `session.start`.
- **Modelo**: `$.model.complete({ model, system, prompt, maxTokens })` manda um prompt isolado; `$.model.fork({ prompt })` reaproveita a conversa (e o cache). Cobra do plano/API key do usuário. Checar `r.isAnswered`. Suporta cache com blocos `{ text, cache: true }`.
- **Background**: `$.clock.every/after` no lugar de `setInterval/setTimeout`; `$.ui.status` (linha fixa sob o prompt), `$.ui.toast`, `$.ui.log` (linha no transcript que o Claude não lê); `$.prompt.submit({ text })` inicia um turno.
- **Acesso**: `$.fs`, `$.process.run([...])` (sem shell, timeout 30 s), `$.http.fetch`, `$.mcp.call`, `$.env`, `$.settings.read`, `$.session.usage()` (contexto e limites do plano), `$.session.send` (mensagem para outra sessão ou subagent).
- **Estado**: variável de módulo (some a cada reload), `$.state` (reativo, dura a sessão, sobrevive a reload; precisa de `types/index.d.ts` e `"types"` no manifest) e `$.store` (JSON persistente entre sessões, 4 MiB, compartilhado entre sessões da máquina, sem atomicidade).

## Interface

- **Render sites próprios**: `Pane` (sidebar à direita em terminal largo/fullscreen, ou quadro acima do prompt) aberto com `$.ui.open({ id })`, e `AbovePrompt` (a faixa acima do prompt).
- **Sites do Claude Code que dá para redesenhar**: `Spinner`, `UserMessage`, `AssistantMessage`, `ToolUse`/`ToolResult`/`ToolGroup`, `AskUserQuestion`, `PromptHint`, `SessionMode`, entre outros. O **prompt de permissão não** pode ser alterado.
- **Elementos** via `const { Box, Text, Button } = $.ui.resolve(e)`: `Box` (flex), `Text`, `Button` (com `hotkey`), `Input`, `Select`, `Markdown`, `Code`, `Link`; `Svg` só no Desktop; `Raster` e `Image` só no terminal.
- Ciclo: um callback muda o estado, chama `$.ui.invalidate('ui.render')` (ou escreve em `$.state`) e o hook redesenha a árvore inteira.

## Regras que a análise estática exige

O `claude plugin validate` lê o código sem executar e lista `hooks:` e `calls:`. Para ele enxergar tudo:

- Escreva cada chamada por extenso: `$.store.get(...)`. Nada de `const ui = $.ui`, desestruturar `$` ou passá-lo para métodos/funções internas (pode passar para função de topo do mesmo arquivo).
- Nome do evento sempre string literal em `on(...)`.
- Não redeclare `on` dentro de `register`.
- Só ES modules, `import` estático de arquivos dentro do plugin; o único import "bare" permitido é `claude-code`.
- Um `on` por evento sem matcher (dois `session.start` sem filtro quebra o carregamento).

## Limites que mais pegam

- Hook: 10 s de execução própria (50 ms em `prompt.edit`); esperar `next` ou uma chamada `$` não conta, exceto `$.clock.sleep`. Hook que estoura é pulado.
- Hook que falha antes de chamar `next` é pulado, então um guarda de segurança **abre** por padrão. Para fechar, use `.catch(...)` e responda `deny` quando `next.called` for falso.
- `.catch`: 1 s. `$.http.fetch`: 30 s e 4 MiB. `$.fs`: 4 MiB por arquivo. Redesenho: até 10 por segundo.
- Nomes de comando/tool/pane: letras, dígitos, `_` e `-`, até 64 caracteres. Nome de plugin começando com `claude-` é recusado.

## Fluxo de desenvolvimento

1. `claude --plugin-dir ./meu-mod`: carrega sem instalar e recarrega a cada save (variáveis de módulo zeram; `session.start` roda de novo).
2. Na primeira carga interativa, o Claude Code gera `.claude-plugin/types/` (tipos exatos da versão) e um `tsconfig.json`, então `tsc -p ./meu-mod` funciona.
3. `claude plugin validate ./meu-mod` (`--strict` trata avisos como erro).
4. `claude plugin test` com `tests/*.test.ts` usando `claude-code/testing`: dispara eventos (`$.tool.call`, `$.command.run`...) e faz stub das respostas, sem sessão nem rede.
5. Para pedir ao Claude: a skill embutida `plugin-authoring` (ou `/plugin-authoring`). Ela escreve em `~/.claude/dev-mods/<sessão>/`, que é apagado depois; copie para o repo.
6. Publicar: listar no `.claude-plugin/marketplace.json` e subir a `version` (a cópia instalada é cacheada por versão).

**Na nuvem**: `validate` e `test` funcionam (verificado neste container com o exemplo acima, 1 teste passando). Mods rodam em sessões na nuvem, mas nada que desenham aparece lá; o mesmo vale para a extensão do VS Code e `claude -p`. Painéis e faixas só aparecem no terminal e no Desktop.

## Segurança

Mod roda com as permissões do usuário, sem sandbox: lê arquivos e variáveis de ambiente, vê todos os prompts e tool calls, pode aprovar tool calls antes de você ser perguntado e gasta seu uso de modelo. Antes de instalar um mod de terceiros, rode `claude plugin validate` e leia as linhas `hooks:` e `calls:`. Para desligar: `/plugin` (um mod), `--safe-mode` (uma sessão) ou `"disableAllHooks": true` (todos).

## Referências

- Exemplos oficiais: [anthropics/claude-code-playground › claude-code/mods](https://github.com/anthropics/claude-code-playground/tree/main/claude-code/mods) (`token-weather`, `blast-radius`, `replay-theater`).
- Mods embutidos com código e testes: [anthropics/claude-code › mods](https://github.com/anthropics/claude-code/tree/main/mods) (`diff`, `agents-md`, `sec-default`, `telemetry`).
- Catálogo da comunidade: [karanb192/awesome-claude-code-mods](https://github.com/karanb192/awesome-claude-code-mods), com milhares de mods escaneados e a navegação em [mods.aidojo.si](https://mods.aidojo.si/). Mostra o que o validator diz que cada mod lê, escreve, roda ou manda pela rede. O scan é independente, não da Anthropic.
- Repos de mods da comunidade para usar de modelo: [dougcunha/claude-mods](https://github.com/dougcunha/claude-mods) (marketplace com TSX e testes, mesma estrutura deste repo), [hamzafer/claude-code-mods](https://github.com/hamzafer/claude-code-mods), [OneWave-AI/claude-code-mods](https://github.com/OneWave-AI/claude-code-mods) e [hoobnn/hoobnn-agent-mods](https://github.com/hoobnn/hoobnn-agent-mods).
- Páginas da doc: [create](https://code.claude.com/docs/en/plugins/mods/create), [interface](https://code.claude.com/docs/en/plugins/mods/interface), [events](https://code.claude.com/docs/en/plugins/mods/events), [api](https://code.claude.com/docs/en/plugins/mods/api), [test](https://code.claude.com/docs/en/plugins/mods/test), [troubleshoot](https://code.claude.com/docs/en/plugins/mods/troubleshoot), [admin](https://code.claude.com/docs/en/plugins/mods/admin), [reference](https://code.claude.com/docs/en/plugins/mods/reference).
