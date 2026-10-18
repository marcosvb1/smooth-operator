---
name: Placement Targeting — Marketing API (v26.0)
description: Catálogo exaustivo de enums, regras de dependência, filtros e exclusões de posicionamento do Meta Ads (Facebook, Instagram, Threads, Messenger, Audience Network, WhatsApp).
---

# Placement Targeting — Marketing API

Documentação consolidada baseada na especificação oficial de [Placement Targeting da Meta](https://developers.facebook.com/documentation/ads-commerce/marketing-api/audiences/reference/placement-targeting) (atualizada para API v26.0).

---

## 1. Lógica Global de Parâmetros

* **Entre parâmetros diferentes:** `AND` (ex.: `publisher_platforms: ['facebook']` & `device_platforms: ['mobile']` entrega estritamente no Facebook Mobile).
* **Dentro do mesmo array:** `OR` (ex.: `['facebook', 'instagram']` entrega em ambos os canais).
* **Omissão:** Omitir os parâmetros de posicionamento no `targeting` faz a API considerar todos os posicionamentos elegíveis padrão daquele objetivo (Advantage+ Placements).

---

## 2. Dispositivos e Canais

```json
{
  "device_platforms": ["mobile", "desktop"],
  "publisher_platforms": [
    "facebook",
    "instagram",
    "threads",
    "messenger",
    "audience_network",
    "whatsapp"
  ]
}
```

---

## 3. Catálogo de Posicionamentos Específicos

### Facebook (`facebook_positions`)
- `feed`: Feed principal desktop e mobile (amigos/grupos). Base para a maioria dos demais posicionamentos.
- `story`: Stories do Facebook. *Exige `feed` no FB ou `story` no IG + `device_platforms: ['mobile']`.*
- `facebook_reels`: Vídeos verticais no Facebook Reels.
- `facebook_reels_overlay`: Anúncios em sobreposição no Facebook Reels.
- `instream_video`: Vídeos in-stream antes/durante conteúdos em vídeo.
- `video_feeds`: Feeds dedicados de vídeo (Watch).
- `marketplace`: Aba Marketplace. *Exige `feed` no payload.*
- `search`: Resultados de busca no Facebook. *Exige `feed` no payload.*
- `profile_feed`: Feed ao navegar pelo perfil de um usuário. *Exige `feed` no payload.*
- `right_hand_column`: Coluna da direita no Desktop. *Disponível apenas para formatos estáticos e carrossel em desktop.*
- `notification`: Anúncios na central de notificações. *Exige `feed` no payload.*

### Instagram (`instagram_positions`)
- `stream`: Feed principal do Instagram (Mobile e Web).
- `story`: Instagram Stories (Mobile e Web).
- `reels`: Instagram Reels principal.
- `profile_feed`: Feed ao visitar o perfil de uma conta.
- `profile_reels`: Reels visualizados ao navegar no perfil de uma conta.
- `ig_search`: Resultados de busca do Instagram.
- `explore_home`: Grade inicial da aba Explorar (Explore Grid).
- ⚠️ **`explore` (Feed do Explorar):** **Descontinuado na v26.0+**. O POST aceita `explore`, mas o valor é ignorado sem erro e some de `effective_instagram_positions`. Use `explore_home`.

### Threads (`threads_positions`)
- `threads_stream`: Feed do Threads.
  - *Regra de dependência:* Exige `publisher_platforms: ["instagram", "threads"]` e `instagram_positions: ["stream"]`.

### Audience Network (`audience_network_positions`)
- `classic`: Anúncios nativos, banners e intersticiais em aplicativos e sites parceiros.
- `rewarded_video`: Vídeos com recompensa em jogos e apps.
  - *Regra de dependência:* Não pode ser veiculado isolado (`audience_network` exige `facebook` ou `instagram` junto).

### Messenger (`messenger_positions`)
- `sponsored_messages`: Mensagens patrocinadas para usuários que já interagiram com a página.
- ⚠️ **`story` (Messenger Stories):** Silenciosamente ignorado a partir da v26.0+.

### WhatsApp (`whatsapp_positions`)
- `status`: Anúncios exibidos na aba de Status/Atualizações do WhatsApp. *Exige `story` em `instagram_positions`.*
- `marketing_messages`: Disparos patrocinados para base de assinantes da conta.

---

## 4. Filtros de Brand Safety e Exclusões

### Níveis de Filtro de Conteúdo (`brand_safety_content_filter_levels`)
Controla o tipo de conteúdo adjacente aos anúncios (In-content, Audience Network e Feed):
* Facebook In-Content / Reels: `FACEBOOK_STRICT`, `FACEBOOK_STANDARD`, `FACEBOOK_RELAXED`
* Audience Network: `AN_STRICT`, `AN_STANDARD`, `AN_RELAXED`
* Feeds (FB/IG): `FEED_STRICT`, `FEED_STANDARD`, `FEED_RELAXED`

### Categorias de Editores Excluídas (`excluded_publisher_categories`)
* `debated_social_issues`
* `mature_audiences`
* `tragedy_and_conflict`
* `dating`
* `gambling`

---

## 5. Exclusão com Tolerância de Gasto (`placement_soft_opt_out`)

Permite excluir canais manuais concedendo até **5% de verba residual** se o Meta identificar conversões atipicamente baratas naquele posicionamento:

```json
"placement_soft_opt_out": {
  "facebook_positions": ["marketplace", "profile_feed"],
  "audience_network_positions": ["classic", "rewarded_video"]
}
```

---

## 6. Consulta de Posicionamentos Efetivos (`effective_*`)

Para verificar quais posicionamentos foram de fato ativados pelo algoritmo após as validações de objetivo e criativo:
```
GET /{adset_id}?fields=targeting{effective_publisher_platforms,effective_facebook_positions,effective_instagram_positions,effective_device_platforms}
```
