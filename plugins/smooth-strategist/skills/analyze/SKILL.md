---
name: analyze
description: "Use when there is data, a spreadsheet, numbers or collected evidence and the user needs conclusions that answer a question, not just a description: picks the analysis each question calls for (trend, comparison, composition, concentration, bridge between two numbers, root cause), runs it and writes each finding as fact, why it matters and what to do about it. Fits any domain, e.g. \"what does this spreadsheet tell us?\", \"give me the 3 main takeaways from these numbers\", \"why did response time go up? here is the export\", \"o que esses dados dizem?\", \"tira os principais insights dessa planilha\", \"qual a causa raiz, olhando esses números?\". Not for writing a query, cleaning a dataset or building a dashboard with no question to answer, for structuring a problem that has no data yet (use frame), or for hands-on debugging of a specific bug in the current repo."
---

# Analyze

An analysis says what happened. An insight says what that means for the question being asked. This skill does both: it picks the right analysis for each question, runs it on the real data and writes the conclusion.

Second of five skills in one cycle: `frame` → **analyze** → `narrate` → `decide` → `plan`. Each works alone. `frame` hands over a problem statement and a tree of drivers or hypotheses; when there is none, state in one sentence which question each analysis answers before starting.

The method does not depend on the domain. Units, benchmarks and vocabulary come from the user's data.

Respond in the user's language.

## Flow

1. For each branch or hypothesis, write the question the analysis must answer.
2. Pick the analysis by what the question asks (table below).
3. Run it on the real data. When there is data, compute with code if a code tool is available; otherwise show the arithmetic so the user can check it. Never invent a number; when estimating, show the assumption.
4. Write the insight: fact → why it matters → what it suggests.
5. Decide how to show it (table further down). Produce the chart file only if the user asked or the deliverable is visual; otherwise, when the finding is headed for a presentation, describe the chart in one line. Charts nobody asked for cost time and do not improve the conclusion.
6. Close each question by saying what the data confirms, what it rules out and what is still missing to conclude. What the data confirms goes in the text of the insight. Hypotheses that were tested and not supported get one line each after the insights, and missing data goes in the closing lines. No separate status table.

## Part 1: Analyze

### Question → analysis

| The question is | Analysis | Usual form |
| --- | --- | --- |
| How did it change over time? | Trend | Line; stacked bars when the makeup matters too |
| Which is bigger? How much did it change between two points? | Comparison | Bars with the difference labelled; horizontal and sorted when there are many items |
| Did the makeup change? | Composition | 100% stacked bars, before and after |
| How are the values spread? What is the range? | Distribution | Histogram; box plot to compare groups |
| Do two variables move together? | Relationship | Scatter; bubble size for a third variable |
| Do a few items account for most of it? | Concentration (Pareto) | Sorted bars with a cumulative % line |
| Who moved up or down? | Ranking over time | One line per item across positions |
| What explains the gap between A and B? | Bridge | Waterfall from the first total to the second |
| Are we on target? | Actual vs. target | Bars for actual, a line or marker for target, the gap highlighted |
| Is more effort still paying off? | Marginal return | Input vs. output curve |
| What is the root cause? | 5 Whys | Chain of causes |
| We do not understand the problem as a whole yet | Six questions | What, who, when, where, why, how |
| A diagnosis other people will need to repeat | Yes/no flow | Decision flowchart |

### Notes on the ones that go wrong most often

**Concentration.** The message has the form "X% of [items] account for Y% of [measure]". Sort before accumulating.

**Bridge.** Start total, then each positive and negative change, then end total. The changes must add up exactly; if they do not, there is a missing or double-counted factor, and that is a finding in itself.

**Marginal return.** Look for two points: where each extra unit of input starts returning less than the one before, and where extra input starts reducing the output. An average hides both. The average cost of something can look stable while the cost of the last increment is climbing fast.

**Relationship.** Points lined up in a narrow band show a strong relationship. Correlation does not show cause; say what else could explain it.

**5 Whys.** Start from the problem, ask why and write down the reason, then ask why about the reason. Five is a reference, not a rule. Stop at a cause someone can act on. Every answer must be a fact that can be checked; when an answer opens into several, turn the chain into a tree.

**Six questions.** What is the problem, stated clearly; who causes it, who is affected, who can fix it; when, how long and how often; where it shows up; why, using the 5 Whys; how, both a quick containment and a lasting fix.

**Yes/no flow.** A sequence of binary questions that leads to an answer. Branch the "no" side too when it matters.

### Quality rules

- Every chart has a title, unit, period, source and a callout on the main number.
- One chart, one message.
- Keep what the data shows (fact) apart from the reading of it (interpretation).
- Small sample or incomplete data: say so.
- In a seasonal series, compare equivalent periods (peak with peak), not neighbouring ones.
- Be suspicious of patterns that are too neat. An identical value every month may be an allocation, not a measurement.
- Check the arithmetic against a total the user would recognize before reporting anything.

## Part 2: Insight

Formula: **[what the data shows] → [why it matters for the question] → [what it suggests doing or investigating]**.

Weak: "Tickets from the new form take longer." Strong: "Tickets from the new form wait 3 times longer in the queue (19h vs. 6h median, March to May) because they all land in one queue; routing them by product would remove most of the rise."

### How to show it

| The message is | Form |
| --- | --- |
| One number or one comparison | A chart beside two or three lines of takeaway |
| A list of findings | Table: finding, impact, so what |
| A sequence or a process | Phases in a row, or a timeline |
| What drives a result | Driver tree with a note per branch |
| A choice between options or groups | 2×2 matrix on the two dimensions that matter |
| A change of state | Before and after, side by side |
| An assessment of many items | Grid with high, medium, low per item |

Pick the simplest form that carries the message. A form the reader has to learn costs more than it gives.

## What to deliver

The user wants the conclusions, not the catalogue of analyses. Deliver only the insights that answer the question, in the quantity asked for (if they asked for 2 or 3, give 2 or 3). Each one has:

1. The message in one sentence.
2. The numbers behind it, with period and source.
3. Why it matters and what it suggests investigating or doing.
4. When the finding is going into a presentation, the visual in plain words, such as "bars for monthly volume with the response time line on top".

After the insights come one line per hypothesis tested and not supported, then the assumptions and the missing data, in a few lines.

Left out of the answer: this skill's internal labels ("Form:", "Message:", "Bridge"), status tables for hypotheses, explanations of how each analysis works, and sections that do not change the reading. Those names help choose; to the reader they are noise.

Produce a chart, spreadsheet or slide only if the user asks or the deliverable is visual, using the skills and tools the environment has. Prose, lists, tables and headings follow the user's preferences when they have any. If they want neutral headings, for instance, the message goes in the body and not in the heading.

When the findings need to become a recommendation for someone, continue with `narrate`.
