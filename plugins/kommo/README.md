# kommo

Operação do Kommo CRM (ex-amoCRM) pela API v4, para qualquer conta.

| Componente | O que faz |
| --- | --- |
| skill `kommo-crm` | Consultas e CRUD pontual, relatórios read-only de funil (volume por etapa, snapshot, cohort, drift contra baseline), redesenho de pipeline com migração de leads, conversas e eventos, fontes de lead e merge de contatos. Gates antes de toda escrita e readback depois. |
| skill `kommo-salesbot-builder` | Compila a partir de templates, adapta entre contas e valida o JSON de Salesbot no formato de import da UI. Resolve IDs ao vivo na conta-alvo e roda o validador antes de entregar. Não escreve copy nem cria topologias novas de fluxo. |
| skill `kommo-widget-builder` | Monta, empacota e publica widgets e integrações privadas (manifest, `script.js`, i18n, logos, dev mode, React skeleton, Card SDK) e o padrão de Cloudflare Worker para endpoints só de integração, como `/api/v4/sources`. |
| comando `/kommo:setup` | Cadastra perfis de conta num config local, sem tokens. |

## Instalação

```bash
/plugin marketplace add marcosvb1/smooth-operator
/plugin install kommo@smooth-operator
```

## Configuração

1. Rode `/kommo:setup` para cadastrar as contas (perfis). O config fica em `./.claude/kommo.local.json` (projeto) ou `~/.claude/kommo.local.json` (usuário); a variável `KOMMO_CONFIG` aponta para outro caminho. Formato:

   ```json
   {
     "default_profile": "cliente-a",
     "profiles": {
       "cliente-a": { "domain": "cliente-a.kommo.com" }
     }
   }
   ```

2. Gere o token no Kommo: Configurações → Integrações → criar ou abrir uma integração privada → aba "Chaves e escopos" → token de longa duração. Se a aba não aparecer, preencha uma URL de redirecionamento qualquer e salve.
3. Defina o token como variável de ambiente, nunca no config:
   - `KOMMO_ACCESS_TOKEN_<PERFIL>` (perfil em maiúsculas, `-` vira `_`: `cliente-a` → `KOMMO_ACCESS_TOKEN_CLIENTE_A`), ou
   - `KOMMO_ACCESS_TOKEN`, para uma conta só.

   `KOMMO_DOMAIN_<PERFIL>` ou `KOMMO_DOMAIN` substituem o domínio do config, se precisar.

Os scripts precisam de `bash`, `curl` e `jq` (kommo-crm) e de Python 3 sem dependências externas (kommo-salesbot-builder). Os relatórios vão para `./kommo-reports/` (ou `$REPORT_DIR`) e os baselines de pipeline ficam em `./kommo-baselines/`. Os relatórios de cohort e o dump de contatos têm dados pessoais: mantenha `kommo-reports/` no `.gitignore`.

## Regras que as skills seguem

- Leitura (`GET`) é autônoma. Toda escrita mostra perfil, endpoint, IDs e payload e espera o OK do usuário.
- Criar pipeline ou etapa, qualquer DELETE, status terminal em vários leads, lote de mais de 10 operações, disparo de Salesbot e desinstalação de widget pedem confirmação explícita.
- Depois de cada mutação, há leitura de conferência; sucesso não é declarado só pelo HTTP 2xx.
- Com mais de uma conta configurada e o pedido ambíguo, a skill pergunta qual usar. Nunca escolhe sozinha.
- IDs de conta (pipelines, etapas, campos, canais) vêm da API ou do usuário, nunca do texto das skills.
- Token nunca vai para arquivo, log ou conversa.

## Testes

```bash
bash plugins/kommo/skills/kommo-crm/scripts/test_scripts.sh          # sem rede nem credenciais
bash plugins/kommo/skills/kommo-salesbot-builder/tests/run_all.sh    # provas offline do validador
```

O `run_all.sh` usa um corpus sintético quando `SALESBOT_CORPUS` não está definido. Com uma pasta de exports reais, a prova fica mais forte.
