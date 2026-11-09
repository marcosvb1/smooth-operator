#!/usr/bin/env python3
"""
salesbot_model.py — shared parse/serialize model for Kommo Salesbot exports.

The export wrapper is:
  {"type_functionality": N, "model": {"text": "<JSON STRING>", "name": "...",
                                      "positions": "<JSON STRING>", "type": N}}
where model.text and model.positions are themselves JSON encoded as STRINGS.

This module gives a clean intermediate representation (IR) = the export with the
two stringified blobs PARSED and the purely-cosmetic layout fields stripped from
positions blocks. Everything else (handlers, params, block ids, goto, block_uuid,
actions) is kept verbatim — those are semantic and drive import correctness.

  parse_to_ir(wrapper)  -> IR (nested dict, nothing stringified)
  ir_to_export(ir)      -> wrapper (re-stringified, cosmetics re-applied via auto-layout)
  semantic_projection(wrapper) -> canonical structure for equality diffing (ignores cosmetics)
  auto_layout(blocks)   -> assign deterministic x/y/z/width/height
  text_steps(text) / iter_handlers(node) -> walk the decoded model.text

Round-trip fidelity (see tests/roundtrip.py): for every known-good bot,
  semantic_projection(bot) == semantic_projection(ir_to_export(parse_to_ir(bot)))
and ir_to_export(parse_to_ir(bot)) passes validate.py. This proves the cosmetic
set is exactly {x,y,z,width,height} and that (de)serialization is lossless.
"""
import json

COSMETIC_KEYS = ("x", "y", "z", "width", "height")

# Each model.text step holds its handlers in these lanes; the other top-level key of
# model.text is the "conversation" boolean.
LANES = ("question", "answer", "finish")

# default visual box sizes per block type (only affects appearance, not correctness)
DEFAULT_SIZE = {
    "start": (150, 38),
    "static": (260, 0),
    "question": (400, 200),
    "finish": (374, 62),
}


def _parse_blob(blob):
    if isinstance(blob, (dict, list)):
        return blob
    return json.loads(blob)


def text_steps(text):
    """The steps of a decoded model.text, keyed by step id (without "conversation")."""
    return {k: v for k, v in text.items() if k != "conversation"}


def iter_handlers(node):
    """Yield every {handler, params} dict found anywhere under node (recursively)."""
    if isinstance(node, dict):
        if isinstance(node.get("handler"), str):
            yield node
        for v in node.values():
            yield from iter_handlers(v)
    elif isinstance(node, list):
        for v in node:
            yield from iter_handlers(v)


def parse_to_ir(wrapper):
    model = wrapper["model"]
    text = _parse_blob(model["text"])
    positions = _parse_blob(model["positions"])
    clean_positions = []
    for blk in positions:
        if isinstance(blk, dict):
            clean_positions.append({k: v for k, v in blk.items() if k not in COSMETIC_KEYS})
        else:
            clean_positions.append(blk)
    return {
        "type_functionality": wrapper.get("type_functionality", 0),
        "name": model.get("name"),
        "type": model.get("type"),
        "text": text,
        "positions": clean_positions,
    }


def auto_layout(blocks):
    """Deterministic left-to-right layout. Cosmetic only; mutates copies."""
    out = []
    x_cursor = 0
    for i, blk in enumerate(blocks):
        b = dict(blk)
        btype = b.get("type", "question")
        w, h = DEFAULT_SIZE.get(btype, (400, 200))
        if not any(k in b for k in COSMETIC_KEYS):
            b["x"] = x_cursor
            b["y"] = (i % 2) * 260  # slight zig-zag so boxes don't overlap
            b["z"] = i + 2
            b["width"] = w
            b["height"] = h
        x_cursor += w + 60
        out.append(b)
    return out


def ir_to_export(ir, relayout=True):
    positions = ir["positions"]
    if relayout:
        positions = auto_layout(positions)
    model = {
        "text": json.dumps(ir["text"], ensure_ascii=False),
        "name": ir.get("name"),
        "positions": json.dumps(positions, ensure_ascii=False),
        "type": ir.get("type"),
    }
    return {"type_functionality": ir.get("type_functionality", 0), "model": model}


def _canon(obj):
    """Recursively sort dict keys for stable equality; preserve list order."""
    if isinstance(obj, dict):
        return {k: _canon(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_canon(v) for v in obj]
    return obj


def semantic_projection(wrapper):
    """Structure used for equality diffing — cosmetics stripped, keys canonicalized."""
    return _canon(parse_to_ir(wrapper))


def load_export(path):
    with open(path) as fh:
        return json.load(fh)


def save_export(wrapper, path):
    with open(path, "w") as fh:
        json.dump(wrapper, fh, ensure_ascii=False, indent=2)
