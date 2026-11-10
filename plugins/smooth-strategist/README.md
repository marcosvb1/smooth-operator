# smooth-strategist

Structured problem solving for any domain, in five skills that follow one cycle. Each works on its own; together they take a vague request to an executable plan.

| Skill | Use it when | You get |
| --- | --- | --- |
| `frame` | The request is vague and nobody wrote down what the problem is | A testable problem statement and a tree of drivers or hypotheses with an analysis plan |
| `analyze` | There is data or evidence and you need conclusions | The few insights that answer the question: fact, why it matters, what to do |
| `narrate` | Findings have to reach someone who decides | A storyline with the answer first and the evidence under it |
| `decide` | There is a choice between options or a list to prioritize | The options side by side on the same criteria, what is reversible, who decides |
| `plan` | A direction is chosen and has to become execution | Phases, workstreams with owners, milestones, pending decisions, risks, what to measure |

The skills are not tied to business problems. The same method serves "sales dropped", "the test suite got slow", "which vendor do we pick" or "should I change careers"; vocabulary and examples come from the user's domain. They answer in the user's language.

## Install

```bash
/plugin marketplace add marcosvb1/smooth-operator
```

```bash
/plugin install smooth-strategist@smooth-operator
```

Then ask in plain words ("sales dropped, what do we do?", "what does this spreadsheet tell us?", "help me choose between these three vendors") or call a skill directly, e.g. `/smooth-strategist:frame`.

## Design

- **Result, not method.** Each skill uses its frameworks to think and check, and keeps them out of the answer. The reader gets the statement, the insight, the comparison or the plan.
- **No invented numbers.** Targets, dates, owners, scores and probabilities belong to the user. When they are missing, the skill leaves a marked slot.
- **Recommendation only on request.** `decide` lays the options out fairly and names a winner only when asked.
- **No connectors or external tools required.** `analyze` and `decide` compute with code when the environment can run it and show the arithmetic when it cannot. For charts, decks or spreadsheets the skills hand the structure to whatever skill the environment has.

## Sources

The main methods come from published work, cited where each is used: Barbara Minto, *The Pyramid Principle*; Charles Conn and Robert McLean, *Bulletproof Problem Solving*; Arnaud Chevallier and Albrecht Enders, *Solvable*; A.G. Lafley and Roger Martin, *Playing to Win*; Jeff Bezos's 2015 and 2016 letters to Amazon shareholders; Gokul Rajaram's SPADE; Kenn Adams's Story Spine; Gary Klein's pre-mortem; the urgent vs. important matrix attributed to Dwight Eisenhower.
