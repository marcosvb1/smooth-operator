# Analyze

An analysis says what happened. An insight says what that means for the question being asked. This stage holds the analyses to choose from, and the habits that separate a conclusion the user can rely on from one that merely sounds right.

Second of five stages: `frame` → **analyze** → `narrate` → `decide` → `plan`.

Respond in the user's language.

## What to do

1. Write the question each analysis must answer, and pick the analysis that answers it from the table below. If the user or their board already holds a belief about the data ("the ads are working", "we need more volume"), test that belief first and say plainly whether the data supports it.
2. Compute on the real data, with code if a code tool is available; otherwise show the arithmetic so the user can check it. Never invent a number. When estimating, show the assumption.
3. Write each insight as **what the data shows → why it matters for the question → what it suggests doing or checking**.
4. Run the last pass on the numbers (below) on the finished text.

## Which analysis to use

Choose by the question, not by the data that happens to be there. One question, one analysis; a second one only when the first leaves the question open.

| The question is | Analysis | What it has to contain |
| --- | --- | --- |
| How did it change over time? | **Trend** | The same measure over equal periods, and where the direction changed |
| How does it compare with another item, another period or the target? | **Comparison** (against a target: **actual vs. target**) | Both sides on the same definition and period, and the size of the difference |
| What is it made of, and did the make-up change? | **Mix** | Shares that add to 100%, at two points in time when the question is about change |
| How are the values spread? | **Distribution** | Median, range or quartiles, and the outliers; an average alone does not answer this |
| Do two things move together? | **Relationship** | The pairs of values, how tight the pattern is, and what else could explain it |
| Do a few items account for most of the total? | **Concentration** (Pareto) | Items ordered by size with the cumulative share |
| How did the positions change? | **Rank** | Each item's position at the start and at the end, and why the movers moved |
| What explains the gap between two numbers? | **Bridge** (waterfall) | Start, each factor with its sign, end; the factors add up exactly |
| What did the last increment of effort buy? | **Marginal return** | Added input against added output, step by step, beside the average |
| Is acquiring a customer worth it? | **Unit economics** | Lifetime value (profit per customer over the time they stay), acquisition cost, the ratio between them and the months to pay back the cost |
| Does an investment pay back over time? | **Discounted cash flow** (net present value) | Cash in and out per period, including the initial outlay, each discounted to today and summed; the discount rate stated |
| How well does the business turn capital into profit? | **Return on invested capital** | Operating profit after tax over invested capital (net working capital plus fixed assets), each side opened into its drivers |
| How much of each sale is kept? | **Profit margin** | Revenue, costs, and profit as a share of revenue, at the level asked about (gross, operating or net), across periods |
| Why did this happen? | **Root cause** (5 Whys) | A chain of "why?" from the symptom down to a cause someone can act on, each link supported by a fact |
| What exactly happened? | **Six questions** (who, what, when, where, why, how) | Each question answered from the evidence, with the unanswered ones named |
| Which of the known cases is this? | **Yes/no path** | A sequence of yes/no checks, each one answerable from the data, ending in a diagnosis |

The 5 Whys come from Sakichi Toyoda and the Toyota Production System; the rest are standard analyses.

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

Only when the user asks for a visual or the deliverable is one, pick the form by what it must show: a table of category, description, impact and takeaway for several findings side by side; a chart with a headline and the one figure that matters called out; two axes with four quadrants to sort options; before and after for a change of state; phases or a timeline for a sequence; a journey for what a customer goes through; a positioning map against competitors; a segment map with the size of each segment; a heat map for ratings across many items. Whatever the form, it carries a headline, the evidence and what follows from it.

Left out of the body: explanations of how an analysis works, status tables, and this stage's vocabulary (the method note that closes the answer is the one exception). Produce a chart, spreadsheet or slide only if the user asks or the deliverable is visual, with the tools the environment has; a chart nobody asked for costs time and does not improve the conclusion. Prose, lists and tables follow the user's preferences when they have any.

When the findings need to become a recommendation for someone, the next stage is `narrate`.
