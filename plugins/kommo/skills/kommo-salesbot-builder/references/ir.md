# IR — representação intermediária editável

O IR (Intermediate Representation) é a **superfície editável** do bot: o export com os dois
blobs stringificados **parseados** e o layout cosmético (`x,y,z,width,height`) **removido**.
Implementado em `scripts/salesbot_model.py`.

```
IR = {
  "type_functionality": 0,
  "name": "Nome do bot",
  "type": 2,
  "text": { ... },        // model.text já parseado (objeto keyed por step-id)
  "positions": [ ... ]     // model.positions já parseado, SEM x/y/z/width/height
}
```

## Ciclo

```
export  --parse_to_ir-->  IR  --(editar)-->  IR'  --ir_to_export-->  export'
```
- `parse_to_ir(wrapper)`: desfaz o duplo-stringify e tira os cosméticos.
- `ir_to_export(ir)`: reaplica auto-layout (cosmético determinístico), re-stringifica os dois
  blobs, remonta o wrapper.
- `semantic_projection(wrapper)`: canônico pra diff (ignora cosmético, ordena chaves).

**Fidelidade provada** (`roundtrip.py`), no corpus que o `tests/run_all.sh` usa (sintético por
padrão; `$SALESBOT_CORPUS` aponta para exports reais): para todo bot,
`semantic_projection(orig) == semantic_projection(ir_to_export(parse_to_ir(orig)))` **e** o
regenerado passa no `validate.py`. Logo o IR é lossless fora do layout.

## Por que o IR mantém a topologia verbatim

`positions[].id`, `goto`, `block_uuid` e o espelhamento de `actions` **não** são abstraídos no
IR de fase 1 — são preservados verbatim. Isso porque a geração de fase 1 é **adaptar templates**:
parte-se de um bot known-good (topologia correta), troca-se só os valores-folha (texto, ids,
delays) via slots, e a topologia consistente vem de graça. Nenhuma reconstrução de grafo.

## Camada de slots (templates)

Um template (`templates/*.json`) é um IR onde valores-folha viraram slots:
- string → `"<<nome>>"`; numérico (ids) → sentinela negativo (`-901`, mapeado por `slot.sentinel`).
- `compile.py` substitui slots → `ir_to_export` → `validate.py`. Ver `templates/README.md`.

## Fase 2 (adiado) — HIR / compilador de topologia

Pra gerar bots **novos do zero** (não adaptados de um template), seria preciso um IR de alto
nível (HIR) descrevendo o fluxo lógico (passos + handlers + arestas por nome lógico) e um
**compilador HIR→LIR** que:
- atribui `id`s de bloco e `block_uuid`s,
- reconstrói `goto.block` a partir do grafo de passos,
- espelha `actions` nos blocos de `positions`,
- liga `text`↔`positions`.

Isso é YAGNI na fase 1 (validador + adaptar templates cobre o uso atual sem o risco de
reconstrução). Construir só se a adaptação de templates se mostrar insuficiente.
