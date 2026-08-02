---
name: fx-market-research
description: Run deep, parallel market research on a business idea — competitors, demand evidence, bottom-up sizing, pricing/economics, regulatory and platform risk, distribution channels, and build/maintenance cost — producing a sourced evidence dossier. Use when the user says "research this market", "who are the competitors", "size this market", "is there room for X", "validate this idea", or after fx-idea-scout produces a shortlist. Fans out into independent research lanes running concurrently. Step 2 of the venture loop; gathers evidence, never decides — fx-go-nogo makes the call.
argument-hint: "[venture slug, brief path, or idea description]"
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
  - WebFetch
---

# /fx-market-research: brief → sourced evidence dossier

Step 2 of three. Gathers evidence in parallel. **Renders no verdict** — that's
`fx-go-nogo`. Resist concluding; a lane that editorializes corrupts the scorecard.

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

## Step 0 — Establish the brief (sequential, required)

Read `$VENTURE_HOME/<slug>/brief.md` and `$VENTURE_HOME/constraints.md`.

If no brief exists, create one before fanning out. **Do not skip this.** The lanes
are only parallelizable because they share a fixed definition of the segment, the
wedge, and the ACV assumption — sizing and pricing research is worthless without
them. If the user arrives with a raw idea, ask the minimum questions needed to
pin down buyer persona, wedge, and ACV, then draft the brief.

**The brief must be user-approved before fan-out.** Check for the
`Approved by user on <date>` line in its kill-criteria section. If it's absent —
because you drafted the brief here, or because scout's gate was bypassed — run
the same approval now: present the draft, read out each kill criterion with what
would trip it, and get explicit sign-off via `AskUserQuestion` before spending a
single lane. Take any edits verbatim. Research is the expensive step; the gate
costs one exchange and prevents grading an idea against criteria nobody agreed to.

## Step 1 — Fan out

Spawn one subagent per lane, **all concurrently in a single batch**. Read
`${CLAUDE_PLUGIN_ROOT}/skills/fx-market-research/references/lanes.md` for each lane's full brief and hand it to the subagent
verbatim along with the brief and constraints.

| Lane | File | Model key | Core question |
|---|---|---|---|
| Competitors | `competitors.md` | `fx-lane-researcher` | Who's already here, what do they charge, what do they miss? |
| Demand evidence | `demand.md` | `fx-lane-researcher` | Do buyers describe this pain unprompted, in public? |
| Market sizing | `sizing.md` | `fx-lane-researcher` | How many real buyers exist, counted bottom-up? |
| Economics | `economics.md` | `fx-lane-researcher` | Pricing, ACV, CAC, payback, churn shape, unit math |
| Risk | `risk.md` | `fx-risk-researcher` | Regulatory, compliance, platform/API terms, legal exposure |
| Distribution | `distribution.md` | `fx-lane-researcher` | Exactly how do you reach the first 10 buyers? |
| Build & maintain | `build.md` | `fx-lane-researcher` | Effort to v1, and the ongoing maintenance surface |

**Resolve models before spawning**, per the repo convention:

```bash
LANE_MODEL=$("${CLAUDE_PLUGIN_ROOT}/scripts/resolve-model.py" fx-lane-researcher --repo-root "$VENTURE_HOME")
RISK_MODEL=$("${CLAUDE_PLUGIN_ROOT}/scripts/resolve-model.py" fx-risk-researcher --repo-root "$VENTURE_HOME")
```

Pass the resolved alias as the `model` parameter on each Agent call. Do not
hardcode aliases here and do not rely on agent frontmatter alone — the
frontmatter is the default, `model-defaults.json` is the source of truth, and
`$VENTURE_HOME/.frxnls/model-tiers.json` lets the user retier without editing the
plugin. `--repo-root` is pinned to `$VENTURE_HOME` because this loop runs outside
any git repo, where the script's default git-root detection has nothing to find.

The risk lane is tiered to `opus` by default while the other six run `sonnet`.
That's deliberate and mirrors `rex-code-reviewer.security`: risk close-reads terms
of service and licensing for the one clause that disqualifies the business, and a
cheaper model skimming past that sentence invalidates every other lane's work.

Each writes to `$VENTURE_HOME/<slug>/research/<file>`. Lanes never read each other's
output — that's what makes them independent, and cross-contamination would let
one lane's error propagate.

Optional eighth lane when relevant: **Switching cost** (`fx-lane-researcher`) —
what a buyer must abandon, migrate, or retrain to adopt. Run it whenever incumbents hold the
system of record.

Spawn via `Agent(fx-lane-researcher)` and `Agent(fx-risk-researcher)`; the agent
definitions in `${CLAUDE_PLUGIN_ROOT}/agents/` carry the tool allowlists and the
evidence rules.

## Step 2 — Evidence discipline

Every subagent operates under these rules. Restate them in each subagent prompt.

**Tag every quantitative claim:**
- `[CITED: url]` — pulled directly from a named source
- `[DERIVED: from X × Y]` — computed, showing the inputs
- `[ASSUMED]` — a guess, stated as a guess

An untagged number is a bug. If a lane can't find a number, it writes
`UNKNOWN — <what would resolve it>` rather than inventing one. Unknowns are
useful output; fabricated precision is poison.

**Bottom-up sizing only.** Count actual entities — SEC/IAPD registrant counts,
state license rolls, association membership, Google Maps counts, LinkedIn
company filters, industry census data — then multiply by realistic ACV.
Top-down analyst TAM figures are near-useless at $5–10k MRR scale and must never
be the primary basis. Cite them only as a sanity check, if at all.

**Confidence rating.** Every section closes with High / Medium / Low plus one
line on what would raise it.

**Recency.** Note the date of any source. A 2019 pricing page is a lead, not a fact.

**Disconfirmation quota.** Each lane must actively hunt for evidence *against*
the idea and report at least one thing it found, or explicitly state that it
searched for disconfirming evidence and found none. Without this the dossier
becomes a pile of supporting evidence and the verdict is pre-cooked.

## Step 3 — Assemble

When all lanes return, write `$VENTURE_HOME/<slug>/research/_index.md`:

- One-paragraph state of the evidence
- **Conflicts between lanes**, flagged explicitly and left unresolved. Do not
  smooth them over — a sizing lane finding 4,000 buyers while distribution finds
  no way to reach them is the single most decision-relevant fact in the dossier.
- Confidence heat map by lane
- The top 5 unknowns, ranked by how much they'd move the decision
- Any pre-committed kill criterion from the brief that already appears tripped,
  flagged but **not** acted on

Do not summarize away the detail. `fx-go-nogo` reads the full lane files.

Then offer to run `fx-go-nogo`.

## Handling multiple ventures

If the user selected several candidates, run them **sequentially by venture**,
parallel within each. Seven lanes × three ventures at once produces noise and
blown context. Confirm before starting venture two — findings from the first
often change what's worth researching.

## Anti-patterns

- Reaching a conclusion. Not this skill's job.
- Top-down TAM as the headline number.
- Letting a lane return prose with no tagged figures.
- Running lanes sequentially "to build on each other" — they are designed to be
  independent; dependency is what would make this slow and biased.
- Suppressing a conflict between lanes to produce a tidier summary.
