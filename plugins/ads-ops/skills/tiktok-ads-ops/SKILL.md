---
name: tiktok-ads-ops
description: This skill should be used when the user wants to create, edit, pause, audit or debug TikTok Ads campaigns, ad groups, ads, creatives or Spark Ads through the TikTok Marketing API v1.3 (directly or via an MCP connector such as Make), for any configured advertiser — e.g. "create a TikTok campaign", "upload this video to TikTok Ads", "pause the TikTok ad group", "set up Spark Ads", "TikTok API error", "subir anuncio no TikTok", "criar campanha no TikTok", "pausar campanha do TikTok", "erro na API do TikTok". Not for pure performance reporting or dashboards.
---

# TikTok Ads Ops

Playbook operacional de execucao, conformidade e subida de anuncios na TikTok Marketing API (v1.3), via chamadas diretas ou via um conector MCP (por exemplo, um cenario do Make que expoe uma tool de escrita e outra de relatorios para TikTok Ads). Funciona para qualquer conta: advertiser, fuso, moeda, marca e padrao de nomes vem do perfil configurado.

## Antes de qualquer chamada: qual conta

Leia o perfil do TikTok no arquivo de config do ads-ops, procurado em `$ADS_OPS_CONFIG`, depois `./.claude/ads-ops.local.json` e por fim `~/.claude/ads-ops.local.json`:

```json
{
  "tiktok": {
    "default_profile": "cliente-a",
    "profiles": {
      "cliente-a": {
        "advertiser_id": "<ADVERTISER_ID>",
        "timezone": "America/Sao_Paulo",
        "currency": "BRL",
        "display_name": "<Nome da marca no anuncio>",
        "landing_page": "https://example.com/oferta",
        "pixel_id": "<PIXEL_ID>",
        "mcp_write_tool": "<nome da tool MCP de escrita, se houver>",
        "mcp_report_tool": "<nome da tool MCP de relatorios, se houver>",
        "naming": {
          "campaign": "EMPRESA_AAAA.S_TIKTOK_OBJETIVO_NOME",
          "adgroup": "SEGMENTACAO | LOCALIZACAO | IDADE",
          "ad": "adXX - formato - gancho"
        }
      }
    }
  }
}
```

- Use `timezone`, `currency`, `display_name`, `landing_page` e `pixel_id` do perfil como valores padrao dos payloads, salvo pedido do usuario.
- Se houver mais de um perfil e o usuario nao disser qual, pergunte. Se nao houver config, peca o advertiser ID; o `/ads-ops:setup` e opcional e so vale a pena para quem usa sempre as mesmas contas ou chama a API direto.
- Chamadas diretas usam o header `Access-Token` com o valor de `TIKTOK_ACCESS_TOKEN_<PERFIL>` ou `TIKTOK_ACCESS_TOKEN` (`<PERFIL>` em maiusculas, todo caractere que nao e letra nem numero vira `_`). Nunca grave o token em arquivo.
- Se o perfil indicar `mcp_write_tool` / `mcp_report_tool`, use essas tools (secao 3). Se nao, procure uma tool de TikTok Ads disponivel na sessao antes de cair para chamadas HTTP diretas.

## Quando Usar

- Criar, pausar, editar ou auditar campanhas, grupos de anuncios (`adgroup`) e anuncios (`ad`) no TikTok Ads.
- Subir criativos (videos 9:16, Spark Ads com `auth_code` / `tiktok_item_id`, display names).
- Configurar orcamentos, agendamentos, lances e segmentacoes (exclusao de Pangle, faixas etarias, geolocalizacao).
- Mapear e contornar erros comuns da API do TikTok (limites minimos de orcamento, fusos horarios, rejeicao de formatos, etc.).

---

## 1. Regras Inviolaveis de Conformidade e Pre-Publicacao

1. **NUNCA DELETAR CAMPANHAS OU ANUNCIOS:**
   - A remocao destroi o historico de metricas e tracking de UTMs.
   - Sempre pausar com `POST /v1.3/{campaign|adgroup|ad}/status/update/` e `operation_status: "DISABLE"` (os valores validos sao `ENABLE`, `DISABLE` e `DELETE`; nunca use `DELETE`).

