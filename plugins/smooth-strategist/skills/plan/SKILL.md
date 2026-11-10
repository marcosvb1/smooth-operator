---
name: plan
description: "Use when a direction has been chosen and it has to turn into execution: builds a plan with phases and what ends each one, workstreams with owners, milestones, the decisions still to come and when they are due, the main risks, and what to measure along the way. Fits any domain, e.g. \"turn this decision into a roadmap\", \"plan the rollout of the new process to the regional teams\", \"what do we do in the first 90 days?\", \"plan our move to the new vendor\", \"monta o plano de execução\", \"faz um roadmap disso\", \"como a gente tira isso do papel?\". Not for choosing between options (use decide), and not for planning code changes inside a coding session or breaking a ticket into tasks."
---

# Plan

Turn a chosen direction into something people can execute and check: who does what, in what order, what marks progress and what would show the plan is wrong.

Last of five skills in one cycle: `frame` → `analyze` → `narrate` → `decide` → **plan**, then back to `frame` with what execution taught. Each works alone. If the direction is not settled yet, use `decide` first; a plan for an open question hides the question.

The parts are the same for a product launch, a system migration, a research project or moving house. Scale them to the size of the job: a two-week effort needs a list, not a programme.

Respond in the user's language.

## Flow

1. Write the outcome: what will be true when this is done, and how anyone will know.
2. Work backward from the outcome to the phases.
3. Split the work into workstreams and name an owner for each.
4. Place the milestones and the decisions still to be made, and mark what depends on what.
5. Run a pre-mortem and add what it turns up.
6. Say what will be measured and when the plan gets revisited.

## The parts of a plan

### Outcome and measure

One sentence for the end state and one measure that shows it was reached. Take both from the problem statement or the decision when they exist. If the target or the date was not given, leave a slot ("by [date]") rather than inventing one; a made-up date in a plan gets read as a promise.

### Phases

Group the work into 3 to 5 phases. Each phase has:

- a **theme** in a few words, so that the themes read in order already tell the sequence;
- an **exit condition**: what must be true to move on. "Design done" is not a condition; "the three teams signed off the interface" is.

A common shape for projects inside an organization, as an example and not a template: prepare (settle the details needed to start building) → mobilize (people, roles, way of working) → build → release → hand over to normal operation.

### Workstreams and owners

A workstream is a line of work that can move mostly on its own. Each has one named owner, a person and not a team. Work with two owners has none.

Keep the same workstreams across all phases so the plan reads as a grid: workstreams in rows, phases or time blocks in columns, the main activities in the cells.

### Milestones

A milestone is an event that can be checked on a date: something shipped, signed, measured. Put them where a workstream hands something to another, and at each phase exit. Few and real beats many and vague.

### Decisions still to come

Most plans stall on decisions, not on work. Starting from the end and moving backward, list the decisions that have to be made, who makes each and the date by which each is needed so the work after it can start. Show them on the same timeline as the milestones.

### Dependencies and risks

Mark what cannot start until something else finishes, and which of those sit on the longest chain, since a slip there moves the end date.

For risks, run a **pre-mortem** (from Gary Klein): assume the end date has arrived and the plan failed, then write the most likely reasons. For the two or three that matter most, add either an action that reduces the chance or an early sign to watch for. A long risk register nobody reads is worth less than three risks with an owner each.

### Communication

When the plan changes how other people work, say who needs to know what and when: before it starts, at each release, after it lands. More communication around the moments of change, less in between.

### What to measure

Say what will be tracked during execution, how often, and what result would mean the plan needs to change. Those results feed the next round, starting again from the problem statement.

## Checking the plan

- The outcome can be verified by someone outside the team.
- Every workstream has one owner, or a flagged slot for one.
- Every phase has an exit condition that can be checked.
- No milestone depends on a decision that is not on the plan.
- The first stretch is concrete enough to start now. Later phases may be coarser.

## What to deliver

The user wants the plan filled in, not a description of what a plan contains. The checks do not become sections.

Default layout:

1. Outcome and measure, in two lines.
2. The grid: workstreams with owners in rows, phases in columns, main activities in the cells, milestones marked and the longest chain of dependencies pointed out.
3. Decisions still to come: decision, who, by when.
4. The two or three risks that matter, each with its action or early sign.
5. Who needs to be told what and when, if the plan changes how other people work.
6. What will be measured and when the plan is revisited.
7. Assumptions and gaps the user has to fill (owners not named, dates not set), one line each.

For a small job, collapse this to the outcome, an ordered list of steps with owner and date, and one line on what to watch.

Leave an owner or a date blank and flagged rather than guessing. Cut what does not change what someone will do.

Tables, lists and prose follow the user's preferences when they have any. If the user asks for a Gantt chart, a spreadsheet or a deck, use the skills and tools the environment has, with this structure as content.
