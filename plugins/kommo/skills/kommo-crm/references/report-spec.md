# Report spec — Output schema

Formato canônico dos três modos de relatório da skill `kommo-crm`.

## `funnel-snapshot` (sem `--with-leads`)

### JSON

```json
{
  "_meta": {
    "profile": "cliente-a",
    "domain": "https://cliente-a.kommo.com",
    "pipeline_id": 1234567,
    "pipeline_name": "Funil Comercial",
    "total_active": 413,
    "total_terminal": 1963,
    "snapshot_at": "20260628_153022"
  },
  "stages": [
    {
      "stage_id": 7000001,
      "name": "Incoming leads",
      "sort": 10,
      "editable": false,
      "leads_count": 0,
      "pct_of_active": 0
    },
    {
      "stage_id": 7000002,
      "name": "novo lead",
      "sort": 20,
      "editable": true,
      "leads_count": 666,
      "pct_of_active": 61
    }
  ]
}
```

### CSV

```
pipeline_id,pipeline_name,sort,stage_id,stage_name,editable,leads_count,pct_of_active
1234567,"Funil Comercial",10,7000001,"Incoming leads",false,0,0
1234567,"Funil Comercial",20,7000002,"novo lead",true,666,61
...
```

### Markdown summary (exemplo curto)

```md
# Kommo Funnel Snapshot — cliente-a / Funil Comercial

**Snapshot:** 2026-06-28T15:30:22Z  
**Pipeline:** `1234567` — Funil Comercial  
**Domain:** `https://cliente-a.kommo.com`  
**Perfil:** `cliente-a`  

**Volumes:** 413 ativos · 1963 em system stages (Incoming + 142/143) · **2376 total**

## Etapas (ordenadas por sort)

| sort | id | etapa | editável | leads | % ativos |
|---:|---:|---|:--:|---:|---:|
| 10 | 7000001 | Incoming leads | false | 0 | — |
| 20 | 7000002 | novo lead | true | 17 | 4% |
| ...

**Maior volume ativo:** Em agendamento (57)

## Próxima ação sugerida

- Snapshot JSON: `kommo-reports/kommo_cliente-a_1234567_20260628_153022.json`
- CSV analítico: `kommo-reports/kommo_cliente-a_1234567_20260628_153022.csv`
```

---

## `funnel-snapshot --with-leads` (cohort-export)

Gera adicionalmente `<base>_leads.csv` com 1 linha por lead ativo. **Contém PII** (nome do lead + encarregado IDs).

Schema do CSV:

```
pipeline_id,pipeline_name,stage_id,stage_name,lead_id,lead_name,created_by,responsible_user_id,created_at,updated_at,source_id
1234567,"Funil Comercial",7000002,"novo lead",12345678,"[PROD-26.2] Ana Souza",111111,222222,1715351400,1716894900,33333
```

> ⚠️ Não reproduzir no resumo Markdown nem versionar. Confirme que `kommo-reports/` está no `.gitignore` do projeto antes de gerar.

---

## `pipeline-drift`

Output direto no stdout (markdown bullets). Não gera arquivo. Estrutura:

```md
## Kommo drift check — cliente-a / pipeline 1234567

**API:** `Funil Comercial` — 13 estágios  
**Baseline:** `Funil Comercial` — 10 estágios (`kommo-baselines/cliente-a_1234567.md`)

### 📊 Contagem divergente
- API tem **13** estágios, baseline diz **10**

### ➕ Estágios adicionados na API (ausentes do baseline)
- `7000011` → `Pré-contrato` (sort 70)
- `7000012` → `REUNIÃO AGENDADA` (sort 80)
- `7000013` → `Suporte` (sort 90)

### ✏️ Estágios renomeados
- `7000003`: baseline="Em contato" → API="Em agendamento"
- `142`: baseline="Venda ganha" → API="CONTRATO FECHADO"

---

**Ação sugerida:** editar `kommo-baselines/cliente-a_1234567.md` adicionando seção `## Mudanças desde a snapshot`. Drift de rename/add via UI não exige o workflow de pipeline design.
```

### Exit codes do `pipeline_drift.sh`

- `0` → zero drift (sincronizado)
- `1` → drift detectado (não é erro)
- `2` → pré-requisito ausente (credencial, baseline inexistente) ou falha técnica no GET

> Não tratável como erro. Skill caller deve interpretar `1` como "report e siga" e `2` como "falta de pré-requis".

---

## Convenções de nome de arquivo

`kommo_<perfil>_<pipeline_id>_<YYYYMMDD_HHMMSS>.{json,csv,md}`

- `perfil` = nome do perfil no `kommo.local.json`
- `pipeline_id` numérico sem zeros à esquerda
- Timestamp UTC local (horário da máquina)

---

## Onde os arquivos ficam

Default `./kommo-reports/` no diretório atual (ou `$REPORT_DIR`). Retenção sugerida:

- Snapshots de rotina: manter os últimos 3-6 meses.
- Snapshot pós-refactor: preservar como baseline histórico.
- `_leads.csv` (PII): apagar assim que gerar o insight; não guardar a longo prazo.