2. **DESMARCAR PANGLE / GLOBAL APP BUNDLE (padrao, salvo pedido do usuario):**
   - Por padrao, a API ou interface pode incluir a rede Pangle. Defina explicitamente `placement_type: "PLACEMENT_TYPE_NORMAL"` e `placements: ["PLACEMENT_TIKTOK"]`. Pangle entrega cliques de baixa retencao e jogos casuais.

3. **ORCAMENTOS MINIMOS DA PLATAFORMA (TIKTOK API):**
   - Em contas USD: campanha (CBO diario) minimo de US$ 50 e grupo de anuncios (ABO diario) minimo de US$ 20.
   - Em outras moedas o piso e o equivalente definido pelo TikTok (em contas BRL, observado R$ 50/dia para os dois niveis). Use a `currency` do perfil e, na duvida, confira o minimo que a propria API devolve no erro.
   - Enviar valores inferiores causa rejeicao imediata na API.

4. **FUSO HORARIO E DATAS (`schedule_time`):**
   - O TikTok opera no fuso horario configurado na conta de anuncios (ex: `America/Sao_Paulo` ou UTC). As strings de data devem seguir o formato `YYYY-MM-DD HH:MM:SS` respeitando o fuso do advertiser.

5. **CRIACAO INICIAL EM PAUSA E CONFIRMACAO ANTES DE ESCREVER:**
   - Nao existe dry-run na API do TikTok. Antes de qualquer chamada de escrita (`/create/`, `/update/`, `/status/update/` ou a tool MCP de escrita), mostre ao usuario o `body` final e espere o ok dele. O mesmo vale para trocar qualquer coisa para `ENABLE`.
   - Suba novas campanhas e adgroups com `operation_status: "DISABLE"`. Faca a conferencia de URLs, ofertas e criativos antes de ativar para veiculacao.

6. **PADRAO DE NOMENCLATURA E UTMS:**
   - Use o `naming` do perfil. Sem ele, o padrao sugerido e:
   - **Campanha:** `EMPRESA_Ano.Semestre_TIKTOK_OBJETIVO_NOME` (ex: `ACME_2027.1_TIKTOK_TRAFEGO_GERAL`)
   - **Ad Group:** `SEGMENTACAO | LOCALIZACAO | IDADE` (ex: `GERAL | BR | 18-24`)
   - **Anuncio:** `adXX - formato - gancho` (ex: `ad01 - 9:16 - video_conceito_15s`)
   - **Landing Page & UTMs:** Sempre conferir a URL de destino com parametros dinamicos ou explicitos (`utm_source=tiktok&utm_medium=paid&utm_campaign={{campaign.name}}&utm_content={{ad.name}}`).

---

## 2. Estrutura de Chamadas e Payloads (TikTok Marketing API v1.3)

Base path relativo: `https://business-api.tiktok.com/open_api`

### A. Criar Campanha (`POST /v1.3/campaign/create/`)
```json
{
  "advertiser_id": "<ADVERTISER_ID>",
  "campaign_name": "ACME_2027.1_TIKTOK_TRAFEGO_GERAL",
  "objective_type": "TRAFFIC",
  "budget_mode": "BUDGET_MODE_INFINITE",
  "operation_status": "DISABLE"
}
```
- **Objetivos comuns:** `TRAFFIC`, `WEB_CONVERSIONS`, `LEAD_GENERATION`, `REACH`, `VIDEO_VIEWS`.
- **Budget Mode:** `BUDGET_MODE_INFINITE` (para orcamento no Ad Group / ABO) ou `BUDGET_MODE_DAY` (CBO).

### B. Criar Grupo de Anuncios (`POST /v1.3/adgroup/create/`)
```json
{
  "advertiser_id": "<ADVERTISER_ID>",
  "campaign_id": "<CAMPAIGN_ID>",
  "adgroup_name": "GERAL | BR | 18-24",
  "placement_type": "PLACEMENT_TYPE_NORMAL",
  "placements": ["PLACEMENT_TIKTOK"],
  "location_ids": ["3469034"],
  "age_groups": ["AGE_18_24"],
  "budget_mode": "BUDGET_MODE_DAY",
  "budget": 100.0,
  "schedule_type": "SCHEDULE_START_END",
  "schedule_start_time": "<AAAA-MM-DD HH:MM:SS no fuso da conta, no futuro>",
  "schedule_end_time": "<AAAA-MM-DD HH:MM:SS>",
  "optimization_goal": "CLICK",
  "bid_type": "BID_TYPE_NO_BID",
  "billing_event": "CPC",
  "operation_status": "DISABLE"
}
```
- **Nota:** `location_ids` usa IDs do GeoNames (`3469034` = Brasil, `6252001` = Estados Unidos). Confira com `GET /v1.3/tool/region/` se tiver duvida.
- **Nota:** Para `WEB_CONVERSIONS`, incluir `pixel_id` e `external_action` (ex: `COMPLETE_REGISTRATION`).

