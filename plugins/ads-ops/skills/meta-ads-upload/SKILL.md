---
name: meta-ads-upload
description: |
  This skill should be used whenever the user wants to CHANGE something in Meta (Facebook/Instagram) Ads: create, edit, duplicate, move, pause, activate, rename, change budget, bid, targeting or placements, swap the creative, or upload a video or image for a campaign, ad set, or ad, in any account. Also when a long Meta ID (120…, act_…) shows up and the user wants to act on it. Triggers: "create an adset", "clone this campaign", "swap the creative on ad 120...", "turn this Instagram post into an ad", "sobe esse anúncio", "cria adset", "clona a campanha", "troca o criativo", "duplica o ad", "ativa esse conjunto", "pausa a campanha", "aumenta o orçamento", "muda o público". Use it even for small asks ("só ativa aí", "só troca a URL"): that is where money leaks. Auditing ad sets and naming before creating is in scope. Not for reporting, dashboards, exports, previews, or n8n/Sheets integrations.
---

# Meta Ads Upload

Toda escrita no Meta Ads gasta dinheiro real, e quase nenhum erro aparece como erro. A API responde `{"success": true}` para campo que não gravou, mascara rate limit como "Invalid parameter" e devolve na leitura campos que recusa na escrita. Um plano que "parece certo" não é evidência de nada.

O trabalho desta skill é **transformar um pedido num plano selado**: chamadas completas, sem placeholder, com readbacks e critérios de parada. O plano é mostrado ao usuário e só é executado depois do OK explícito dele.

## Fluxo

1. **Interpretar.** Se faltar decisão estratégica (orçamento, público, objetivo, datas), pergunte. Não decida pelo usuário.
2. **Resolver conta e rota** (seção 1).
3. **Montar o payload inteiro** (seção 2).
4. **Preflight** (seção 3).
5. **Mostrar o plano:** conta, ordem das operações, payload de cada chamada, o que será relido depois e qual valor prova que deu certo. Esperar o OK explícito.
6. **Executar** exatamente o plano aprovado, direto ou pelo agent `meta-ads-operator` (veja "O contrato com o operator").
7. **Reler e comparar** cada objeto alterado com o que foi enviado. Só então dizer que deu certo.

Se o plano precisar mudar durante a execução, pare: novo preflight, novo plano, novo OK.

## Referência local do projeto

Antes de começar, procure no projeto uma referência local de Meta Ads: um doc de IDs por conta, de rotas ou de convenções de nome (por exemplo uma skill ou regra local, ou um `docs/references/meta-ads/`). Quando existir, ela vence os defaults desta skill para IDs, rotas e nomenclatura. IDs nunca saem de memória nem do texto da skill.

## 1. Resolver a conta e a rota

Rotas mudam: conector some entre sessões, webhook novo vira default, conta que entrava por um caminho passa a entrar por outro. **Escolha a rota por capacidade, não por nome**, respondendo nesta ordem:

**a) A conta é alcançável por esta rota?** Cada rota enxerga um conjunto de contas. Errar isso não dá erro claro: dá "não encontrei a conta" ou silêncio.

**b) A rota fecha o payload inteiro?** Ferramenta tipada é mais segura (sem double-encoding, erro com subcode legível), mas tem schema chapado. Se o payload precisa de qualquer um destes, a tipada pode não servir e o caminho é a Graph API:

| Campo | Por que dói perder |
|---|---|
| `url_tags` | sem UTM o ad some do analytics, e `url_tags` é **imutável**: não existe "sobe agora e corrige depois" |
| `lead_gen_form_id` | instant form exige o objeto `call_to_action.value`, não o CTA chapado |
| `object_story_spec` / `asset_feed_spec` | creative composto, par feed+stories, carrossel |
| `source_instagram_media_id` | boost de post ou reel orgânico e partnership ads |
| CTA por `child_attachment` | carrossel sem isso renderiza sem botão |

