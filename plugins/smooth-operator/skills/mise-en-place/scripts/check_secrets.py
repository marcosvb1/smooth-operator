#!/usr/bin/env python3
"""Scan a map written by the mise-en-place skill for secrets and personal data.

Usage: python3 check_secrets.py [--public] [--include-local] [--no-external] <folder-or-file> [...]
       python3 check_secrets.py --self-test
(On Windows, run it with `py` or `python` instead of `python3`.)

--public         also flag real IDs (act_123..., gid://..., numbers with 15+
                 digits) in files that will live in a public repo.
--include-local  also scan *.local.* files, which by convention hold the real
                 IDs and stay out of git (skipped by default).
--no-external    don't run gitleaks or trufflehog even if they are installed.

Exits with code 1 if anything is found. Placeholders such as <TOKEN>, $VAR
and values containing "example" are ignored.

This is a safety net, not a guarantee: people's and companies' names,
addresses and free text can't be detected by patterns. Review samples by hand.
"""

import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PATTERNS = [
    # Credentials
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("Bearer token", re.compile(r"Bearer\s+(?![<$\{])[A-Za-z0-9._~+/=-]{20,}")),
    ("Basic auth", re.compile(r"Basic\s+(?![<$\{])[A-Za-z0-9+/]{16,}={0,2}")),
    ("Cookie header", re.compile(r"^\s*(?:Set-)?Cookie:\s*(?![<$\{])\S{16,}", re.I)),
    ("Meta access token", re.compile(r"\bEAA[A-Za-z0-9]{30,}")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("Stripe key", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("Anthropic/OpenAI key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}")),
    ("Shopify token", re.compile(r"\bshp(?:at|ss|ca|pa)_[A-Fa-f0-9]{20,}")),
    ("Notion token", re.compile(r"\b(?:ntn_|secret_)[A-Za-z0-9]{30,}")),
    ("Airtable token", re.compile(r"\bpat[A-Za-z0-9]{14}\.[a-f0-9]{40,}")),
    ("HubSpot private app token", re.compile(r"\bpat-(?:na|eu|ap)\d-[0-9a-f-]{30,}")),
    ("ClickUp token", re.compile(r"\bpk_\d+_[A-Z0-9]{20,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Webhook URL with secret", re.compile(
        r"https://(?:hooks\.slack\.com/services|discord(?:app)?\.com/api/webhooks|[\w.-]*webhook\.office\.com)/(?![<$\{])\S{10,}")),
    ("Credential in URL", re.compile(r"https?://[^\s/:@<]+:[^\s/@<]+@")),
    ("Token in query string", re.compile(
        r"[?&](?:access_token|api_key|apikey|token|key|secret|sig|signature)=(?![<$\{])[^\s&\"']{12,}", re.I)),
    ("Secret assignment", re.compile(
        r"(?<![A-Za-z0-9_-])(?![A-Za-z_-]*(?:next|page|continuation|sync|cursor)[_-])(?:[A-Za-z]+[_-])*"
        r"(?:token|secret|password|passwd|api[_-]?key|client[_-]?secret)[\"']?\s*[:=]\s*[\"']?(?![<$\{])([A-Za-z0-9._~+/=-]{16,})",
        re.I,
    )),
    # Personal data
    ("E-mail", re.compile(r"[\w.%+-]+@[\w-]+(?:\.[\w-]+)*\.[^\W\d_]{2,}")),
    ("Phone number (international)", re.compile(r"(?<![\w+])\+\d{1,3}[\s.-]?\(?\d{1,4}\)?(?:[\s.-]?\d{2,5}){2,4}\b")),
    ("Phone number", re.compile(r"(?<![\w(])\(\d{2,4}\)\s?\d{3,5}[\s.-]?\d{4}\b")),
    ("US SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("Brazil CPF", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
    ("Brazil CNPJ", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")),
]

# Values that collide with numeric IDs only count when the line carries a label.
PHONE_LABEL = re.compile(
    r"(?:phone|tel\b|tel:|tel\.|mobile|cell|fax|telefon|t[ée]l[ée]phone|tel[ée]fono|telefone|celular|"
    r"whatsapp|fone|電話|携帯|телефон|手机|电话|전화)", re.I)
PHONE_NUMBER = re.compile(r"(?<![\w-])\(?\d[\d\s().-]{6,18}\d(?![\w-])")
ID_LABEL = re.compile(
    r"\b(?:ssn|social security|nino|national insurance|ni number|dni|nie|nif|aadhaar|pan|sin|tfn|curp|rfc|"
    r"cpf|cnpj|rg|steuer-?id|personalausweis|passport|passaporte|pasaporte|national id)\b|マイナンバー", re.I)
ID_VALUE = re.compile(r"(?<![\w-])[A-Z0-9][A-Z0-9.\-/ ]{5,22}[A-Z0-9](?![\w-])", re.I)
CARD_LABEL = re.compile(r"\b(?:card|cart[ãa]o|tarjeta|karte|carte|visa|mastercard|amex|cc)\b", re.I)
CARD_GROUPED = re.compile(r"\b\d{4}([ -])\d{4}\1\d{4}\1\d{1,7}\b")
CARD_PLAIN = re.compile(r"\b\d{13,19}\b")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,4})?\b")

PUBLIC_IDS = [
    ("Real ID (act_)", re.compile(r"\bact_\d{6,}")),
    ("Real ID (gid://)", re.compile(r"gid://[A-Za-z]+/[A-Za-z]+/\d+")),
    ("Real ID (15+ digits)", re.compile(r"(?<![\w.])\d{15,}(?![\w.])")),
]

ALLOWED_EMAIL = re.compile(r"(?:example\.(?:com|org|net)|\.example\b|\.test\b|users\.noreply\.github\.com|noreply@)", re.I)
HEX_TOKEN = re.compile(r"(?<![A-Za-z0-9_$<{-])[0-9a-fA-F]{32,}(?![A-Za-z0-9_>}-])")
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
HASH_CONTEXT = re.compile(r"(?:image_hash|hash|sha\d*|md5|checksum|etag)\W", re.I)
HIGH_ENTROPY = re.compile(r"(?<![A-Za-z0-9_$<{-])[A-Za-z0-9_+/=-]{32,}(?![A-Za-z0-9_>}-])")


def entropy(s: str) -> float:
    counts = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in counts.values())


def luhn(digits: str) -> bool:
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


def iban_valid(text: str) -> bool:
    s = text.replace(" ", "").upper()
    if not 15 <= len(s) <= 34:
        return False
    s = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in s)) % 97 == 1


