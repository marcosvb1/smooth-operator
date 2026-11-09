# Step details

Details for steps 3 to 7 of `SKILL.md`. Read the section for the step you are on.

## 3. Accounts

List, with read calls only, the accounts, workspaces, portals, subdomains or projects that are visible. For each one: name, ID, what it's for, currency and time zone when they exist, and the profile or variable that selects it. Show the list and ask which ones are actually used and which is the default; the default goes into the `README.md` frontmatter (`default_account`).

## 4. Objects and properties

For each object relevant to the goal (template: `templates/object.md`):

- Pull the **schema** from the metadata endpoint or tool (properties, custom fields, event types), not from samples: a sample only shows what happens to be filled in.
- Record per property: API name, UI label, type, whether it's required or read-only, enum options with their **IDs** (pipeline statuses, stages, lists, tags), and what it means for the business when that isn't obvious.
- Record the **relations** (lead → contact → company; campaign → ad set → ad) and how to navigate between them.
- Prefer the schema. Read a real record only if the schema leaves the shape unclear: at most 1 to 3, requesting only fields without personal data (`fields=`, `properties=`, a `SELECT` of named columns). Never read records in tools that hold special categories (health, children, biometrics, an individual's finances); those maps stay schema-only.
- Add the optional `Personal data` column (`no`, `yes`, `sensitive`) when the user wants it: the map then doubles as a data inventory for GDPR article 30 or LGPD article 37 records.

Objects outside the goal get one row in the `README.md` table, with no file of their own.

## 5. Payloads

For each common operation (list, search, create, update, move…), keep the request/response pair **that worked**, minimal, with the path or tool, parameters, body and an excerpt of the response (template: `templates/payload.md`).

- Reads: run them for real.
- Writes: don't execute them just to document them. In this order:
  1. the tool's own dry-run, sandbox or validation (`validate_only`, test mode), when it exists;
  2. a write the user already asked for in this session: record its payload;
  3. if the tool has none of that (common in CRMs and task managers), propose **one** reversible write on a test object to the user (create a "mise-en-place test" lead and delete it right after, for example) and only do it after they say yes. Before proposing it, check what the write can trigger outside the tool: automations and workflows on that object (welcome emails or WhatsApp messages), webhooks, and conversion events sent to ad platforms, which pollute campaign optimization. Use obviously fake data on `example.com`, and remember a delete may be a soft delete that stays in the audit log;
  4. otherwise, record it from the documentation and mark it `docs`.
- A write that spends money, messages third parties or deletes real data never goes through option 3.
- Note the errors that came up and what fixed them: it's the most valuable part of the map.

## 6. Redaction and secrets

- **Never** write a token, password, API key, cookie or signed URL in any map file, `data.local.json` included: synced folders, backups and shared drives leak local files. Credentials appear as `$VARIABLE_NAME` or `<TOKEN>` and live in an environment variable or a secret manager (1Password, Doppler, Vault…). If the destination already keeps credentials in a local file, don't add more, and point it out to the user.
- If the project already separates real values another way (`.env` + `.env.example`, a secret manager), follow it instead of `data.local.json`.
- Personal data (names, emails, phones, ID documents, addresses of leads, customers and the team's own users) becomes placeholders: `<NAME>`, `<EMAIL>`, `<PHONE>`, `<NATIONAL_ID>`, `<ADDRESS>`.
- Account, page, pipeline and field IDs are **not secrets** and are what makes the map useful. In a public or shared repo, the `.md` files use `<AD_ACCOUNT_ID>`, accounts appear as neutral slugs (`client-a`) because a client's name can reveal a business relationship under NDA, and the real IDs and names live in `data.local.json`, with the same shape as `data.example.json` (check that `.gitignore` covers `*.local.json` and offer to add it). In a private vault or repo, IDs in the `README.md` tables are fine and more practical.
- Run the check. `scripts/check_secrets.py` lives in the skill folder and only uses the Python standard library:

```bash
python3 <skill-folder>/scripts/check_secrets.py [--public] <destination>/<tool>
```

(`py` or `python` on Windows.)

  - Credentials: JWTs, bearer and basic auth, cookies, `*_token`/`*_secret` with a value, keys with known prefixes, webhook URLs with secrets, hex tokens and long high-entropy strings.
  - Personal data: emails (Unicode included), phone numbers in international format or next to a phone label in many languages, payment cards (Luhn), IBANs (checksum), US SSNs, Brazilian CPF/CNPJ, and national IDs next to their label (SSN, NINO, DNI, NIE, Aadhaar, PAN, SIN, TFN, CURP, RFC…).
  - It reads UTF-8 and UTF-16, scans every file regardless of extension, and lists the files it had to skip.
  - It skips `*.local.*` files, which hold the real IDs by convention (`--include-local` scans them too).
  - When `gitleaks` or `trufflehog` is installed it runs them as well (`--no-external` to skip).
  - With `--public`, it also flags real IDs (`act_…`, `gid://…`, numbers with 15+ digits). Use it when the destination is a public repo.
  - Names and addresses have no reliable pattern: re-read the samples yourself.
  - Fix everything it flags or explain the false positive to the user.
  - `--self-test` runs the script's own example cases.
- Without Python in the session, search by hand, for example `grep -rnE 'eyJ|Bearer [A-Za-z0-9]|sk_|_token"?: ?"?[A-Za-z0-9]|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|\+?[0-9][0-9 ()-]{9,}[0-9]' <destination>/<tool>`.

## 7. Steering (`rules.md`)

Write the rules a future session needs to follow to avoid mistakes (template: `templates/rules.md`). Use `steering-checklist.md` as the checklist: rate limits and pagination, which operations are irreversible or cost money, safe defaults (e.g. always create paused), the account's naming conventions, format pitfalls (money in cents, time zones, IDs as strings), and when to stop and ask. One rule per line, with the reason when it isn't obvious.
