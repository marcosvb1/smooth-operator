# smooth-strategist

Structured problem solving for any domain: one skill, `strategist`, that works through five stages of one cycle. It finds the stage a request asks for, checks once that the stages before it hold, and goes back to one only when that changes the answer.

| Stage | Use it when | You get |
| --- | --- | --- |
| `frame` | The request is vague and nobody wrote down what the problem is | A testable problem statement and a tree of drivers or hypotheses with an analysis plan |
| `analyze` | There is data or evidence and you need conclusions | The few insights that answer the question: fact, why it matters, what to do |
| `narrate` | Findings have to reach someone who decides | A storyline with the answer first and the evidence under it |
| `decide` | There is a choice between options or a list to prioritize | The options side by side on the same criteria, what is reversible, who decides |
| `plan` | A direction is chosen and has to become execution | Phases, workstreams with owners, milestones, pending decisions, risks, what to measure |

The skill is not tied to business problems. The same method serves "sales dropped", "the test suite got slow", "which vendor do we pick" or "should I change careers"; vocabulary and examples come from the user's domain. It answers in the user's language.

## Install

```bash
/plugin marketplace add marcosvb1/smooth-operator
```

```bash
/plugin install smooth-strategist@smooth-operator
```

Then ask in plain words ("sales dropped, what do we do?", "what does this spreadsheet tell us?", "help me choose between these three vendors") or call the skill directly with `/smooth-strategist:strategist`.

## Design

- **One skill, not five.** With five separate skills the right one often did not fire, and none of them looked back: asked which campaigns to run to go from 57 enrollments to 1,000, the model listed campaigns. One skill with a stage check fired in 37 of 39 runs of the same eval cases, against 21 of 39 (see [evals](evals/README.md)).
- **Result in the body, method in a note.** Each stage uses its frameworks to think and check, and keeps them out of the body of the answer. Every answer then closes with a short **Method** note: the stage, the technique used and why that one, the steps done and skipped, and what the stage check found. The note is what makes an answer auditable against the method.
- **No invented numbers.** Targets, dates, owners, scores and probabilities belong to the user. When they are missing, the skill says so instead of filling them in.
- **Recommendation only on request.** The `decide` stage lays the options out fairly and names a winner only when asked.
- **No connectors or external tools required.** The `analyze` and `decide` stages compute with code when the environment can run it and show the arithmetic when it cannot. For charts, decks or spreadsheets the skill hands the structure to whatever skill the environment has.

## Sources

The main methods come from published work, cited where each is used: Barbara Minto, *The Pyramid Principle*; Charles Conn and Robert McLean, *Bulletproof Problem Solving*; Arnaud Chevallier and Albrecht Enders, *Solvable*; A.G. Lafley and Roger Martin, *Playing to Win*; Jeff Bezos's 2015 and 2016 letters to Amazon shareholders; Gokul Rajaram's SPADE; Kenn Adams's Story Spine; Donald Miller, *Building a StoryBrand*; Jason Ocker's five-act pitch arc after Gustav Freytag; the 5 Whys from the Toyota Production System; Gary Klein's pre-mortem; the urgent vs. important matrix attributed to Dwight Eisenhower.