def digit_count(text: str) -> int:
    return sum(c.isdigit() for c in text)


def scan_line(line: str, public: bool = False):
    hits = []
    if PHONE_LABEL.search(line):
        hits += [("Phone number", m.group(0).strip()) for m in PHONE_NUMBER.finditer(line)
                 if 8 <= digit_count(m.group(0)) <= 15]
    if ID_LABEL.search(line):
        hits += [("National ID", m.group(0)) for m in ID_VALUE.finditer(line)
                 if digit_count(m.group(0)) >= 5 and not ID_LABEL.fullmatch(m.group(0))]
    for m in CARD_GROUPED.finditer(line):
        if luhn(re.sub(r"\D", "", m.group(0))):
            hits.append(("Payment card", m.group(0)))
    if CARD_LABEL.search(line):
        hits += [("Payment card", m.group(0)) for m in CARD_PLAIN.finditer(line) if luhn(m.group(0))]
    hits += [("IBAN", m.group(0)) for m in IBAN.finditer(line) if iban_valid(m.group(0))]
    if public:
        for label, pattern in PUBLIC_IDS:
            hits += [(label, m.group(0)) for m in pattern.finditer(line)]
    for label, pattern in PATTERNS:
        for m in pattern.finditer(line):
            text = m.group(0)
            if label == "E-mail" and ALLOWED_EMAIL.search(text):
                continue
            if "example" in text.lower() or "exemplo" in text.lower():
                continue
            hits.append((label, text))
    covered = " ".join(t for _, t in hits)
    if not HASH_CONTEXT.search(line):
        for m in HEX_TOKEN.finditer(line):
            text = m.group(0)
            if text in covered or text.isdigit() or UUID.match(text):
                continue
            if entropy(text) > 3.5:
                hits.append(("Hex token", text))
                covered += " " + text
    for m in HIGH_ENTROPY.finditer(line):
        text = m.group(0)
        if text in covered or text.isdigit():
            continue
        has_mix = any(c.isdigit() for c in text) and any(c.isalpha() for c in text)
        if has_mix and entropy(text) > 4.0:
            hits.append(("High-entropy string", text))
    # One finding per span: drop hits whose text sits inside a longer hit.
    unique = []
    for label, text in hits:
        if any(text != other and text in other for _, other in hits):
            continue
        if (label, text) not in unique:
            unique.append((label, text))
    return unique


def is_local(f: Path) -> bool:
    return ".local." in f.name or f.name.endswith(".local")


def iter_files(paths, include_local=False):
    for p in paths:
        path = Path(p)
        if path.is_file():
            yield path
        elif path.is_dir():
            for f in sorted(path.rglob("*")):
                if not f.is_file() or ".git" in f.parts or "__pycache__" in f.parts:
                    continue
                if is_local(f) and not include_local:
                    continue
                yield f


def read_text(f: Path):
    """Return the file's text, or None when it looks binary or can't be decoded."""
    data = f.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig")
    if b"\x00" in data[:4096]:
        # UTF-16 without a BOM shows up as every other byte being NUL.
        for enc in ("utf-16-le", "utf-16-be"):
            try:
                text = data.decode(enc)
            except UnicodeDecodeError:
                continue
            if text.isprintable() or "\n" in text:
                return text
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def redact(text: str) -> str:
    return text if len(text) <= 12 else f"{text[:6]}…{text[-4:]}"


