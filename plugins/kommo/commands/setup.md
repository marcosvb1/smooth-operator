---
description: Cadastra contas do Kommo no config local do plugin kommo
argument-hint: "[nome-do-perfil]"
allowed-tools: Read, Write, Edit, Bash(mkdir:*), Bash(ls:*)
---

Configure os perfis de conta usados pelas skills `kommo-crm`, `kommo-salesbot-builder` e `kommo-widget-builder`. Argumento recebido: `$ARGUMENTS` (nome do perfil, opcional).

1. Pergunte onde salvar, recomendando a primeira opção:
   - `./.claude/kommo.local.json`, só para este projeto (recomendado);
   - `~/.claude/kommo.local.json`, para todos os projetos.
   Se o usuário escolher o projeto, confira se `.gitignore` cobre `.claude/*.local.json` e, se não cobrir, ofereça adicionar a linha. Ofereça também adicionar `kommo-reports/` (os relatórios de cohort e o dump de contatos têm dados pessoais).
2. Se o arquivo já existir, leia e mostre os perfis atuais antes de mudar qualquer coisa. Preserve o que já existe.
3. Pergunte um nome curto para o perfil, em minúsculas com hífen (ex.: `cliente-a`). Se a mesma conta tiver várias marcas, o perfil é a conta, não a marca.
4. Pergunte o subdomínio da conta (`<subdominio>.kommo.com`). Aceite a URL completa e grave só o host.
5. Pergunte se este perfil deve ser o `default_profile`. Com um perfil só, ele vira o default.
6. Grave o JSON neste formato, mesclando com o que já existia:

```json
{
  "default_profile": "cliente-a",
  "profiles": {
    "cliente-a": { "domain": "cliente-a.kommo.com" }
  }
}
```

7. **Nunca** grave tokens nesse arquivo. No fim, explique:
   - onde gerar o token: no Kommo, Configurações → Integrações → integração privada → aba "Chaves e escopos" → token de longa duração (se a aba não aparecer, preencher qualquer URL de redirecionamento e salvar);
   - qual variável de ambiente definir no shell ou no gerenciador de segredos, com o nome do perfil em maiúsculas e `-` trocado por `_`: `KOMMO_ACCESS_TOKEN_<PERFIL>` (ou `KOMMO_ACCESS_TOKEN` para todas as contas);
   - como testar: `source "${CLAUDE_PLUGIN_ROOT}/skills/kommo-crm/scripts/kommo_env.sh" && kommo_load_credentials <perfil> && kommo_get "$DOMAIN/api/v4/account" | jq .id` deve devolver o ID numérico da conta.

Se o usuário colar um token na conversa, não grave nem repita, e avise que ele deve ir para uma variável de ambiente.
