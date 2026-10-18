# Meta Ads API - Endpoints Reference

## URLs Base

```
https://graph.facebook.com/v25.0/
```

---

## Ad Account

### Obter informações da conta
```
GET /act_{ad_account_id}?fields=name,account_status,currency,amount_spent
```

### Listar campanhas
```
GET /act_{ad_account_id}/campaigns?fields=name,status,objective,daily_budget
```

### Listar adsets
```
GET /act_{ad_account_id}/adsets?fields=name,status,daily_budget,targeting
```

### Listar ads
```
GET /act_{ad_account_id}/ads?fields=name,status,creative{video_id,image_hash}
```

---

## Campaign

### Criar campanha
```
POST /act_{ad_account_id}/campaigns

{
  "name": "NOME_CAMPANHA",
  "objective": "OUTCOME_SALES",
  "status": "PAUSED",
  "special_ad_categories": [],
  "access_token": TOKEN
}
```

### Obter adsets de uma campanha
```
GET /{campaign_id}/adsets?fields=name,status
```

---

## Adset

### Criar adset
```
POST /act_{ad_account_id}/adsets

{
  "name": "01 - Público | Objetivo",
  "campaign_id": CAMPAIGN_ID,
  "targeting": {
    "geo_locations": {"countries": ["BR"]},
    "age_min": 18,
    "age_max": 65,
    "genders": [1, 2],
    "facebook_positions": ["feed", "story"],
    "publisher_platforms": ["facebook", "instagram"]
  },
  "billing_event": "IMPRESSIONS",
  "optimization_goal": "OFFSITE_CONVERSIONS",
  "daily_budget": 3000,
  "access_token": TOKEN
}
```

### Atualizar adset
```
POST /{adset_id}

{
  "name": "Novo nome",
  "daily_budget": 5000,
  "access_token": TOKEN
}
```

---

## Video Upload

### Upload de vídeo
```
POST /act_{ad_account_id}/advideos

{
  "source": "https://url-do-video.mp4",
  "title": "Nome do vídeo",
  "access_token": TOKEN
}
```

**Resposta:**
```json
{
  "id": "1234567890"
}
```

### Obter thumbnail do vídeo
```
GET /{video_id}?fields=picture
```

---

## Image Upload

### Upload de imagem
```
POST /act_{ad_account_id}/adimages

FormData:
- filename: (name, file, "image/png")
- access_token: TOKEN
```

**Resposta:**
```json
{
  "images": {
    "nome.png": {
      "hash": "abc123...",
      "url": "https://..."
    }
  }
}
```

---

## Creative

### Criar creative (vídeo)
```
POST /act_{ad_account_id}/adcreatives

{
  "name": "NOME_CRIATIVO",
  "object_story_spec": {
    "page_id": PAGE_ID,
    "video_data": {
      "video_id": VIDEO_ID,
      "message": "Copy do anúncio",
      "image_url": "https://thumbnail.jpg",
      "call_to_action": {
        "type": "LEARN_MORE",
        "value": {"link": "https://link.com"}
      }
    }
  },
  "url_tags": "utm_source={{site_source_name}}&utm_medium=ppc",
  "access_token": TOKEN
}
```

### Criar creative (imagem - link_data)
```
POST /act_{ad_account_id}/adcreatives

{
  "name": "NOME_CRIATIVO",
  "object_story_spec": {
    "page_id": PAGE_ID,
    "link_data": {
      "image_hash": IMAGE_HASH,
      "link": "https://link.com",
      "message": "Copy do anúncio",
      "call_to_action": {"type": "LEARN_MORE"}
    }
  },
  "access_token": TOKEN
}
```

### Criar creative com IG Stories
```
POST /act_{ad_account_id}/adcreatives

{
  "name": "NOME_CRIATIVO",
  "object_story_spec": {
    "instagram_user_id": IG_USER_ID,
    "link_data": {
      "image_hash": IMAGE_HASH,
      "link": "https://link.com",
      "message": "Copy do anúncio",
      "call_to_action": {"type": "LEARN_MORE"}
    }
  },
  "access_token": TOKEN
}
```

---

## Ad

### Criar ad
```
POST /act_{ad_account_id}/ads

{
  "name": "NOME_AD",
  "adset_id": ADSET_ID,
  "creative": {"creative_id": CREATIVE_ID},
  "status": "PAUSED",
  "access_token": TOKEN
}
```

### Atualizar ad
```
POST /{ad_id}

{
  "name": "Novo nome",
  "status": "ACTIVE",
  "access_token": TOKEN
}
```

---

## Copy / Duplicate

### Duplicar campanha
```
POST /{campaign_id}/copies

{
  "deep_copy": true,
  "rename_strategy": "DEEP_RENAME",
  "rename_suffix": " - Copy",
  "status_option": "PAUSED",
  "start_time": "2025-01-01T00:00:00-0300",
  "end_time": "0",
  "access_token": TOKEN
}
```

**Parâmetros:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `deep_copy` | boolean | Copia adsets e ads filhos (max 3 sync, 51 async) |
| `rename_strategy` | enum | `DEEP_RENAME`, `ONLY_TOP_LEVEL_RENAME`, `NO_RENAME` |
| `rename_prefix` | string | Prefixo do nome |
| `rename_suffix` | string | Sufixo do nome (default: "- Copy") |
| `status_option` | enum | `ACTIVE`, `PAUSED`, `INHERITED_FROM_SOURCE` |
| `start_time` | datetime | Hora de início dos adsets copiados |
| `end_time` | datetime | Hora de fim (`0` = sem fim) |
| `parameter_overrides` | object | Overrides de specs da campanha |