**c) A rota honra `validate_only`?** Isso varia por rota **e por operação**, sobretudo em rotas próprias (webhooks, proxies): ele pode funcionar na criação e ser ignorado no update, ou ser engolido e o POST criar de verdade. Na dúvida, trate todo POST como mutação real.

**d) A rota diagnostica?** Quando um erro vier genérico ("Invalid parameter", sem subcode), outra rota para a mesma conta costuma devolver o erro real do Graph com `error_subcode` e `error_user_title`. Rodar o mesmo payload pela outra rota é mais barato que adivinhar o campo culpado.

**e) A rota sobe mídia?** Subir imagem (`POST /act_.../adimages`) e criar objeto são capacidades diferentes. Um app sem a permissão responde `(#3) Application does not have the capability`: isso é **determinístico**, não é rate limit, e retry ou `sleep` não resolvem. No conector oficial, `ads_creative_upload_media` com `upload_source: URL` exige URL pública. **Escolha a rota de upload no plano, antes de executar.**

### As rotas deste plugin

1. **Conector oficial do Meta Ads (preferido).** Se a sessão tiver as tools `ads_*` (por exemplo `ads_get_ad_accounts`, `ads_create_campaign`, `ads_create_ad_set`, `ads_create_ad`, `ads_create_creative`, `ads_creative_upload_media`, `ads_update_entity`, `ads_get_ad_entities`), use-as. Não precisa de token nem de `/ads-ops:setup`. Descubra conta, página e Instagram com `ads_get_ad_accounts`, `ads_get_ad_account_pages` e `ads_get_ig_accounts` e confirme com o usuário qual usar.
   - `ads_activate_entity` e `ads_boost_ig_post` com `confirmed: true` gastam dinheiro: só depois do resumo (conta, budget, público, datas, link) e do OK.
   - Para duplicar um item só, passe `source_campaign_id`, `source_adset_id` ou `source_ad_id` na tool de criação.
   - Se uma chamada falhar, use `ads_get_errors` antes de tentar de novo.
2. **Graph API crua**, por um conector genérico de Graph ou pelo runner, quando a tipada não fecha o payload (tabela acima).
3. **Runner Python** (seção 6): sem conector na sessão, ou para o que o conector não cobre bem, como copiar a árvore inteira com `/copies` e `deep_copy`, jobs em lote a partir de JSON e numeração automática de ad sets.

## 2. Montar o payload

Leia a referência da entidade antes de escrever qualquer chamada: `references/meta-ads-endpoints.md` (endpoints e payloads), `references/adset-objectives-destinations.md` (objetivo × optimization goal × destination × promoted object), `references/bid-strategies.md` (`bid_strategy`, CBO × ABO, subentrega) e `references/placement-targeting.md` (posicionamentos). Os templates em `templates/` mostram o shape de cada job.

O que mais quebra em silêncio:

