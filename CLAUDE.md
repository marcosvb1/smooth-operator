# smooth-operator

Repositório para desenvolver skills, plugins e mods do Claude. A ideia é que o repo funcione como um marketplace de plugins (`.claude-plugin/marketplace.json` na raiz, um plugin por pasta).

## Qual ferramenta usar

| Vou criar | Use | Observações |
| --- | --- | --- |
| Plugin do Claude Code | `/plugin-dev:create-plugin [descrição]` | Fluxo guiado em 8 fases (descoberta → componentes → design → estrutura → implementação → validação → teste → README). |
| Skill avulsa | `skill-creator` | Cria e melhora skills, e roda evals e benchmarks. |
| Mod (muda a UI ou o comportamento do Claude Code) | skill embutida `plugin-authoring` | O plugin-dev **não** cobre mods. |
| Plugin do Cowork | `create-cowork-plugin` (cowork-plugin-management) | Hooks e commands do Claude Code não valem lá. |
| Servidor MCP | `mcp-server-dev` ou `mcp-builder` | |

### plugin-dev (claude-plugins-official)

- **Skills de referência**, que carregam sozinhas quando o assunto aparece: `plugin-structure` (layout e `plugin.json`), `skill-development` (SKILL.md e descriptions que disparam bem), `agent-development` (subagents e exemplos `<example>`), `command-development` (slash commands e `allowed-tools`), `hook-development` (PreToolUse, Stop, SessionStart…), `mcp-integration` (`.mcp.json` com stdio, SSE ou HTTP) e `plugin-settings` (`.claude/<plugin>.local.md`).
- **Agents**: `agent-creator` gera um subagent a partir de uma descrição, `plugin-validator` checa a estrutura e o manifest, e `skill-reviewer` revisa a qualidade de uma skill.
- **Lacuna**: quase não cobre o `marketplace.json`, então essa parte é manual.

### Mods (`plugin-authoring`)

Um mod é um plugin cujos hooks são código TS/TSX que roda dentro do Claude Code: painéis ao vivo, faixa acima do prompt, status line, toasts, slash commands, bloqueio ou reescrita de tool calls (`tool.call`), alteração do prompt (`prompt.submit`) ou do system prompt (`prompt.compose`), tools, subagents e timers.

Estrutura mínima:

```
<mod>/
  .claude-plugin/plugin.json   # { "name", "version", "description" }
  hooks/hooks.json             # { "modules": ["./register.tsx"] }
  hooks/register.tsx           # export const register: Register = (on, options) => { ... }
  types/index.d.ts             # só se usar $.state
```

Cada hook recebe `($, e, next)`: `$` é a API do engine, `e` é o evento e `next(e)` repassa o evento adiante. `$.state` guarda valores durante a sessão e `$.store` guarda entre sessões.

Para checar: `claude plugin validate <mod>`, `tsc -p <mod>` e `claude plugin test <mod>` (com testes `*.test.ts`).

Mods criados numa sessão na nuvem ficam no container e somem quando a sessão acaba, então commite-os neste repo.

## Antes de commitar

- Plugins: rode o agent `plugin-dev:plugin-validator`.
- Skills: rode o agent `plugin-dev:skill-reviewer`.
- Mods: rode `claude plugin validate`, `tsc` e `claude plugin test`.

## Distribuição

Liste cada plugin ou mod no `.claude-plugin/marketplace.json` da raiz. A instalação é `/plugin marketplace add marcosvb1/smooth-operator` uma vez e depois `/plugin install <nome>@smooth-operator`. Skills avulsas ficam em `skills/` e entram no marketplace por uma entrada com `"source": "./"`, `"strict": false` e a lista `"skills"` (veja `skills/README.md`).
