---
name: fx-go-nogo
description: Turn a research dossier into a scored go/no-go decision on a business idea — weighted scorecard against personal constraints, kill-criteria check, what-would-change-my-mind, and the single cheapest next validation experiment. Use when the user asks "should I build this", "is this worth pursuing", "go or no go", "make the call", "score this idea", or after fx-market-research completes. Step 3 of the venture loop; decides, and on a Go offers handoff to fx-brainstorm.
argument-hint: "[venture slug or research directory path]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - WebSearch
---

# /fx-go-nogo: dossier → decision

Step 3 of three. Reads the **full lane files**, not just the index — the index is
a navigation aid, and the decision-relevant detail lives in the lanes.

Run this on the main session model — no subagents, no tiering. It is the judgment
step and the one place in the loop where cost savings are false economy:
everything upstream was gathering, and this is where the call gets made.

## Paths — resolve before anything else

The venture loop is **standalone**. It does not run inside a product repo and
never writes to the current working directory. All ventures live under one root
so the ledger and constraints are never scattered or lost.

Resolution order for `VENTURE_HOME`:

1. `$FX_VENTURE_HOME` if set
2. The path in `~/.frxnls/venture-home` (single line, created at first-run setup)
3. Neither → run first-run setup (see below)

Layout under the root:

```
$VENTURE_HOME/
  constraints.md      # standing constraints, one file, overridable per venture
  _ledger.md          # every idea ever screened, append-only
  <slug>/             # one directory per venture
```

Plugin assets are read from `${CLAUDE_PLUGIN_ROOT}/templates/` and
`${CLAUDE_PLUGIN_ROOT}/skills/<skill>/references/`.

## Step 0 — Load

- `$VENTURE_HOME/<slug>/brief.md` (especially the pre-committed kill criteria)
- `$VENTURE_HOME/<slug>/research/*.md` — all of them
- `$VENTURE_HOME/constraints.md`

If research is missing or thin, say so and offer to run `fx-market-research`
rather than deciding on vapor.

## Step 1 — Kill criteria check (runs first, and can end it)

Walk the kill criteria written in the brief *before research began*. For each:
tripped, not tripped, or unknown.

**Any tripped criterion is a No-Go by default.** They were pre-committed
specifically so they couldn't be rationalized after the fact. Overriding one is
allowed but requires the user to explicitly say so and a written reason in the
decision doc — never override silently, and never quietly reinterpret a criterion
to make it survive.

## Step 2 — Score

Read `${CLAUDE_PLUGIN_ROOT}/skills/fx-go-nogo/references/scorecard.md` for the rubric. Ten dimensions, weighted by what
`$VENTURE_HOME/constraints.md` says the user actually cares about:

Demand evidence · Distribution · Economics · Competition · Regulatory & platform
risk · Build effort · **Maintenance surface** · Time to first dollar · Founder fit
· Defensibility

Rules that keep the score honest:

- **Every score cites its lane.** No score without evidence behind it.
- **Confidence-adjust.** A high score built on Low-confidence evidence is
  reported as "high but unconfirmed", not as a high score.
- **Gates, not averages.** Demand, distribution, and blocking risk are gates. A
  failure in any one of them is No-Go regardless of total — a beautiful product
  in a market you cannot reach is not a 7/10, it's a zero. Never let a strong
  average paper over a failed gate.
- **Unknowns are not zeros and not passes.** Carry them into Step 4.

## Step 3 — Verdict

One of four, stated plainly in the first line:

- **GO** — gates pass, score strong, no tripped kill criteria. Build the wedge.
- **CONDITIONAL GO** — promising, but hinges on a specific unknown. Name the one
  thing to resolve and the experiment that resolves it. This is the most common
  honest answer.
- **PIVOT** — the market is real, this wedge is wrong. Say what to shift to
  (different persona, different wedge, different pricing model) and route back to
  `fx-idea-scout` with that framing.
- **NO-GO** — kill it. Give the single clearest reason first, then supporting
  ones.

Then, always: **what would change this answer?** Two or three specific findings
that would flip the verdict. This is what makes the decision reversible when
facts change, and it's what makes a No-Go useful six months later.

Bias toward decisiveness. "More research needed" is a non-answer unless you name
exactly what research and why it's decision-changing. Do not soften a No-Go
because the user is invested — a fast, well-argued kill is the most valuable
output this whole workflow produces.

## Step 4 — Cheapest next experiment

Regardless of verdict, specify the **single cheapest test** that would most
reduce uncertainty. Cheap means days and under a few hundred dollars, not weeks.

Good: 20 cold emails to named prospects measuring reply rate; a landing page with
pricing behind an email gate; ten calls booked from a trade subreddit; buying the
incumbent for a month to find where it actually breaks; posting the workaround as
a free tool to see who bites.

Bad: "build an MVP." That's not an experiment, it's the whole bet.

State the pass/fail threshold **before** running it — e.g. "3+ of 20 replies
expressing interest, or this is dead." A test without a pre-declared threshold
just generates evidence to interpret favorably.

## Step 5 — Write and record

Write `$VENTURE_HOME/<slug>/decision.md`: verdict, date, scorecard with citations,
kill-criteria table, what-would-change-my-mind, next experiment with threshold.

Append to `$VENTURE_HOME/_ledger.md` — every venture, whatever the verdict. The ledger
is the compounding asset here: it stops re-litigating dead ideas, and the
accumulated kill reasons sharpen `fx-idea-scout`'s screening over time.

## Step 6 — Handoff

Ask via `AskUserQuestion` what happens next. Always ask — never chain
automatically.

On **NO-GO**: ledger it, offer to return to the shortlist or stop. Done.

On **PIVOT**: offer to re-run `fx-idea-scout` with the reframing.

On **GO** or **CONDITIONAL GO**, recommend the cheap experiment from Step 4
first. `fx-brainstorm` stress-tests the *how*; there's no point until the
*whether* is settled by real signal.

When the user is ready to build, the venture **leaves this loop**. It stops being
a research folder and becomes a product repo, which is where `fx-brainstorm` →
`fx-plan` → `fx-ship` take over. That repo doesn't exist yet at decision time, so
do not attempt to invoke `fx-brainstorm` from here.

Instead, offer to write `$VENTURE_HOME/<slug>/handoff.md` — a portable packet the
user drops into the new repo as `docs/brainstorms/<slug>.md`, where
`fx-brainstorm` will pick it up as its origin document. It must stand alone
without the research folder:

- The thesis in three sentences: who, what pain, what wedge
- Buyer persona and the money math (monthly revenue per account, implied ACV,
  accounts needed)
- The wedge, stated as the narrowest shippable v1
- Channel: how the first 10 customers get reached
- **Constraints that survived** — anything the risk lane found that limits the
  build (compliance prerequisites, API terms, platform dependencies), stated as
  hard requirements rather than notes
- What the scorecard scored *low* on, carried forward as the known weaknesses
  `fx-brainstorm` should attack first
- Link back to `$VENTURE_HOME/<slug>/` for full evidence

Carrying the weaknesses forward is the point. Without them the new repo starts
from a clean, optimistic story and re-discovers the problems this loop already
paid to find.

## Anti-patterns

- Averaging past a failed gate.
- Scoring on vibes rather than lane citations.
- Hedging to avoid disappointing the user.
- Recommending "build an MVP" as the next experiment.
- Overriding a tripped kill criterion without the user explicitly saying to.
