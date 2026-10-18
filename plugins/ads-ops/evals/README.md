# ads-ops evals

Trigger eval for the two skills in this plugin: does `meta-ads-upload` or `tiktok-ads-ops` fire when it should, and stay out of the way when it shouldn't? Both skills make real writes to ad accounts, so false positives matter more than recall here: a request for a report must not load an upload playbook.

- 14 `should-trigger` cases: 8 for Meta (upload, duplicate, move, swap creative, Instagram post to ad, audit before creating, budget update) and 6 for TikTok (campaign, upload, pause, Spark Ads, API error, bid). English and Portuguese.
- 12 `should-not-trigger` near misses: performance reports, dashboards, exports, n8n or BigQuery integrations, ad copywriting, auction concepts, organic posting and Google Ads.
- Each case has two deterministic `tool_used: Skill` graders. A Meta case checks that `meta-ads-upload` fires and `tiktok-ads-ops` doesn't, a TikTok case the reverse, and a near miss that neither fires. No LLM judge.
- Cases only allow `Read`, `Glob`, `Grep` and `Skill`, so a run can't call an ad API even when a skill fires.

The full list is in [CASES.md](CASES.md).

## Run

From the repo root, with Claude Code and an `ANTHROPIC_API_KEY` (or a logged-in account):

```bash
claude plugin eval ./plugins/ads-ops --ablation none --concurrency 4 \
  --max-cost-usd 2 --threshold 0 --no-publish --trust-plugin --json results.json
```

- `--ablation none`: the no-plugin arm can't fire either skill, so it adds cost and no signal.
- `--threshold 0`: without it the command exits 1 when any case misses.
- `--model <id>` pins the model; `--tag meta`, `--tag tiktok` or `--tag should-not-trigger` runs one group.
- Results and the HTML report go to `evals/results/<timestamp>/` (git-ignored).

## Reading the result

Report recall per skill and the false-positive rate separately. With 3 runs per case, a group of 6 to 12 cases moves by about ±12 to ±20 points from noise alone, so a smaller change between two runs is not a real difference.

## Limits

- The sandbox loads only this plugin. In real use other skills compete for the same request (for example, an official Meta Ads connector), so false positives here are a lower bound and recall an upper bound.
- `max_turns: 3` keeps runs cheap: the grader only needs to see whether a skill was invoked.
