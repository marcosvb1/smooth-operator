# smooth-strategist evals

The skill produces advice, not code, so "is the answer good?" has no test. Two narrower things can be tested, and this suite has a set for each.

- **Trap cases** (13, tag `trap`): each prompt plants one trap whose right answer is known by construction (a target the proposed fix cannot reach, an average that hides the marginal cost, a claim the user's own numbers contradict, a date the dependencies make impossible). A run passes when the answer catches the trap.
- **Trigger cases** (20, tag `holdout`): 10 requests where the skill should fire and 10 near misses where it should not (definitions, translation, code, ad copy, fiction). They were written after the skill's description and have not been used to edit it; keep it that way, or add new ones when the description changes.

Neither set measures whether a framing or a plan is wise. That still takes a person who knows the domain.

Graders are pass/fail. `regex` graders check a figure that must appear, or a placeholder that must not. `llm` graders ask one narrow question about the trap, judged 2-of-3. `fires.md` and `does-not-fire.md` (`tool_used: Skill`) check whether the skill was invoked. The list of cases is in [CASES.md](CASES.md).

## Run

From the repo root, with Claude Code and a logged-in account or `ANTHROPIC_API_KEY`:

```bash
claude plugin eval ./plugins/smooth-strategist --tag trap --model sonnet --judge-model sonnet \
  --concurrency 8 --no-publish --trust-plugin --max-cost-usd 8 --json trap.json
```

```bash
claude plugin eval ./plugins/smooth-strategist --tag holdout --ablation none --model sonnet \
  --concurrency 8 --no-publish --trust-plugin --max-cost-usd 4 --json trigger.json
```

The trap run executes each case three times with the plugin and three times without (about US$ 5 on Sonnet); add `--ablation none` to skip the no-plugin arm. The trigger run needs no baseline (about US$ 3). Results and the HTML report go to `evals/results/<timestamp>/` (git-ignored).

## Reading a trap result

1. **Did the skill fire?** If not, the two arms are the same model answering alone.
2. **Does the no-plugin arm already pass?** Then the rule covering this trap adds nothing on this model, and the case is only a regression check.
3. **Does the plugin arm pass where the baseline fails?** This is the only evidence that a rule earns its place.

Three runs per arm is little: one run flipping moves a case by 33 points. Treat 3/3 against 0/3 as a difference and 2/3 against 3/3 as noise.

## Results so far (Sonnet, 3 runs per case, 39 runs per column)

The plugin started as five separate skills (`frame`, `analyze`, `narrate`, `decide`, `plan`). The first trap run showed the right skill often did not fire, so they were merged into one skill with a stage check. Same 13 trap cases in all three columns:

| | no plugin | five skills | one skill |
| --- | --- | --- | --- |
| runs where a skill fired | n/a | 21 of 39 | 37 of 39 |
| runs that caught the trap | 33 of 39 | 34 of 39 | 38 of 39 |
| `f02-gap-vs-campaigns` | 0 of 3 | 0 of 3 | 3 of 3 |
| `n02-no-blanks` | 1 of 3 | not comparable (grader changed) | 3 of 3 |

Trigger cases against the single skill: fired in 30 of 30 should-trigger runs and in 0 of 30 should-not-trigger runs.

What it shows:

- The model alone catches 11 of the 13 traps every time. On those, the skill is a regression check, not an improvement.
- The two traps the model alone misses are the ones the single skill fixes: listing campaigns when asked how to go from 57 enrollments to 1,000 (`f02`), and leaving a blank in an email that has to be sent today (`n02`).
- Most of the gain from merging came from the skill firing at all. The comparison is not clean: the single skill's description was written after seeing the trap cases and is more insistent, so part of the gain may be the description and not the merge. The trigger cases are the check on that, since the description never saw them.

Corrections made to graders along the way, so the columns are read with the same rules: `d01` matched `130` only as a whole word and missed "130k"; `p02` had a two-part criterion that failed correct answers; `n02` flagged an "R$ X" written in the note to the user, outside the email. The one-skill column is the run before four one-line wording fixes from review; only `n02` was rerun after them.

## Limits

- The traps were written by the same author as the skill. A trap the author did not think of is not here.
- The sandbox loads only this plugin. In real use other skills compete for the same request, so the trigger numbers are an upper bound on recall and a lower bound on false positives.
- `llm` graders are a model's reading. Keep each criterion to one checkable claim; a criterion with two conditions fails for the wrong reason.
