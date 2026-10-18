#!/usr/bin/env python3
"""
validate.py — Validate a Kommo Salesbot export for import-without-errors.

Two passes:
  STRUCTURAL (always): the consistency invariants that make a bot importable.
    Proven by: passing all known-good corpus bots AND rejecting malformed ones.
  INVENTORY (opt-in, --inventory): every account-specific id used by the bot is
    present in the resolved inventory for the target account (catches foreign/placeholder
    ids). Do NOT run inventory pass against the foreign corpus bots — only against bots
    generated for the account whose inventory you pass.

Exit code: 0 if no ERROR-severity findings, 1 otherwise. --strict also fails on WARN.

Usage:
  python3 validate.py bot.json
  python3 validate.py bot.json --inventory /tmp/inv.cliente-a.json
  python3 validate.py bot.json --json        # machine-readable findings
"""
import argparse
import json
import re
import sys

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
MAX_BOT_BYTES = 64 * 1024
MAX_BUTTONS = 13
MAX_BUTTON_LEN = 80

# handlers observed in the known-good corpus (union). Unknown handlers -> WARN (not error).
KNOWN_HANDLERS = {
    "send_message", "show", "buttons", "waits", "wait_answer", "conditions", "condition",
    "action", "goto", "distribution", "trigger", "send_internal", "start", "_stop", "_start",
    "stop", "preset", "find", "filter", "meta", "validations", "send_external_message",
    "widget_request", "exits",
}
GOTO_TYPES = {"question", "answer", "finish"}


class Findings:
    def __init__(self):
        self.items = []

    def add(self, severity, code, message, where=""):
        self.items.append({"severity": severity, "code": code, "message": message, "where": where})

    def err(self, code, msg, where=""):
        self.add("ERROR", code, msg, where)

    def warn(self, code, msg, where=""):
        self.add("WARN", code, msg, where)

    @property
    def n_err(self):
        return sum(1 for i in self.items if i["severity"] == "ERROR")

    @property
    def n_warn(self):
        return sum(1 for i in self.items if i["severity"] == "WARN")


# send_message params vocabulary. `type` is the DELIVERY type and is "external" in
# every bot of the corpus and in every export checked on live accounts. The dev doc's `show` handler
# uses params.type as a CONTENT type ("text"/"buttons"/"buttons_url") with params.value
# -- that dialect is only valid pasted into a Custom step (Code), never in a compiled
# send_message. Mixing them imports "clean" and renders an EMPTY block in the builder,
# with no error anywhere (observed 2026-09-02).
SEND_MESSAGE_TYPES = {"external"}


def _check_send_message(f, params, where, sid):
    if not isinstance(params, dict):
        f.err("SEND_PARAMS", f"send_message params must be an object (step {sid})", where)
        return
    t = params.get("type")
    if t is not None and t not in SEND_MESSAGE_TYPES:
        f.warn("SEND_TYPE", f"send_message type '{t}' unseen (corpus only has 'external'); "
                            f"a content-type here renders an empty block (step {sid})", where)
    if "value" in params:
        f.warn("SEND_VALUE", f"send_message has 'value' -- that is the `show` handler "
                             f"dialect; real send_message carries content in 'text' (step {sid})", where)
    # NO content-key check here. A template-driven send legitimately carries `text`
    # and `buttons` ONLY in the positions mirror, leaving the text blob with just
    # template_id (13 such sends across 4 known-good corpus bots). Checking one blob
    # in isolation is exactly the mistake that produced the wrong verdict on 2026-09-02.


def iter_handlers(node):
    """Yield every {handler, params} dict found anywhere under node (recursively)."""
    if isinstance(node, dict):
        if "handler" in node and isinstance(node.get("handler"), str):
            yield node
        for v in node.values():
            yield from iter_handlers(v)
    elif isinstance(node, list):
        for v in node:
            yield from iter_handlers(v)


