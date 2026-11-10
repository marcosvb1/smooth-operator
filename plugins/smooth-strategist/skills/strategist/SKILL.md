---
name: strategist
description: "Use for any request to work through a problem, a set of numbers, a message to a decision-maker, a choice or an execution plan, in any domain: defines the problem and breaks it down, draws conclusions from data, writes the recommendation or summary, lays out a decision, or turns a decision into a plan, and checks that the earlier steps hold before doing the one asked for. Use it even when the request looks simple or already names its solution, e.g. \"which campaigns do we run to hit the target?\", \"sales dropped, what do we do?\", \"what do these numbers show?\", \"which channel is dragging us down?\", \"write the email asking for approval\", \"write the exec summary\", \"build or buy?\", \"build the decision matrix\", \"plan the rollout\", \"que campanhas a gente roda pra bater a meta?\", \"o que esses dados dizem?\", \"escreve o e-mail pro diretor\", \"monta a matriz de decisão\", \"monta o plano\". Not for hands-on debugging of code in the current repo, planning code changes, brand or ad copy, or fiction."
---

# Strategist

One cycle, five stages: **frame** the problem → **analyze** the evidence → **narrate** the answer → **decide** between options → **plan** the execution. A request usually asks for one stage. The answer is only as good as the stages before it, so place the request in the cycle first. When the request names several stages ("analyze this and write the email"), do them in cycle order, reading each reference as you reach it.

Respond in the user's language.

## 1. Find the stage asked for

| The user wants | Stage | Read |
| --- | --- | --- |
| To understand or structure a vague problem | frame | `references/frame.md` |
| Conclusions from data or evidence | analyze | `references/analyze.md` |
| A piece of writing that carries findings to someone | narrate | `references/narrate.md` |
| A choice or a priority order laid out | decide | `references/decide.md` |
| A chosen direction turned into execution | plan | `references/plan.md` |

## 2. Check the stages before it, once

Do this in your head, in one pass. It is a gate, not a review to write up.

- **Is the problem defined?** Is there a goal, and is the distance to it known? If the request jumps to a solution ("which campaigns do we run?", "how do we roll out a chatbot?") while the gap is large or its cause is unknown, the solution asked for may not be the answer.
- **Does the evidence support what is being asked?** Do the user's own numbers hold up (the arithmetic, the period, the claim they want made)?
- **Is the choice made?** A plan for a direction nobody has chosen hides the choice.

Then:

- If the earlier stages hold, go straight to the stage asked for. Do not redo or restate them.
- If an earlier stage is missing or wrong **and that changes the answer**, do the minimum of it first, in a few lines at the top (the size of the gap, the corrected figure, the decision still open), and then do the stage asked for in the light of it. If the fix needs more than a few lines, read the earlier stage's reference as well.
- If it is missing but would not change the answer, leave it.

## 3. Do the stage

Read the reference file for the stage and follow it. Each one says what to deliver and what to leave out.

## 4. Point to the next stage

End with one line on what comes next in the cycle, only when it is not obvious to the user. Do not start it unasked.