- **Targeting:** `POST` de `targeting` **substitui o objeto inteiro**, não faz merge. Remonte idade, geo e `advantage_audience` junto do placement, senão o que você esqueceu volta ao default calado. Teto rígido de idade exige `advantage_audience: 0`.
- **Placement:** o Explorar do IG é `explore_home`; `explore` é aceito no POST mas **ignorado calado** (pelo menos a partir da v26). Readback de placement é sempre pelo `effective_*`, nunca só pelo campo enviado.
- **Creative estático com par feed+stories** = 1 ad com `asset_feed_spec` e **três regras**: story/reels (FB+IG) → arte vertical, feed (FB+IG) → arte de feed, catch-all `{}` → arte de feed. Regra só de Instagram, ou sem catch-all, deixa o resto dos placements a critério da Meta. Vídeo feed+vertical tem o mesmo shape com `video_label`.
- 🔴 `link_data` sem `image_hash` cria ad **sem mídia** e sem erro. O readback confere hash ou vídeo no creative.
- **Carrossel:** CTA nos dois níveis (raiz e cada card). 4:5 renderiza mal em Stories e Reels.
- **Vídeo:** `image_url` **ou** `image_hash` no `video_data`, nunca os dois (a leitura devolve ambos, a escrita rejeita).
- 🔴 **`degrees_of_freedom_spec` se copia de creative vivo, nunca se escreve à mão.** Com DOF montado à mão a API costuma devolver `Invalid parameter` sem nome de campo; com o DOF lido de um creative ativo do mesmo formato na mesma conta (`GET /{creative_id}?fields=degrees_of_freedom_spec`), passa. Reaproveite o objeto inteiro.
- **CBO × ABO:** em CBO, `bid_strategy` vai só na campanha; em ABO, vai em cada ad set (`references/bid-strategies.md`). O runner só manda `bid_strategy` no ad set se o input tiver o campo.
- **Unidades:** `daily_budget`, `daily_min_spend_target` e `bid_amount` são na **menor unidade da moeda** da conta (centavos para BRL e USD; moedas sem decimal, como JPY, vão pelo valor de face). O piso de gasto só é validado na ativação e a Meta limita a razão piso/orçamento: confira o piso como % do orçamento da mãe. Piso percentual (`min_budget_spend_percentage`) só grava pela interface.
- **Boost de post existente:** para saber se a publicação já foi anunciada, compare `source_instagram_media_id`. O ID `effective` ads-only é uma cópia e não prova repostagem.
- 🔴 **Menores de idade:** a Meta restringe muito a segmentação de 13-17 anos (sem interesses, objetivo e placements limitados, geo fina pode não sobreviver). Confira as regras atuais antes de montar, e não misture menor e maior no mesmo ad set: isso se decide no briefing, não na correção. Categorias especiais (crédito, emprego, moradia, temas sociais) também restringem segmentação.
- **Creative é imutável.** Trocar arte ou texto é sempre creative novo. O ad pode ser reapontado para ele (`POST /{ad_id}` com `creative`, que é o que o modo `update` do runner faz), mas isso reinicia revisão e aprendizado; para preservar o histórico do ad antigo, crie ad novo e pause o antigo.
- **Nomenclatura:** siga a convenção da conta (audite os nomes existentes) ou a da referência local. Sem nenhuma das duas, pergunte.

## 3. Preflight, antes de mostrar o plano

- **Abra cada arte e olhe.** "Entregue" não é "finalizada": cace placeholder de vídeo, caixa branca, lorem, texto cortado e proporção errada.
- **Audite a numeração existente** (`ads_get_ad_entities` no nível de ad set, ou `--mode audit` no runner) antes de criar ad set novo, senão nasce um `03` duplicado.
- **Resolva todo ID.** Nenhum placeholder sobrevive ao plano.
- **Declare os readbacks:** o que será relido depois de cada escrita e qual valor prova que deu certo.

## 4. Invariantes, em qualquer rota

- **`PAUSED` na criação e na duplicação.** Quem ativa é o usuário.
- **`url_tags` em todo creative, em qualquer destino** (formulário nativo e WhatsApp inclusive), salvo quando o projeto definir outra regra. Só fica sem quando a API recusa o campo, e isso se prova por `validate_only`, não se presume.
- **Nunca apagar campanha.** Pausar. Histórico apagado não volta.
- **`{"success": true}` não é prova.** Releia o objeto e compare campo a campo com o que foi enviado.
- **Exceção ao diff:** `location_types` voltar `["frequently_in","home","recent"]` quando você mandou `["home","recent"]` **não é desvio**. É a Meta injetando, não sai por reescrita e os dois encodings carregam a mesma opção. Não liste como achado nem abra pendência; no plano, avise que o readback pode voltar assim.
- **Verifique cópia por conteúdo, não por ID.** `/copies` sempre gera `creative_id` novo. Compare `image_hash`/`video_id`, CTA e `url_tags`.
- **Erro genérico não é veredito.** "Invalid parameter" sem subcode pode ser rate limit, transporte (query string × body) ou campo sobrando. Retry até 3x com backoff resolve o transitório; **3 falhas idênticas seguidas são determinísticas**: pare e desconfie do transporte. Para achar o campo culpado, **monte do mínimo que passa para cima**, um campo por vez, com `validate_only`. Bissectar por subtração de um payload cheio costuma falhar em todos os ramos e não ensinar nada. Antes de montar um spec complexo, leia o objeto vivo equivalente em vez de inventar o shape.
- **Espace as mutações.** Rotas próprias (webhooks, proxies) podem limitar a vazão; confira o limite antes de mandar um lote, porque lote apertado falha no meio e parece rejeição de campo. O runner espera só 0,3s entre chamadas.
- **Activity Log não serve para auditoria recente**: pode atrasar dias. Cross-check de curto prazo é por `created_time`/`updated_time` do objeto.
- **Depois de qualquer edição pela interface, releia `url_tags` por string exata.** Editar creative no gerenciador cria creative novo, e o UTM some em silêncio.