def run_external(paths):
    """Run gitleaks and trufflehog when installed; return the number of findings."""
    found = 0
    for p in paths:
        if shutil.which("gitleaks"):
            r = subprocess.run(
                ["gitleaks", "detect", "--no-git", "--no-banner", "--redact", "-s", p,
                 "--report-format", "json", "--report-path", "/dev/stdout"],
                capture_output=True, text=True, timeout=300)
            try:
                items = json.loads(r.stdout or "[]")
            except json.JSONDecodeError:
                items = []
            for it in items:
                found += 1
                print(f"{it.get('File')}:{it.get('StartLine')}: gitleaks: {it.get('RuleID')}")
        if shutil.which("trufflehog"):
            r = subprocess.run(
                ["trufflehog", "filesystem", p, "--json", "--no-update"],
                capture_output=True, text=True, timeout=300)
            for line in r.stdout.splitlines():
                try:
                    it = json.loads(line)
                except json.JSONDecodeError:
                    continue
                meta = it.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {})
                found += 1
                print(f"{meta.get('file')}:{meta.get('line')}: trufflehog: {it.get('DetectorName')}")
    return found


SELF_TEST = [
    # Credentials
    ('"access_token": "aB3dE5fG7hJ9kL1mN3pQ5r"', True),
    ("auth_token: aB3dE5fG7hJ9kL1mN3pQ5r", True),
    ("refresh_token=aB3dE5fG7hJ9kL1mN3pQ5r", True),
    ("token: abcdefghijklmnop1234", True),
    ("Authorization: Bearer abcDEF1234567890abcdefXYZ987", True),
    ("Authorization: Basic dXNlcjpwYXNzd29yZDEyMzQ1Ng==", True),
    ("https://hooks.slack.com/services/T0000/B0000/XXXXXXXXXXXXXXXX", True),
    ("PAT: glpat-abcdefghijklmnopqrst", True),
    ("Access-Token: 9f8e7d6c5b4a39281706f5e4d3c2b1a0aabbccdd", True),
    # Personal data, several countries
    ("Phone: (415) 555-0132", True),
    ("phone: 020 7946 0958", True),
    ("phone +44 20 7946 0958", True),
    ("Telefon: 030 12345678", True),
    ("tel 06 12 34 56 78", True),
    ("電話 090-1234-5678", True),
    ("Телефон: +7 912 345-67-89", True),
    ("Telefone: 11 98765-4321", True),
    ("whatsapp 5511987654321", True),
    ("SSN 123-45-6789", True),
    ("IBAN DE89 3704 0044 0532 0130 00", True),
    ("card 4111 1111 1111 1111", True),
    ("DNI 12345678Z", True),
    ("NI number QQ123456C", True),
    ("Aadhaar 2345 6789 0123", True),
    ("CPF 12345678901", True),
    ("cpf 123.456.789-09", True),
    ("joao.silva@gmail.com", True),
    ("email: jürgen.müller@beispiel.de", True),
    # Must stay clean
    ("Authorization: Bearer $HUBSPOT_TOKEN", False),
    ('"access_token": "<TOKEN>"', False),
    ('"next_page_token": "Xk29fjaLq0Pz81mVn3TyBw7Rq2Ls"', False),
    ('"image_hash": "9f8e7d6c5b4a39281706f5e4d3c2b1a0"', False),
    ("id 3fa85f64-5717-4562-b3fc-2c963f66afa6", False),
    ("pipeline_id 12345678901", False),
    ("campaign 120212345678901234 created", False),
    ("dev@example.com", False),
    ("validated_at: 2026-10-10", False),
    ("| `<STAGE_ID>` | Qualified |", False),
]


def self_test():
    failed = 0
    for line, expected in SELF_TEST:
        got = bool(scan_line(line))
        if got != expected:
            failed += 1
            print(f"FAILED: expected {'a finding' if expected else 'clean'}: {line}")
    if not scan_line("ad account act_1234567890", public=True):
        failed += 1
        print("FAILED: --public should flag act_1234567890")
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "utf16.md"
        f.write_text("token: abcdefghijklmnop1234\n", encoding="utf-16")
        text = read_text(f)
        if not text or not any(scan_line(line) for line in text.splitlines()):
            failed += 1
            print("FAILED: UTF-16 file should be decoded and flagged")
    print("self-test ok" if not failed else f"{failed} case(s) failed")
    return 1 if failed else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    public = "--public" in argv
    include_local = "--include-local" in argv
    external = "--no-external" not in argv
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print(__doc__.strip())
        return 2
    found = 0
    skipped = []
    for f in iter_files(paths, include_local):
        try:
            text = read_text(f)
        except OSError as exc:
            skipped.append(f"{f} ({exc.strerror})")
            continue
        if text is None:
            skipped.append(f"{f} (binary)")
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for label, value in scan_line(line, public):
                found += 1
                print(f"{f}:{n}: {label}: {redact(value)}")
    if external:
        found += run_external(paths)
    for s in skipped:
        print(f"Skipped, not scanned: {s}")
    if found:
        print(f"\n{found} finding(s). Replace them with a placeholder or an environment variable, "
              "or explain the false positive.")
        return 1
    tools = [t for t in ("gitleaks", "trufflehog") if external and shutil.which(t)]
    print("No known secret or personal-data pattern found"
          + (f" (also checked with {', '.join(tools)})" if tools else "")
          + ". Names, addresses and free text can't be detected: review the samples by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
