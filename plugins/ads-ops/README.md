# ads-ops

Operação de mídia paga no Meta Ads e no TikTok Ads, para qualquer conta.

| Componente | O que faz |
| --- | --- |
| skill `meta-ads-upload` | Cria, atualiza, duplica e audita campanhas, adsets e ads no Meta. Usa o conector oficial do Meta Ads quando ele está na sessão e, sem ele, um runner Python na Graph API em dry-run por padrão. |
| skill `tiktok-ads-ops` | Playbook para criar e operar campanhas na TikTok Marketing API v1.3, direto ou via conector MCP. |
| comando `/ads-ops:setup` | Opcional. Cadastra perfis de conta num config local, sem tokens. |

## Instalação

```bash
/plugin marketplace add marcosvb1/smooth-operator
/plugin install ads-ops@smooth-operator
```

## Configuração

Se a sessão já tem o conector oficial do Meta Ads, ou um conector de TikTok Ads, não precisa configurar nada: as skills usam o login do conector e perguntam a conta. A configuração abaixo só é necessária para o runner do Meta ou para chamadas diretas à API do TikTok, ou para deixar contas padrão com nome.

1. Rode `/ads-ops:setup` para cadastrar as contas. O config fica em `./.claude/ads-ops.local.json` (projeto) ou `~/.claude/ads-ops.local.json` (usuário); a variável `ADS_OPS_CONFIG` aponta para outro caminho.
2. Defina os tokens como variáveis de ambiente, nunca no config:
   - `META_ACCESS_TOKEN_<PERFIL>` ou `META_ACCESS_TOKEN`
   - `TIKTOK_ACCESS_TOKEN_<PERFIL>` ou `TIKTOK_ACCESS_TOKEN`

O runner do Meta precisa de Python 3 com `requests`. Os relatórios de execução vão para `./ads-ops-runs/` (ou `$ADS_OPS_RUNS_DIR`).

## Regras que as duas skills seguem

- Tudo nasce pausado e passa por dry-run ou revisão antes de executar.
- Nada é deletado; o que sai do ar é pausado.
- IDs de conta vêm do perfil, de env vars ou do JSON do job, nunca do texto da skill.