## 5. Duplicar

Use o endpoint nativo `/{id}/copies` em vez de recriar à mão: ele preserva pixel, público e creative. `deep_copy: true` clona os filhos, `status_option: "PAUSED"` e `rename_suffix` evitam nome duplicado; ad set muda de campanha por `campaign_id` e ad muda de ad set por `adset_id`. O limite é de 3 ad sets síncronos e 51 assíncronos, então campanha grande vai em lotes.

## O contrato com o operator

O agent `meta-ads-operator` é o braço mecânico: executa um plano selado e nada mais. Use-o quando quiser separar quem decide de quem executa.

- **A skill, no contexto principal:** interpreta o pedido, resolve conta, rota e IDs, monta o payload inteiro, roda o preflight, declara ordem, readbacks e critérios de bloqueio, mostra o plano e coleta o OK.
- **O operator:** confere que o plano está íntegro e dentro do escopo, executa exatamente as chamadas declaradas, na ordem, registra IDs e respostas, e para no primeiro mismatch.

Aprovação dada dentro do subagent não vale: o OK acontece no contexto principal, sobre o plano final.

## 6. O runner Python

Tudo fica em `${CLAUDE_PLUGIN_ROOT}/skills/meta-ads-upload/`: `scripts/run_meta_job.py` (runner), `scripts/meta_ads_core.py` (core, depende de `requests`) e `templates/*.template.json` (inputs). Os relatórios vão para `./ads-ops-runs/meta/` (ou `$ADS_OPS_RUNS_DIR/meta/`).

### Segurança do runner

- Sempre começar em dry-run (default). No dry-run as leituras (GET) rodam de verdade, então `audit` e a numeração automática usam dados reais; as escritas não são enviadas e aparecem em `planned_calls` no relatório, com método, caminho e parâmetros. O `planned_calls` é o plano a mostrar ao usuário, com uma lacuna: uploads de mídia não aparecem nele (no dry-run eles devolvem IDs fictícios), então liste os arquivos a subir à parte.
- `--execute` só com o payload revisado e o OK do usuário.
- Nunca gravar token em config, template ou JSON de input.
- O runner só repete GET sozinho. Se um POST falhar por rede ou 5xx, releia (por nome ou `created_time`) antes de reenviar, porque ele pode ter gravado.
- O runner segue para o próximo item quando um falha e marca `partial`. Para o contrato do operator (parar no primeiro mismatch), mande um item por job.

### Contas e credenciais

O runner resolve a conta nesta ordem (o primeiro que tiver o valor ganha):

1. `context` dentro do JSON do job (`ad_account`, `page_id`, `ig_user_id`, `api_version`), só quando o usuário pedir outra conta para aquele job
2. O perfil escolhido com `--profile <nome>` (ou o `default_profile`) no config do ads-ops
3. Variáveis `META_AD_ACCOUNT_<PERFIL>`, `META_PAGE_ID_<PERFIL>`, `META_IG_USER_ID_<PERFIL>`
4. Variáveis genéricas `META_AD_ACCOUNT`, `META_PAGE_ID`, `META_IG_USER_ID`, `META_API_VERSION` (default `v25.0`)

