# Decide

Lay out a decision so that whoever owns it can choose well and explain why afterwards.

Fourth of five stages: `frame` → `analyze` → `narrate` → **decide** → `plan`.

This stage structures the decision; the decider chooses. Give a recommendation when the user asks for one. A question of the form "should we X?" or "which first?" counts as asking: answer it after the comparison, not before. When the user asks only to lay out or compare options, make the trade-offs clear and stop there. A recommendation nobody asked for tends to bend the comparison toward itself.

It works the same for a company picking a vendor, a team picking an architecture or a person picking a job. Criteria and values come from the user.

Respond in the user's language.

## Flow

1. State the decision in one sentence: what is being chosen, by whom, by when.
2. Size it: how reversible is it (below)? That sets how much analysis it deserves.
3. Check the options are real alternatives, including "do nothing" and "wait" when they are viable.
4. Pick the comparison that fits (table below) and fill it in with the user's facts.
5. Deliver the comparison, what to find out before deciding, who decides and, when asked for, the recommendation.

## Numbers

Weights, scores and probabilities come from the user or from facts that can be cited. When they are missing, do not fill them in to make the method run: a made-up score looks like analysis and decides the result.

A missing value does not become an empty bracket inside the comparison either. A table the user will show to a committee has no blank cells: each cell says in words what is known ("3 months of 2 developers; cost not given"), and what has to be found out goes in its own short list under the table, with who can answer it. The comparison must be presentable as it is. For a decision tree with no probabilities, give the break-even probability (how likely the good outcome must be for the option to win) or fall back to scenarios.

## How much care it deserves

From Jeff Bezos's letters to Amazon shareholders (2015 for the two types, 2016 for the 70% rule).

- **One-way door**: consequential and hard or impossible to undo. Decide slowly and methodically, with deliberation and consultation.
- **Two-way door**: reversible. Decide fast, and let the person or team closest to the work decide. Being wrong is cheap; being slow is not.

The 2016 letter adds that most decisions should be made with around 70% of the information you wish you had; waiting for 90% usually means being slow.

The common mistake is treating a two-way door with the weight of a one-way door. Before comparing anything, ask what it would cost to undo each option. Often part of a decision is reversible and part is not; split them.

## Which comparison to use

| Situation | Use |
| --- | --- |
| A list of tasks or initiatives to put in order | **Urgent vs. important** |
| Two to four options, a quick view | **Pros and cons** |
| Options compared with rigour, on stated criteria | **Criteria scoring** |
| Outcomes are uncertain and can be given rough probabilities | **Decision tree** |
| One bet whose upside and downside both need showing | **Scenarios** |
| A hard call that involves several people | **SPADE** |

### Urgent vs. important

Attributed to Dwight Eisenhower. Two questions per item: does it have a near deadline with a real consequence, and does it move the goal?

- **Urgent and important**: do now.
- **Important, not urgent**: schedule. This is where the work that matters most usually sits, and where it gets postponed.
- **Urgent, not important**: hand off or do the minimum.
- **Neither**: drop.

### Pros and cons

1. Put the options in columns.
2. For each, list what it does well against the need and where it falls short.
3. Write the trade-off accepted by choosing each one.

Start here before reaching for anything heavier. When each side is defending its own option, ask of every option "what would have to be true for this to be the right choice?" (from A.G. Lafley and Roger Martin, *Playing to Win*). The argument turns into a list of facts to check.

### Criteria scoring

1. Make sure the options really differ.
2. Choose the criteria, and the weights if any, **before** scoring. Criteria chosen after tend to be chosen for the option someone already prefers.
3. Score each option on each criterion on one consistent scale (1 to 5, or high, medium, low).
4. With weights, compute the weighted average, with code when a code tool is available and otherwise showing the arithmetic.
5. Write one line per option: where it wins and where it lacks.

If a small change in one weight flips the winner, say so. The result is then a tie and the decision rests on that criterion.

### Decision tree

- **Decision node**: the options under review, one branch each.
- **Chance node**: the possible outcomes of each option, each with a probability. Probabilities under a node add up to 1.
- **Outcome**: the value of each end point, in one unit (money, time, whatever the user counts in).

Expected value of an option = sum of probability × value over its outcomes. Compare options by expected value and also by worst case: an option with a higher expected value and a ruinous worst case may still be the wrong one. Compute with code when a code tool is available, otherwise show the arithmetic, and say where each probability came from.

### Scenarios

1. Describe three paths: optimistic, expected and pessimistic. When there is a history in numbers, start from it and project each path.
2. Beside each, state the assumptions that produce it and the result it leads to.
3. Optionally, a probability for each.

The assumptions are the content. Three paths with no stated assumptions say nothing.

### SPADE

From Gokul Rajaram, described in First Round Review.

1. **Setting**: what exactly is being decided, why it matters, by when.
2. **People**: who is consulted (gives input), who approves (holds a veto, used rarely) and who is responsible (owns the decision and carries it out).
3. **Alternatives**: feasible, different from each other and covering the realistic range, with pros and cons.
4. **Decide**: the consulted give their view privately; the responsible person weighs the views and chooses.
5. **Explain**: the responsible person states the reasoning, takes it to the approver and gets commitment from everyone involved, including those who disagreed.

## What to deliver

The user wants the decision laid out, not an explanation of the model. Name the model at most once in the body, if that helps.

Deliver:

- the comparison in the form the chosen method produces: an ordered list, a side-by-side table on the same criteria, a tree with expected values, or roles and steps;
- what is reversible and what is not;
- what to find out before deciding, and how long that takes;
- who decides;
- the recommendation, only when asked for, after the comparison, with the fact that would change it.

In running text, go through the same dimensions for every option in the same order. Without that the comparison stops being fair, and each option gets judged on whatever favours it.

Points that change the choice go inside the comparison, not in a separate note. Assumptions and missing data go at the end, in a few lines. Cut what does not change what the user will decide.

Prose, lists and tables follow the user's preferences when they have any; short structured text is the default. If the user asks for a deck, document or spreadsheet, use the skills the environment has, with this structure as content.

Once the choice is made, the `plan` stage turns it into execution.
