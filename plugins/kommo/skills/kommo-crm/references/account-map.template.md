# Mapa da conta — <perfil> (<subdominio>.kommo.com)

Modelo para documentar uma conta específica. Não faz parte do plugin: copie para o projeto do
usuário (ex.: `./kommo-baselines/<perfil>-account-map.md`), preencha a partir da API e trate como
snapshot datado. Antes de concluir sobre o estado atual, confira na API.

Fontes: `GET /api/v4/account`, `GET /api/v4/leads/pipelines`, `GET /api/v4/leads/custom_fields`,
`GET /api/v4/contacts/custom_fields`, `GET /api/v4/users`.

**Conferido em:** <AAAA-MM-DD>
**Account ID:** `<ACCOUNT_ID>` · **Plano:** <Base | Advanced | Pro | Enterprise>

## Marcas / unidades dentro da conta

Uma conta pode abrigar várias marcas ou produtos. Registre como elas se separam (pipeline próprio,
custom field, tag), para nunca confundir marca com conta.

| Marca/produto | Como separa | Observação |
|---|---|---|
| <Marca A> | pipeline `<PIPELINE_ID>` | |
| <Produto X> | CF `<Nome>` (`<FIELD_ID>`) = `<valor>` | |

## Pipelines ativos

| Pipeline | ID | Etapas | Função | Marca |
|---|---|---:|---|---|
| <Nome> | `<PIPELINE_ID>` | <N> | <triagem / venda / pós-venda> | <Marca> |

Arquivados: listar só ID e nome; não paginar por padrão.

## Roteiro por pergunta

| Pergunta típica | Pipeline / filtro |
|---|---|
| "<pergunta do time>" | `<PIPELINE_ID>` + CF `<FIELD_ID>` |

## Custom fields relevantes

| Entidade | Campo | ID | Tipo | Cobertura | Observação |
|---|---|---|---|---|---|
| leads | <Nome> | `<FIELD_ID>` | select | <~%> | enums abaixo |
| contacts | <Nome> | `<FIELD_ID>` | text | <~%> | |

### Enums críticos

- `<Nome do campo>` (`<FIELD_ID>`): `<valor>` → `<ENUM_ID>`, ...

## Canais (source_id)

O nome do canal não vem pela API (veja `sources-forms.md`). De-para levantado por evidência:

| source_id | Canal | Como foi identificado |
|---|---|---|
| `<SOURCE_ID>` | <WhatsApp número X> | <pipes em que os leads caem> |

## Usuários

Resolver `user_id` → nome em `GET /api/v4/users` antes de mapear distribuição ou responsável.

## Peculiaridades

- <ex.: telefone salvo com e sem 9º dígito; CF com preenchimento fraco; variações de caixa>
