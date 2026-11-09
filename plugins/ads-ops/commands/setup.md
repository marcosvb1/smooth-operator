---
description: Cadastra contas de Meta Ads e TikTok Ads no config local do ads-ops
argument-hint: "[meta|tiktok] [nome-do-perfil]"
allowed-tools: Read, Write, Edit, Bash(mkdir:*), Bash(ls:*)
---

Configure os perfis de conta usados pelas skills `meta-ads-upload` e `tiktok-ads-ops`. Este passo é opcional: quem usa só o conector oficial do Meta Ads ou um conector de TikTok Ads não precisa dele. Ele serve para o runner do Meta, para chamadas diretas à API do TikTok e para dar nome às contas usadas sempre. Argumentos recebidos: `$ARGUMENTS` (plataforma e nome do perfil, ambos opcionais).

1. Pergunte onde salvar, recomendando a primeira opção:
   - `./.claude/ads-ops.local.json`, só para este projeto (recomendado);
   - `~/.claude/ads-ops.local.json`, para todos os projetos.
   Se o usuário escolher o projeto, confira se `.gitignore` cobre `.claude/*.local.json` e, se não cobrir, ofereça adicionar a linha.
2. Se o arquivo já existir, leia e mostre os perfis atuais antes de mudar qualquer coisa. Preserve o que já existe.
3. Pergunte a plataforma (Meta, TikTok ou as duas) e um nome curto para o perfil, em minúsculas com hífen (ex.: `cliente-a`).
4. Colete os campos, um bloco por vez:
   - **Meta**: `ad_account` (com ou sem `act_`), `page_id`, `ig_user_id` (opcional), `api_version` (opcional, default `v25.0`).
   - **TikTok**: `advertiser_id`, `timezone` (ex.: `America/Sao_Paulo`), `currency` (ex.: `BRL`), `display_name`, `landing_page` (opcional), `pixel_id` (opcional), `mcp_write_tool` e `mcp_report_tool` (opcionais, nomes das tools MCP se a conta usa um conector), e `naming` (opcional: padrões de nome para `campaign`, `adgroup` e `ad`).
5. Pergunte se este perfil deve ser o `default_profile` daquela plataforma.
6. Grave o JSON neste formato, mesclando com o que já existia:

```json
{
  "meta": {
    "default_profile": "cliente-a",
    "profiles": {
      "cliente-a": { "ad_account": "act_...", "page_id": "...", "ig_user_id": "..." }
    }
  },
  "tiktok": {
    "default_profile": "cliente-a",
    "profiles": {
      "cliente-a": { "advertiser_id": "...", "timezone": "America/Sao_Paulo", "currency": "BRL", "display_name": "..." }
    }
  }
}
```

7. **Nunca** grave tokens nesse arquivo. No fim, diga quais variáveis de ambiente o usuário precisa definir no shell ou no gerenciador de segredos dele, com o nome do perfil em maiúsculas, com todo caractere que não é letra nem número trocado por `_`:
   - Meta: `META_ACCESS_TOKEN_<PERFIL>` (ou `META_ACCESS_TOKEN` para todas as contas)
   - TikTok: `TIKTOK_ACCESS_TOKEN_<PERFIL>` (ou `TIKTOK_ACCESS_TOKEN`)

Se o usuário colar um token na conversa, não grave e avise que ele deve ir para uma variável de ambiente.