def validate(wrapper, inventory=None):
    f = Findings()

    # ---- wrapper shape ----
    if not isinstance(wrapper, dict):
        f.err("WRAPPER", "Top-level must be an object {type_functionality, model}", "$")
        return f
    if "model" not in wrapper:
        f.err("WRAPPER", "Missing top-level 'model'", "$")
        return f
    if "type_functionality" not in wrapper:
        f.warn("WRAPPER", "Missing 'type_functionality' (corpus uses 0)", "$")
    model = wrapper["model"]
    if not isinstance(model, dict):
        f.err("WRAPPER", "'model' must be an object", "$.model")
        return f
    for key, typ in (("text", str), ("positions", str), ("name", str), ("type", (int, float))):
        if key not in model:
            f.err("MODEL", f"model.{key} missing", "$.model")
        elif not isinstance(model[key], typ):
            f.err("MODEL", f"model.{key} must be {typ}", f"$.model.{key}")
    if f.n_err:
        return f

    # text/positions are STRINGIFIED json
    try:
        text = json.loads(model["text"])
    except Exception as e:  # noqa: BLE001
        f.err("TEXT_PARSE", f"model.text is not valid JSON string: {e}", "$.model.text")
        return f
    try:
        positions = json.loads(model["positions"])
    except Exception as e:  # noqa: BLE001
        f.err("POS_PARSE", f"model.positions is not valid JSON string: {e}", "$.model.positions")
        return f
    if not isinstance(text, dict):
        f.err("TEXT_TYPE", "model.text must decode to an object keyed by step-id", "$.model.text")
        return f
    if not isinstance(positions, list):
        f.err("POS_TYPE", "model.positions must decode to an array of blocks", "$.model.positions")
        return f

    # ---- size limit ----
    tlen = len(model["text"].encode("utf-8"))
    if tlen > MAX_BOT_BYTES:
        f.err("SIZE", f"model.text is {tlen} bytes (> 64KB limit)", "$.model.text")

    # ---- text steps ----
    text_steps = {k: v for k, v in text.items() if k != "conversation"}
    if "conversation" not in text:
        f.warn("TEXT_CONV", "model.text missing top-level 'conversation' boolean (corpus has it)", "$.model.text")
    text_step_ids = set()
    text_block_uuid = {}  # step_id -> block_uuid
    for sid, step in text_steps.items():
        if not re.fullmatch(r"-?\d+", str(sid)):
            f.warn("STEP_ID", f"step id '{sid}' is not an integer-like key", f"text.{sid}")
        text_step_ids.add(str(sid))
        if not isinstance(step, dict):
            f.err("STEP_SHAPE", f"step {sid} must be an object", f"text.{sid}")
            continue
        blocks = [b for b in ("question", "answer", "finish") if b in step]
        if not blocks:
            f.err("STEP_BLOCKS", f"step {sid} has no question/answer/finish array", f"text.{sid}")
        bu = step.get("block_uuid")
        if bu is None:
            f.warn("BLOCK_UUID", f"step {sid} has no block_uuid", f"text.{sid}")
        else:
            if not (isinstance(bu, str) and UUID_RE.match(bu)):
                f.warn("BLOCK_UUID", f"step {sid} block_uuid '{bu}' not a uuid", f"text.{sid}")
            text_block_uuid[str(sid)] = bu
        for b in blocks:
            arr = step.get(b)
            if not isinstance(arr, list):
                f.err("BLOCK_ARR", f"step {sid}.{b} must be an array", f"text.{sid}.{b}")
                continue
            for i, h in enumerate(arr):
                if not isinstance(h, dict) or "handler" not in h:
                    f.err("HANDLER", f"step {sid}.{b}[{i}] is not a handler object", f"text.{sid}.{b}[{i}]")
                    continue
                hn = h["handler"]
                if hn not in KNOWN_HANDLERS:
                    f.warn("HANDLER_UNK", f"unknown handler '{hn}' (step {sid})", f"text.{sid}.{b}[{i}]")
                if hn == "send_message":
                    _check_send_message(f, h.get("params"), f"text.{sid}.{b}[{i}]", sid)

    # ---- positions blocks ----
    pos_by_id = {}
    pos_steps = set()
    pos_block_uuid = {}  # step -> uuid
    for j, blk in enumerate(positions):
        if not isinstance(blk, dict):
            f.err("POS_BLK", f"positions[{j}] must be an object", f"positions[{j}]")
            continue
        bid = blk.get("id")
        btype = blk.get("type")
        if bid is None:
            # the decorative trigger block legitimately has null/absent id (corpus uses null or -1)
            if btype != "static":
                f.err("POS_ID", f"positions[{j}] (type {btype}) missing 'id'", f"positions[{j}]")
        else:
            if bid in pos_by_id:
                f.err("POS_ID_DUP", f"duplicate positions block id {bid}", f"positions[{j}]")
            pos_by_id[bid] = blk
        step = blk.get("step")
        if step is not None:
            pos_steps.add(str(step))
            bu = blk.get("block_uuid")
            if bu:
                pos_block_uuid[str(step)] = bu
        if "actions" in blk and not isinstance(blk["actions"], list):
            f.err("POS_ACT", f"positions[{j}].actions must be an array", f"positions[{j}]")

    # ---- CONSISTENCY: the heart ----
    # 1. every text step appears as a positions block step
    for sid in text_step_ids:
        if sid not in pos_steps:
            f.err("SYNC_TEXT_POS", f"text step {sid} has no matching positions block (step {sid})", f"text.{sid}")
    # 2. block_uuid agreement where both present
    for sid, bu in text_block_uuid.items():
        pbu = pos_block_uuid.get(sid)
        if pbu and bu and pbu != bu:
            f.err("SYNC_UUID", f"block_uuid mismatch for step {sid}: text={bu} positions={pbu}", f"text.{sid}")
    # 3. every text BRANCH target resolves. Branch edges live in several handler shapes:
    #    goto {step,type}; waits.conditions[].action {step,type}; distribution.variants[] {step,type};
    #    conditions.params.result[] gotos (caught by recursion). Bare {step} targets (waits/distribution)
    #    are NOT handler:goto, so a naive goto-only scan misses them (false negative).
    all_steps = text_step_ids | pos_steps
    pos_step_type = {}
    for blk in positions:
        if isinstance(blk, dict) and blk.get("step") is not None:
            pos_step_type[str(blk.get("step"))] = blk.get("type")

    def text_targets(node):
        if isinstance(node, dict):
            h = node.get("handler")
            p = node.get("params", {})
            if h == "goto" and isinstance(p, dict):
                yield (p.get("step"), p.get("type"), "goto")
            elif h == "waits" and isinstance(p, dict):
                for c in p.get("conditions", []) or []:
                    a = (c or {}).get("action", {})
                    if isinstance(a, dict):
                        yield (a.get("step"), a.get("type"), "waits")
            elif h == "distribution" and isinstance(p, dict):
                for v in p.get("variants", []) or []:
                    if isinstance(v, dict):
                        yield (v.get("step"), v.get("type"), "distribution")
            elif h == "wait_answer" and isinstance(p, dict):
                yield (p.get("step"), p.get("type"), "wait_answer")
            for v in node.values():
                yield from text_targets(v)
        elif isinstance(node, list):
            for v in node:
                yield from text_targets(v)

    for sid, step in text_steps.items():
        if not isinstance(step, dict):
            continue
        for tgt, typ, kind in text_targets(step):
            if tgt is None:
                f.err("GOTO", f"{kind} in step {sid} missing target step", f"text.{sid}")
                continue
            if str(tgt) not in all_steps:
                f.err("GOTO_DANGLE", f"{kind} in step {sid} -> step {tgt} ({typ}) which does not exist", f"text.{sid}")
            elif typ in ("question", "finish") and str(tgt) in pos_step_type:
                bt = pos_step_type[str(tgt)]
                if bt and bt != typ:
                    f.warn("GOTO_TYPE_MATCH", f"{kind} in step {sid} -> step {tgt} declared '{typ}' but target block is '{bt}'", f"text.{sid}")
            # a goto into the 'answer' lane requires the target text step to actually have an answer block
            if typ == "answer" and str(tgt) in text_steps and isinstance(text_steps[str(tgt)], dict) \
                    and "answer" not in text_steps[str(tgt)]:
                f.warn("GOTO_BLOCK_MISSING", f"{kind} in step {sid} -> step {tgt} type 'answer' but that step has no answer block", f"text.{sid}")
            if typ is not None and typ not in GOTO_TYPES:
                f.warn("GOTO_TYPE", f"target type '{typ}' unexpected (step {sid})", f"text.{sid}")

    # 4. positions edges resolve: block-level goto.block AND every action's links[].block
    for j, blk in enumerate(positions):
        if not isinstance(blk, dict):
            continue
        g = blk.get("goto")
        if isinstance(g, dict) and g.get("block") is not None:
            if g["block"] not in pos_by_id:
                f.err("POS_GOTO_DANGLE", f"positions[{j}] (id {blk.get('id')}) goto.block {g['block']} has no such block", f"positions[{j}]")
        for a in blk.get("actions", []) or []:
            if isinstance(a, dict):
                for lk in a.get("links", []) or []:
                    if isinstance(lk, dict) and lk.get("block") is not None and lk["block"] not in pos_by_id:
                        f.err("POS_LINK_DANGLE", f"positions[{j}] (id {blk.get('id')}) action links.block {lk['block']} has no such block", f"positions[{j}]")

    # 4b. exactly one start block (INV-ONE-START)
    n_start = sum(1 for b in positions if isinstance(b, dict) and b.get("type") == "start")
    if n_start != 1:
        f.err("ONE_START", f"expected exactly 1 start block in positions, found {n_start}")

    # 4c. orphan positions block: a non-start/static/finish block whose step has no text entry
    for j, blk in enumerate(positions):
        if not isinstance(blk, dict):
            continue
        st = blk.get("step")
        if st is not None and str(st) not in text_step_ids and blk.get("type") not in ("start", "static", "finish"):
            f.warn("POS_ORPHAN", f"positions[{j}] (id {blk.get('id')}, type {blk.get('type')}) step {st} has no text entry", f"positions[{j}]")

    # 4d. block_uuid uniqueness across text steps
    seen_uuid = {}
    for sid, bu in text_block_uuid.items():
        if bu in seen_uuid:
            f.warn("BLOCK_UUID_DUP", f"block_uuid {bu} used by steps {seen_uuid[bu]} and {sid}")
        else:
            seen_uuid[bu] = sid

    # 4e. handler-shape structural checks (run without inventory)
    for h in iter_handlers(text):
        hn = h.get("handler")
        p = h.get("params", {})
        if not isinstance(p, dict):
            continue
        if hn == "send_message":
            srcs = p.get("chat_sources")
            broadcast = p.get("send_to_all_chat_sources") is True
            if isinstance(srcs, list):
                for s in srcs:
                    if isinstance(s, dict) and "id" in s and not isinstance(s["id"], int):
                        f.err("CHATSRC_TYPE", f"send_message chat_sources id must be int, got {type(s['id']).__name__} {s['id']!r}")
            if srcs and broadcast:
                f.err("SEND_CHANNEL_CONFLICT", "send_message has BOTH chat_sources and send_to_all_chat_sources=true")
            if not p.get("is_in_starting_block") and not srcs and not broadcast:
                f.warn("SEND_NO_CHANNEL", "non-starting send_message has neither chat_sources nor send_to_all_chat_sources")
        if hn == "action" and p.get("name") == "change_status" and isinstance(p.get("params"), dict):
            if p["params"].get("pipeline_id") is None:
                f.err("PIPELINE_REQUIRED", "change_status requires a pipeline_id (absent) — status alone is ambiguous")

    # 5. button limits
    for h in iter_handlers(text):
        p = h.get("params", {})
        if isinstance(p, dict):
            btns = p.get("buttons")
            if isinstance(btns, list):
                if len(btns) > MAX_BUTTONS:
                    f.warn("BUTTONS_MAX", f"{len(btns)} buttons (> {MAX_BUTTONS} recommended max)")
                for b in btns:
                    txt = b if isinstance(b, str) else (b.get("text") if isinstance(b, dict) else None)
                    if isinstance(txt, str) and len(txt) > MAX_BUTTON_LEN:
                        f.warn("BUTTON_LEN", f"button text >{MAX_BUTTON_LEN} chars may truncate on Messenger: '{txt[:30]}...'")

    # ---- INVENTORY pass ----
    if inventory is not None:
        _inventory_pass(f, text, positions, inventory)

    return f


