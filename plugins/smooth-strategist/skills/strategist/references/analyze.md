# Analyze

An analysis says what happened. An insight says what that means for the question being asked. A capable model already knows which chart or method fits which question; this stage holds the few habits that separate a conclusion the user can rely on from one that merely sounds right.

Second of five stages: `frame` → **analyze** → `narrate` → `decide` → `plan`.

Respond in the user's language.

## What to do

1. Write the question each analysis must answer. If the user or their board already holds a belief about the data ("the ads are working", "we need more volume"), test that belief first and say plainly whether the data supports it.
2. Compute on the real data, with code if a code tool is available; otherwise show the arithmetic so the user can check it. Never invent a number. When estimating, show the assumption.
3. Write each insight as **what the data shows → why it matters for the question → what it suggests doing or checking**.
4. Run the last pass on the numbers (below) on the finished text.

## Traps that change the conclusion

- **Size the gap first.** When there is a target, say how far the result is from it and what the best case of the proposed fix would yield. A fix that closes a tenth of the gap is not the answer, however sound it is.
- **Like with like.** Both sides of a comparison cover the same period and the same definition. No full year against a half year. In a seasonal series, compare equivalent periods (peak with peak), not neighbouring ones.
- **Average hides marginal.** An average can look stable while the last increment costs several times more. When effort was added, compute what the added effort bought.
- **A total must add up.** When explaining the gap between two numbers, the parts must sum to it exactly. A remainder is a missing or double-counted factor.
- **Missing is not zero.** A blank cell, a period that has not finished or a cohort too young to measure is unknown. Leave it out of rates and say so.
- **Small samples prove nothing.** Five out of thirty-five is a lead to follow, not a rate to project.
- **Too neat is suspect.** An identical value every period is probably an allocation, not a measurement.
- **Timing is evidence, not proof.** When a change coincides with an event, say that it coincides and what else could explain it.
- **Fact apart from reading.** Say what the data shows, then what you make of it.

## Last pass on the numbers

Most errors in an analysis are a wrong figure in an otherwise right sentence. After the text is written, go through every number in it, one by one:

- recompute it from the data instead of trusting the figure carried over from an earlier step;
- check the label next to it: the period, the unit and what it counts ("February to June" followed by six values is wrong before any arithmetic);
- check every claim of direction or range ("fewer than", "every month", "between X and Y") against all the values it covers;
- check derived figures (rates, per-unit costs, break-even points, time estimates) by dividing or adding the parts again.

Fix what does not match and drop a number that cannot be verified. A side figure that adds colour and turns out wrong costs more trust than it earned.

## What to deliver

Only the insights that answer the question, in the quantity asked for (if they asked for 3, give 3). Each one has the message in one sentence, the numbers behind it with their period, and why it matters and what to do or check. After them, one line per hypothesis tested and not supported, then the assumptions and the missing data, in a few lines.

Left out: explanations of how an analysis works, status tables, and this stage's vocabulary. Produce a chart, spreadsheet or slide only if the user asks or the deliverable is visual, with the tools the environment has; a chart nobody asked for costs time and does not improve the conclusion. Prose, lists and tables follow the user's preferences when they have any.

When the findings need to become a recommendation for someone, the next stage is `narrate`.