O token vem só de variável de ambiente: `META_ACCESS_TOKEN_<PERFIL>` ou `META_ACCESS_TOKEN`. `<PERFIL>` é o nome do perfil em maiúsculas, com `-` trocado por `_` (perfil `cliente-a` → `META_ACCESS_TOKEN_CLIENTE_A`).

O config é procurado em `$ADS_OPS_CONFIG`, depois `./.claude/ads-ops.local.json` e por fim `~/.claude/ads-ops.local.json`. Ele é opcional; para cadastrar contas, sugira `/ads-ops:setup`. Formato da seção Meta:

```json
{
  "meta": {
    "default_profile": "cliente-a",
    "profiles": {
      "cliente-a": { "ad_account": "act_<AD_ACCOUNT_ID>", "page_id": "<PAGE_ID>", "ig_user_id": "<IG_USER_ID>" }
    }
  }
}
```

Se faltar conta, página ou token, o runner para dizendo o que configurar. Pergunte ao usuário em vez de inventar IDs.

### Comandos

```bash
RUN="python3 ${CLAUDE_PLUGIN_ROOT}/skills/meta-ads-upload/scripts/run_meta_job.py"
```

| Tarefa | Comando |
|---|---|
| Auditar campanha | `$RUN --mode audit --input audit.json` |
| Criar adsets | `$RUN --mode create --input adsets.json` |
| Criar ads de vídeo | `$RUN --mode create --input video_ads.json` |
| Criar ads de imagem | `$RUN --mode create --input image_ads.json` |
| Criar ads de posts existentes do Instagram | `$RUN --mode create --input existing_post_ads.json` |
| Atualizar ads com novo creative | `$RUN --mode update --input update_ads.json` |
| Duplicar campanhas, adsets ou ads | `$RUN --mode duplicate --input duplicate_adsets.json` |

Fluxo: `audit` → copiar o template certo para o diretório de trabalho e preencher os `<PLACEHOLDERS>` → dry-run → revisar e mostrar `planned_calls` → `--execute` com o OK. Acrescente `--profile <nome>` para escolher a conta e `--output <arquivo>` para mudar onde o relatório é gravado.

O runner recusa inputs com `<PLACEHOLDERS>` não preenchidos e inputs com `access_token`. O relatório traz `status: "ok"` (saída 0), `"partial"` quando algum item falhou (saída 2; veja `result.error` e o `error` de cada item) ou `"error"` (saída 1). Nunca diga que deu certo sem conferir isso e sem o readback.

### Modos

- `audit`: validar naming e estado da campanha
- `create` + `job_type=adsets`: criar ad sets com numeração (`auto_number` + `name_template`, ex. `{num:02d} - Publico`). A numeração lê o número no início do nome dos existentes (`01 - ...`); se a conta usa outro padrão, confirme antes.
- `create` + `job_type=video_ads` | `image_ads` | `existing_post_ads`: subir mídia, creative e ad
- `update`: criar creative com asset customization e apontar o ad existente para ele
- `duplicate` + `job_type=campaigns` | `adsets` | `ads`: clonar pelo `/copies`

Em `duplicate`, o input segue o padrão `items[]` com um `id` por objeto; campos no root valem para todos e campos no item sobrescrevem:

| Campo | Descrição |
|-------|-----------|
| `deep_copy` | Clonar filhos junto (default: `true`) |
| `rename_strategy` | `DEEP_RENAME`, `ONLY_TOP_LEVEL_RENAME`, `NO_RENAME` |
| `rename_prefix` / `rename_suffix` | Prefixo ou sufixo no nome da cópia (default do Meta: "- Copy") |
| `status_option` | `PAUSED` (recomendado), `ACTIVE`, `INHERITED_FROM_SOURCE` |
| `start_time` / `end_time` | ISO datetime (`end_time: "0"` = sem fim) |
| `campaign_id` | Campanha destino (só para adsets) |
| `adset_id` | Adset destino (só para ads) |

### Limites do runner

- Precisa de Python 3 com `requests` e de rede para `graph.facebook.com`. Sem isso, use o conector oficial.
- Dynamic Creative complexo pede script dedicado.