def _inventory_pass(f, text, positions, inv):
    pipelines = {p["id"]: p for p in inv.get("pipelines", [])}
    pipeline_statuses = {p["id"]: {s["id"] for s in p["statuses"]} for p in inv.get("pipelines", [])}
    status_ids = {s["id"] for p in inv.get("pipelines", []) for s in p["statuses"]}
    user_ids = {u["id"] for u in inv.get("users", [])}
    lead_cf = {c["id"]: c for c in inv.get("lead_custom_fields", [])}
    contact_cf = {c["id"]: c for c in inv.get("contact_custom_fields", [])}
    all_cf = {**lead_cf, **contact_cf}
    enum_ids = {e["id"] for c in all_cf.values() for e in c.get("enums", [])}
    select_types = ("select", "multiselect", "radiobutton", "checkbox")
    cs = inv.get("chat_sources", {})
    # Only an explicit human-curated 'confirmed' list counts. The 'from_existing_bots'
    # scan is reference-only (may contain ids from FOREIGN accounts) and never confirms.
    confirmed_cs = set(cs.get("confirmed", []))
    bots = set(inv.get("bots", []) or [])  # optional: bot-chaining ids (resolve_ids may not populate)

    for h in iter_handlers(text):
        hn = h.get("handler")
        p = h.get("params", {})
        if not isinstance(p, dict):
            continue
        # change_status -> pipeline + status (status must belong to the pipeline)
        if hn == "action" and p.get("name") == "change_status":
            ap = p.get("params", {})
            sid_ = ap.get("value")
            pid = ap.get("pipeline_id")
            if pid is not None and pid not in pipelines:
                f.err("INV_PIPELINE", f"change_status pipeline_id {pid} not in this account")
            if sid_ is not None:
                if pid in pipeline_statuses:
                    if sid_ not in pipeline_statuses[pid]:
                        f.err("INV_STATUS_PIPELINE", f"change_status status {sid_} does not belong to pipeline {pid}")
                elif sid_ not in status_ids:
                    f.err("INV_STATUS", f"change_status value {sid_} not a status in this account")
        if hn == "action" and p.get("name") == "set_custom_fields":
            ap = p.get("params", {})
            cfid = ap.get("custom_fields_id")
            cf = all_cf.get(cfid) if isinstance(cfid, int) else None
            if isinstance(cfid, int) and cf is None:
                f.err("INV_CF", f"set_custom_fields custom_fields_id {cfid} not in this account")
            if cf is None:  # try the {{lead.cf.ID}} placeholder form
                cfp = ap.get("custom_field")
                if isinstance(cfp, str):
                    m = re.search(r"cf\.(\d+)", cfp)
                    if m:
                        cf = all_cf.get(int(m.group(1)))
            val = ap.get("value")
            # bare digit-string value targeting a select-typed CF must be a known enum id
            if isinstance(val, str) and val.isdigit() and cf and cf.get("type") in select_types:
                if int(val) not in {e["id"] for e in cf.get("enums", [])}:
                    f.err("INV_ENUM", f"set_custom_fields value {val} is not an enum id of CF {cf.get('id')} ({cf.get('name')})")
        if hn == "action" and p.get("name") == "change_responsible_user":
            uid = p.get("params", {}).get("value")
            if isinstance(uid, int) and uid not in user_ids:
                f.err("INV_USER", f"change_responsible_user value {uid} not a user in this account")
        if hn == "send_internal":
            uid = p.get("user_id")
            if isinstance(uid, int) and uid not in user_ids:
                f.err("INV_USER", f"send_internal user_id {uid} not a user in this account")
        if hn == "trigger":
            tr = p.get("trigger") if isinstance(p.get("trigger"), dict) else {}
            ru = (tr.get("settings") or {}).get("responsible_user")
            if ru not in ("current", None) and str(ru).isdigit() and int(ru) not in user_ids:
                f.err("INV_USER", f"trigger responsible_user {ru} not a user in this account")
        if hn == "start":
            bid = p.get("bot")
            if isinstance(bid, int) and bots and bid not in bots:
                f.err("INV_BOT", f"start.bot {bid} not a bot in this account")
        # chat_sources
        srcs = p.get("chat_sources")
        if isinstance(srcs, list):
            for s in srcs:
                cid = s.get("id") if isinstance(s, dict) else None
                if isinstance(cid, int) and cid not in confirmed_cs:
                    f.warn("INV_CHATSRC", f"chat_source id {cid} not confirmed for this account (verify channel)")

    # placeholder-referenced ids: {{lead.cf.NNN}} / {{lead.cf.NNN.MMM}} (cf id + enum id),
    # {{contact.cf.NNN}}, {{company.cf.NNN}}. A typo'd id silently breaks the bot at runtime.
    ph_re = re.compile(r"\{\{(?:lead|contact|company)\.cf\.(\d+)(?:\.(\d+))?\}\}")
    seen_cf, seen_enum = set(), set()

    def walk_strings(n):
        if isinstance(n, str):
            for m in ph_re.finditer(n):
                seen_cf.add(int(m.group(1)))
                if m.group(2):
                    seen_enum.add(int(m.group(2)))
        elif isinstance(n, dict):
            for v in n.values():
                walk_strings(v)
        elif isinstance(n, list):
            for v in n:
                walk_strings(v)

    walk_strings(text)
    for cfid in sorted(seen_cf):
        if cfid not in all_cf:
            f.err("INV_CF_PH", f"placeholder references custom field {cfid} not in this account")
    for eid in sorted(seen_enum):
        if eid not in enum_ids:
            f.err("INV_ENUM_PH", f"placeholder references enum id {eid} not in this account")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bot", help="path to a salesbot export json")
    ap.add_argument("--inventory", help="account inventory json from resolve_ids.py (enables ID checks)")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument("--strict", action="store_true", help="exit nonzero on WARN too")
    args = ap.parse_args()

    with open(args.bot) as fh:
        wrapper = json.load(fh)
    inv = None
    if args.inventory:
        with open(args.inventory) as fh:
            inv = json.load(fh)

    f = validate(wrapper, inv)

    if args.json:
        print(json.dumps({"errors": f.n_err, "warnings": f.n_warn, "findings": f.items}, ensure_ascii=False, indent=2))
    else:
        for it in f.items:
            mark = "✗" if it["severity"] == "ERROR" else "⚠"
            print(f"  {mark} [{it['code']}] {it['message']}" + (f"  ({it['where']})" if it["where"] else ""))
        status = "PASS" if f.n_err == 0 else "FAIL"
        print(f"{status}: {f.n_err} error(s), {f.n_warn} warning(s) — {args.bot.split('/')[-1]}")

    rc = 1 if f.n_err or (args.strict and f.n_warn) else 0
    sys.exit(rc)


if __name__ == "__main__":
    main()
