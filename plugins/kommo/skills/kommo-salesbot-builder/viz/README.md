# Salesbot Viewer

Visualizador **read-only** de salesbots do Kommo. Abre um export e desenha o fluxo legível —
sem precisar abrir o construtor visual do Kommo nem decifrar o JSON stringificado na mão.

Companheiro da skill `kommo-salesbot-builder`: o builder **gera/valida** o export; este viewer
**lê** qualquer export (gerado aqui ou exportado de uma conta) e mostra a topologia.

## Como usar

Abra `salesbot-viewer.html` no navegador (duplo-clique já funciona — é arquivo único, zero deps,
roda offline). Depois:

- **Arraste** um `.json` de export pra janela, ou clique **Abrir bot**.
- **Ver exemplo** carrega um bot de demonstração embutido.
- `sample-bot.export.json` é um export sintético no formato real (wrapper) pra testar o "Abrir bot".

## O que ele aceita

Parsing tolerante — reconhece três formas da mesma coisa:

| Entrada | Origem típica |
|---|---|
| **Wrapper de export** (`model.text`/`model.positions` como **string** JSON) | "Exportar" da UI do Kommo; saída do `compile.py` |
| **IR** já parseado (`text`/`positions` como objeto) | `salesbot_model.parse_to_ir` |
| **Template** da skill (chave `lir`) | `templates/*.json` |

## O que ele mostra

- **Fluxo** — grafo **esquerda→direita** (igual ao construtor do Kommo; fan-outs se abrem na
  vertical, então os rótulos nunca colidem). Nós coloridos por tipo (mensagem, pausa, condição,
  distribuir, ação, gatilho, fim). Arestas **sólidas** = salto linear; **tracejadas roxas** =
  ramificação, com o critério no rótulo — liderado pelo valor que distingue o ramo (`"45160"`,
  `⏱ 1d`, `💬 recebida`, `contém "sim"`, `senão`); **passe o mouse** na aresta pra ver a
  condição completa. Decodifica os dois endereçamentos (`text` por step-id ↔ `positions` por
  block-id) e as ramificações via `actions[].links[].block` — não só `goto.block`.
- **Passos** — lista detalhada de cada bloco com seus handlers humanizados e as saídas.
- **JSON** — o export já **desempacotado** (blobs parseados), pra leitura.
- **Sidebar** — resumo, histograma de handlers, canais/status/usuários referenciados e um
  **alerta de ações que mexem em produção** (`change_status`, `change_responsible_user`,
  `distribution`, `set_tag`, `trigger`…), espelhando o gate de segurança da skill.
- **Verificação leve** — flagga goto pra step inexistente, `send_message` sem canal,
  `change_status` sem `pipeline_id`. Não substitui `validate.py --inventory` contra a conta-alvo.

## Limites

Read-only, client-side. Não resolve IDs ao vivo nem confirma `chat_source` — pra isso é o motor
da skill. Os ids exibidos são os do arquivo (em templates aparecem sentinelas tipo `-901`).