### C. Upload de Video e Criativos (`POST /v1.3/file/video/ad/upload/`)
- Formato obrigatorio para TikTok: Proporcao 9:16 (1080x1920 ou 720x1280), formato .mp4 / .mov, codec H.264.
- A chamada retorna `video_id` que deve ser usado na criacao do anuncio.

### D. Criar Anuncio (`POST /v1.3/ad/create/`)
```json
{
  "advertiser_id": "<ADVERTISER_ID>",
  "adgroup_id": "<ADGROUP_ID>",
  "creatives": [
    {
      "ad_name": "ad01 - 9:16 - video_conceito_15s",
      "ad_format": "SINGLE_VIDEO",
      "video_id": "<VIDEO_ID>",
      "ad_text": "<Texto do anuncio>",
      "landing_page_url": "https://example.com/oferta?utm_source=tiktok&utm_medium=paid&utm_campaign={{campaign.name}}&utm_content={{ad.name}}",
      "call_to_action": "LEARN_MORE",
      "display_name": "<display_name do perfil>",
      "operation_status": "DISABLE"
    }
  ]
}
```

### E. Spark Ads (Anuncios com Post Organico ou Codigo de Autorizacao)
- Para veicular posts de contas de criadores ou da marca:
  - Spark Ads usam `identity_type` `AUTH_CODE` (post autorizado por codigo), `TT_USER` (conta TikTok vinculada) ou `BC_AUTH_TT` (conta autorizada via Business Center), com `identity_id` e o `tiktok_item_id` do post.
  - `CUSTOMIZED_USERS` e a identidade de anuncio comum (nao Spark), com `display_name` e imagem de perfil.

---

## 3. Execucao via Conector MCP (ex.: Make)

Os nomes das tools variam por conta; use os do perfil (`mcp_write_tool`, `mcp_report_tool`). O formato abaixo e o de um cenario Make que repassa chamadas para a API do TikTok.

- **Tool de escrita:**
  - Parametros:
    - `operation`: Descricao textual clara da operacao (ex: "Criar campanha de trafego").
    - `url`: Endpoint relativo na API TikTok (ex: `/v1.3/campaign/create/`).
    - `method`: Metodo HTTP (`GET` para leitura, `POST` para escrita; a API do TikTok so usa esses dois).
    - `body`: String contendo o JSON serializado com os campos exatos da API TikTok.
  - Sempre validar o JSON do `body` antes do envio.
- **Tool de relatorios:**
  - Consultas de desempenho e delivery de D-30 a D-1, agregacao `AUCTION_CAMPAIGN` ou `AUCTION_ADGROUP`.

---

## 4. Resolucao de Erros Comuns da API (Gotchas)

- **Erro de Budget Minimo (`Budget must be greater than...`):**
  - O TikTok valida rigorosamente os pisos diarios de campanha e grupo. Nunca passe valores abaixo do minimo da moeda da conta (regra 3).
- **Incompatibilidade de Idade com Menores de 18:**
  - O TikTok restringe segmentacao direcionada a menores de 18 anos na maioria dos objetivos. O publico mais jovem disponivel e `AGE_18_24`.
- **Formato e Proporcao de Video Rejeitado:**
  - Videos 16:9 ou 1:1 podem ser rejeitados ou ter entrega severamente penalizada quando o posicionamento for exclusivamente TikTok. Sempre exija 9:16.
- **Erros de Timezone no Agendamento:**
  - Se a data de inicio enviada estiver no passado em relacao ao horario da conta, a API recusa a criacao do Ad Group. Envie o horario atual da conta ou deixe o inicio imediato.
- **Status Ativo com Saldo/Faturamento Pendente:**
  - Uma campanha `ENABLE` nao entrega se houver pendencia no cadastro de fornecedor ou forma de pagamento na conta de anuncios. Verifique sempre o D+1 de impressoes.