**Resposta:**
```json
{
  "copied_campaign_id": "123456",
  "ad_object_ids": [
    {
      "ad_object_type": "adset",
      "source_id": "111",
      "copied_id": "222"
    },
    {
      "ad_object_type": "ad",
      "source_id": "333",
      "copied_id": "444"
    }
  ]
}
```

### Duplicar adset
```
POST /{adset_id}/copies

{
  "campaign_id": CAMPAIGN_ID_DESTINO,
  "deep_copy": true,
  "rename_strategy": "DEEP_RENAME",
  "rename_suffix": " - Copy",
  "status_option": "PAUSED",
  "start_time": "2025-01-01T00:00:00-0300",
  "end_time": "0",
  "access_token": TOKEN
}
```

**Parâmetros:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `campaign_id` | numeric string | Campanha destino (opcional, default = mesma) |
| `deep_copy` | boolean | Copia ads filhos (max 3 sync, 51 async) |
| `rename_strategy` | enum | `DEEP_RENAME`, `ONLY_TOP_LEVEL_RENAME`, `NO_RENAME` |
| `rename_prefix` | string | Prefixo do nome |
| `rename_suffix` | string | Sufixo do nome (default: "- Copy") |
| `status_option` | enum | `ACTIVE`, `PAUSED`, `INHERITED_FROM_SOURCE` |
| `start_time` | datetime | Hora de início customizada |
| `end_time` | datetime | Hora de fim (`0` = sem fim) |

**Resposta:**
```json
{
  "copied_adset_id": "123456",
  "ad_object_ids": [
    {
      "ad_object_type": "ad",
      "source_id": "111",
      "copied_id": "222"
    }
  ]
}
```

### Duplicar ad
```
POST /{ad_id}/copies

{
  "adset_id": ADSET_ID_DESTINO,
  "rename_strategy": "NO_RENAME",
  "status_option": "PAUSED",
  "access_token": TOKEN
}
```

**Parâmetros:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `adset_id` | numeric string | Adset destino (opcional, default = mesmo) |
| `rename_strategy` | enum | `DEEP_RENAME`, `ONLY_TOP_LEVEL_RENAME`, `NO_RENAME` |
| `rename_prefix` | string | Prefixo do nome |
| `rename_suffix` | string | Sufixo do nome (default: "- Copy") |
| `status_option` | enum | `ACTIVE`, `PAUSED`, `INHERITED_FROM_SOURCE` |
| `creative_parameters` | AdCreative | Override de creative (apenas campos top-level) |

**Resposta:**
```json
{
  "copied_ad_id": "123456"
}
```

---

## Call to Action Types

| Tipo | Uso |
|------|-----|
| `LEARN_MORE` | Saiba mais (padrão mais comum) |
| `SIGN_UP` | Cadastre-se |
| `SHOP_NOW` | Compre agora |
| `BOOK_NOW` | Agende agora |
| `GET_OFFER` | Obter oferta |
| `DOWNLOAD` | Baixar |
| `GET_QUOTE` | Solicitar orçamento |
| `CONTACT_US` | Fale conosco |

---

## Status Values

| Status | Significado |
|--------|-------------|
| `ACTIVE` | Ativo |
| `PAUSED` | Pausado |
| `DELETED` | Deletado |
| `PENDING_REVIEW` | Aguardando revisão |
| `DISAPPROVED` | Rejeitado |

---

## Optimization Goals

| Goal | Uso |
|------|-----|
| `OFFSITE_CONVERSIONS` | Conversões no site (pixel) |
| `LINK_CLICKS` | Cliques no link |
| `IMPRESSIONS` | Impressões (awareness) |
| `REACH` | Alcance |
| `LANDING_PAGE_VIEWS` | Visualizações de página |
| `LEAD_GENERATION` | Geração de leads |

---

## Billing Events

| Event | Uso |
|-------|-----|
| `IMPRESSIONS` | Por impressão (padrão) |
| `LINK_CLICKS` | Por clique |

---

## Rename Strategy (Copy/Duplicate)

| Estratégia | Descrição |
|------------|-----------|
| `DEEP_RENAME` | Renomeia o objeto e todos os filhos |
| `ONLY_TOP_LEVEL_RENAME` | Renomeia apenas o objeto copiado |
| `NO_RENAME` | Mantém o nome original |

---

## Status Option (Copy/Duplicate)

| Opção | Descrição |
|-------|-----------|
| `ACTIVE` | Cópia fica ativa imediatamente |
| `PAUSED` | Cópia fica pausada (recomendado) |
| `INHERITED_FROM_SOURCE` | Herda o status do original |

---

## Erros Comuns

### `instagram_actor_id` inválido
**Solução:** Usar `instagram_user_id` no lugar.

### Asset feed sem tipo de ação
**Solução:** Declarar `call_to_action_types` no `asset_feed_spec` e, na dúvida sobre o shape, ler o `asset_feed_spec` de um creative ativo do mesmo formato. Não edite no Ads Manager para contornar: isso cria creative novo e o `url_tags` some.

### Naming conflict em adset
**Solução:** Sempre consultar adsets existentes via API antes de criar.

---

## Rate Limits

- **Standard:** limites por pontuação (Business Use Case); acompanhe o header `X-Business-Use-Case-Usage` e reduza o ritmo quando passar de ~75%
- **Pode variar** conforme tamanho da conta
- **Recomendado:** Adicionar `time.sleep(0.3)` entre requests consecutivos
