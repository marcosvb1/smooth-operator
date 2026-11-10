# smooth-strategist evals

These skills produce advice, not code, so "is the answer good?" has no test. What can be tested is narrower: each case here plants one trap whose right answer is known by construction (a target the proposed fix cannot reach, an average that hides the marginal cost, a claim the user's own numbers contradict, a date the dependencies make impossible). A run passes when the answer catches the trap. The suite does not measure whether a framing or a plan is wise; that still takes a person who knows the domain.

- 13 cases: 4 `analyze`, 3 `narrate`, 2 `decide`, 2 `frame`, 2 `plan`; English and Portuguese.
- Graders are pass/fail. `regex` graders check a figure that must appear (or a placeholder that must not). `llm` graders ask one narrow question about the trap, judged 2-of-3.
- Each case also has `fires.md` (`tool_used: Skill`). Under the with/without comparison it is not part of the score; it shows whether the skill was invoked at all.

The list is in [CASES.md](CASES.md).

## Run

From the repo root, with Claude Code and a logged-in account or `ANTHROPIC_API_KEY`:

```bash
claude plugin eval ./plugins/smooth-strategist --model sonnet --judge-model sonnet \
  --concurrency 8 --no-publish --trust-plugin --max-cost-usd 12 --json results.json
```

Each case runs three times with the plugin and three times without. `--case 'a0*'` or `--tag analyze` narrows the run. A full run cost about US$ 5 on Sonnet. Results and the HTML report go to `evals/results/<timestamp>/` (git-ignored).

## Reading the result

Read three things per case, in this order:

1. **Did the skill fire?** If not, the two arms are the same model answering alone, and the case says nothing about the skill's content.
2. **Does the no-plugin arm already pass?** Then the rule that covers this trap adds nothing on this model, and the case is only a regression check.
3. **Does the plugin arm pass where the baseline fails?** This is the only evidence that a rule earns its place.

Three runs per arm is little: one run flipping moves a case by 33 points. Treat 3/3 against 0/3 as a difference and 2/3 against 3/3 as noise.

## First run (Sonnet, 3 runs per arm)

| case | skill fired | with plugin | without |
| --- | --- | --- | --- |
| a01-gap-size | 3/3 | pass | pass |
| a02-marginal-cost | 3/3 | 2/3 on one grader | pass |
| a03-mix-shift | 0/3 | pass | pass |
| a04-partial-month | 0/3 | pass | pass |
| d01-ruinous-worst-case | 3/3 | pass | pass |
| d02-weighted-winner | 0/3 | pass | pass |
| f01-solution-in-problem | 3/3 | pass | pass |
| f02-gap-vs-campaigns | 0/3 | 0/3 | 0/3 |
| n01-payback-claim | 0/3 | pass | pass |
| n02-no-blanks | 0/3 | 2/3 | 1/3 |
| n03-wrong-growth | 3/3 | pass | 2/3 on one grader |
| p01-direction-not-settled | 3/3 | pass | pass |
| p02-infeasible-date | 3/3 | pass | pass |

What it shows:

- The model without the plugin catches 11 of the 13 traps. On these traps the skills add no measurable accuracy.
- The skill did not fire in 6 of 13 cases, including the two cases that fail (`f02`, `n02`). The first thing to fix is the triggering, not the content.
- `f02` is the one trap the baseline misses every time: asked which campaigns to run to go from 57 to 1,000, it lists campaigns. In an earlier manual test where `frame` was loaded, the answer started from the size of the gap.

## Limits

- The traps were written by the same author as the skills. A trap the author did not think of is not here.
- The sandbox loads only this plugin; in real use other skills compete for the same request.
- `llm` graders are a model's reading. Keep each criterion to one checkable claim; a criterion with two conditions fails for the wrong reason.
