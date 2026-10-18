---
name: Meta Ads Objective, Optimization Goal & Destination Type Mapping
description: Matriz oficial de combinações válidas da Marketing API (v25/v26) entre Campaign Objective, AdSet Optimization Goal, Destination Type e Promoted Object.
---

# Matriz de Objetivos, Otimizações e Tipos de Destino (Meta Marketing API)

No Meta Ads (ODAX), cada nível da hierarquia depende estritamente do nível superior:
Campanha (`objective`) → Ad set (`optimization_goal` + `destination_type` + `promoted_object`) → Creative (CTA)

Configurar uma combinação incompatível resulta em erros de validação imediata da Graph API.

---

## 1. Matriz de Combinações Canônicas (ODAX)

| Objetivo de Negócio | Campaign `objective` | AdSet `optimization_goal` | AdSet `destination_type` | `promoted_object` Requerido | Formato / CTA no Criativo |
|---|---|---|---|---|---|
| **Vendas / Compras no Site** | `OUTCOME_SALES` | `OFFSITE_CONVERSIONS` | `WEBSITE` | `{"pixel_id": "...", "custom_event_type": "PURCHASE"}` | `SHOP_NOW`, `LEARN_MORE` + `website_url` |
| **Leads em Formulário Nativo** | `OUTCOME_LEADS` | `LEAD_GENERATION` *(ou `QUALITY_LEAD`)* | `ON_AD` | `{"page_id": "..."}` | `SIGN_UP` com `lead_gen_form_id` + link `https://fb.me/` |
| **Leads em Landing Page** | `OUTCOME_LEADS` | `OFFSITE_CONVERSIONS` | `WEBSITE` | `{"pixel_id": "...", "custom_event_type": "LEAD"}` | `SIGN_UP`, `LEARN_MORE` + `website_url` |
| **Tráfego para Site / LP** | `OUTCOME_TRAFFIC` | `LANDING_PAGE_VIEWS` *(requer Pixel)* ou `LINK_CLICKS` | `WEBSITE` | *Opcional* (Pixel para LPV) | `LEARN_MORE` + `website_url` |
| **Visitas ao Perfil do Instagram** | `OUTCOME_TRAFFIC` | `PROFILE_VISIT` *(nunca VISIT_INSTAGRAM_PROFILE)* | `INSTAGRAM_PROFILE` | *Nenhum* | CTA `VIEW_INSTAGRAM_PROFILE` (somente URL HTTPS normal) |
| **Mensagens no WhatsApp (CTWA)** | `OUTCOME_ENGAGEMENT` *(ou OUTCOME_LEADS)* | `CONVERSATIONS` | `WHATSAPP` | `{"page_id": "..."}` | `WHATSAPP_MESSAGE` *(ou `LEARN_MORE` apontando app_destination)* |
| **Mensagens no Instagram Direct** | `OUTCOME_ENGAGEMENT` | `CONVERSATIONS` | `INSTAGRAM_DIRECT` | `{"page_id": "...", "instagram_profile_id": "..."}` | `SEND_MESSAGE` para Direct |
| **Mensagens no Messenger** | `OUTCOME_ENGAGEMENT` | `CONVERSATIONS` | `MESSENGER` | `{"page_id": "..."}` | `SEND_MESSAGE` |
| **Visualizações de Vídeo** | `OUTCOME_ENGAGEMENT` | `THRUPLAY` | `ON_VIDEO` *(ou `UNDEFINED`)* | *Nenhum* | Vídeo com CTA de engajamento/saiba mais |
| **Reconhecimento e Alcance** | `OUTCOME_AWARENESS` | `REACH` ou `IMPRESSIONS` | `UNDEFINED` | *Nenhum* | Livre / `LEARN_MORE` |

---

## 2. Detalhamento Técnico das Principais Rotas

### A. Lead Ads (Formulários Nativos Instantâneos)
1. **Campanha:** `objective: "OUTCOME_LEADS"`.
2. **AdSet:**
   - `optimization_goal: "LEAD_GENERATION"` (ou `QUALITY_LEAD` para filtrar leads mais qualificados).
   - `destination_type: "ON_AD"`.
   - `promoted_object: {"page_id": "<PAGE_ID>"}`.
   - *Nota:* O formulário **não** vai no AdSet.
3. **AdCreative:**
   - O formulário entra em `call_to_actions`:
     ```json
     {
       "call_to_action_types": ["SIGN_UP"],
       "call_to_actions": [
         {
           "type": "SIGN_UP",
           "value": {
             "lead_gen_form_id": "<LEAD_GEN_FORM_ID>"
           }
         }
       ],
       "link_urls": [
         {
           "website_url": "https://fb.me/"
         }
       ]
     }
     ```
   - O campo `link_urls` com o placeholder `https://fb.me/` é mandatório para validação das regras de posicionamento (`asset_customization_rules`).
4. **Permissão da API:**
   - Listar ou criar formulários via `GET/POST /{page_id}/leadgen_forms` exige **Page Access Token**. Usar token de usuário resulta no erro `190` (*"Must be called with a Page Access Token"*).

---

### B. Conversões no Site (Vendas e Leads em Landing Page)
1. **Campanha:** `objective: "OUTCOME_SALES"` ou `"OUTCOME_LEADS"`.
2. **AdSet:**
   - `optimization_goal: "OFFSITE_CONVERSIONS"`.
   - `destination_type: "WEBSITE"`.
   - `promoted_object`: Objeto estritamente obrigatório contendo:
     ```json
     {
       "pixel_id": "<PIXEL_ID>",
       "custom_event_type": "PURCHASE" // ou "LEAD", "COMPLETE_REGISTRATION", "START_TRIAL", etc.
     }
     ```
   - Omissão de `promoted_object` ou de `custom_event_type` rejeita a criação do conjunto imediatamente.

---

### C. Tráfego para o Perfil do Instagram
1. **Campanha:** `objective: "OUTCOME_TRAFFIC"`.
2. **AdSet:**
   - `optimization_goal: "PROFILE_VISIT"`.
   - `destination_type: "INSTAGRAM_PROFILE"`.
   - ⚠️ **Gotcha Histórico:** O antigo optimization goal `VISIT_INSTAGRAM_PROFILE` foi descontinuado pela Meta. AdSets configurados com o valor legado nascem `ACTIVE`, mas registram R$ 0 de entrega e nenhuma impressão. A rota oficial e ativa exige `OUTCOME_TRAFFIC` + `PROFILE_VISIT` + `INSTAGRAM_PROFILE`.
3. **AdCreative:**
   - O CTA do criativo deve usar `call_to_action: {"type": "VIEW_INSTAGRAM_PROFILE", "value": {"link": "https://instagram.com/<perfil>"}}`.
   - O valor do link aceita **apenas URL HTTPS padrão**. Enviar deep link (`app_link`) quebra o anúncio com o erro de subcode `1346001` (`WITH_ISSUES`).
