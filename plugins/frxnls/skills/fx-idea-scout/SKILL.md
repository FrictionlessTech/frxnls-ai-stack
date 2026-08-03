---
name: "fx-idea-scout"
description: "Generate or frame business ideas, then cheaply screen them down to a researchable shortlist. Use when the user says \"brainstorm business ideas\", \"find gaps in X\", \"what software do Y use\", \"ideas for a niche SaaS\", \"I have an idea for...\", \"help me find a business to build\", or names a target market/vertical they want to probe for opportunity. Handles both a specific idea/category AND open-ended search. This is step 1 of the venture loop — it produces a shortlist and a brief, then hands off to fx-market-research. Screens, never researches deeply."
---

## Codex execution

Before running this workflow, read `../../references/runtime.md` and apply its
Codex-specific delegation, interaction, and model-selection rules. Those rules
override any provider-specific wording that remains below.

# /fx-idea-scout: raw intent → screened shortlist + brief

Step 1 of three:

```
fx-idea-scout ─▶ fx-market-research ─▶ fx-go-nogo ─▶ (prompt) fx-brainstorm
  (WHAT could      (EVIDENCE, in       (DECIDE)
   work)            parallel)
```

This skill is **cheap and fast**. Its job is to kill ideas before they cost real
research. The budget is work, not wall-clock: per candidate, at most 5 searches
and 8 opened sources, stopping early on a decisive kill and stopping a check as
soon as it has one supporting observation. End with 2–3 survivors.

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

Plugin assets are read from `../../templates/` and
`references/`.

## Step 0 — First-run setup and constraints

### 0a. Locate the root (first run only)

If `VENTURE_HOME` can't be resolved from the env var or `~/.frxnls/venture-home`,
this is a first run. Ask once, via a direct question to the user:

> Where should ventures live? **`~/ventures` (default)** / **another folder**

On "another folder", ask for the path. Then:

1. `mkdir -p` the root
2. Write the resolved absolute path to `~/.frxnls/venture-home` so every later
   run finds it without asking again
3. Seed `_ledger.md` from `../../templates/ledger-entry.md`
4. Tell the user the resolved path and mention they can override per-session with
   `FX_VENTURE_HOME`, or `git init` the root if they want history

Never ask about location again once the pointer file exists.

### 0b. Constraints

Read `$VENTURE_HOME/constraints.md`. If missing, interview from
`../../templates/constraints.md` via a direct question to the user: MRR
target, max ongoing maintenance hours/week, capital available, time-to-first-dollar
tolerance, verticals to avoid, unfair advantages. Write the file with today's
date in `last_reviewed`.

These are **standing** constraints — written once, reused across every venture.
Do not re-interrogate on later runs. Two exceptions:

- If `last_reviewed` is more than 6 months old, mention it once and offer a
  refresh. Circumstances change; stale constraints silently distort every score.
- At brief time (Step 4), ask whether the standing numbers apply to *this*
  venture. Per-venture deviations get recorded as overrides in `brief.md`, not
  by editing the standing file. The standing file stays the baseline so that
  ledger entries remain comparable to each other.

### 0c. Ledger

Read `$VENTURE_HOME/_ledger.md`. If anything raised this session matches a
previously screened idea, say so immediately with the original verdict, its date,
and the constraints in effect at the time — then ask what's changed. Match on
the entry's persona and wedge, not just the market: *same market + same wedge*
is dead unless its revisit trigger has fired; *same market with a new wedge or
new persona* is a legitimate new candidate — say which case this is. Do not
silently re-research dead ideas; that's the whole reason the ledger sits at the
root rather than inside a venture folder.

## Step 1 — Detect mode

**Mode A — Targeted.** User named an idea, a vertical, a job title, or a
category ("what tools does an RIA use", "something for dental practices",
"I want to build X").

**Mode B — Open.** User named only constraints ("$5–10k MRR, low maintenance",
"a niche B2B thing", "just show me ideas").

If genuinely ambiguous, ask once. Otherwise infer and state which mode you picked
in one line.

### Mode A: map the workflow, then find the gaps

Do not jump to "here are 10 product ideas". First reconstruct the target's actual
working day:

1. **Role decomposition.** Who exactly? (An RIA is not one persona — there's the
   advisor, the ops/CCO person, the client service associate. Pick one.)
2. **Tool census.** What software do they actually run? Search for stack surveys,
   vendor comparison posts, "day in the life" content, and job postings for that
   role (job posts name the tools explicitly and are the highest-signal source).
3. **Seam mapping.** Gaps live at the *seams between tools* and in the
   *spreadsheet residue* — the manual step someone does to get data from system A
   into system B. List every seam you can find.
4. **Gap candidates.** State each in this form: *when **trigger** occurs,
   **persona** must move **artifact/data** from **system A** to **system B** to
   achieve **outcome**, but currently uses **workaround**, costing
   **consequence**.* A candidate that can't fill the trigger slot — nothing
   makes the buyer act *now* — is a flag; genuine dissatisfaction with no
   urgency rarely converts to a purchase.

The "why hasn't the incumbent closed it" answer is the whole game. If you can't
answer it, the gap is probably imaginary or unprofitable — flag it as such.

### Mode B: generate against structured sources

Never freestyle. Pull candidates from these generators, aiming for breadth across
them rather than depth in one:

- **Spreadsheet archaeology** — work currently done in Excel/Airtable/Google
  Sheets by people whose job title isn't "analyst".
- **Job-posting mining** — roles that exist only to move data between systems, or
  postings that describe a manual process.
- **Boring verticals with money** — trades, compliance-heavy professions, B2B
  services, equipment-heavy industries. Low competition, high willingness to pay.
- **Mandatory work** — recurring obligations handled manually, found in
  regulatory exam manuals, insurer/lender checklists, certification
  requirements, procurement questionnaires, audit-prep guides, SOP templates,
  and filing calendars. Mandatory + recurring + manual is attractive even when
  nobody posts an angry thread about it.
- **Change-driven windows** — something recently shifted: new rules or
  enforcement, incumbent price hikes or acquisitions, APIs opening or closing,
  platform deprecations, labor shortages, new model capabilities. Change creates
  a why-now; the screen will ask for it.
- **Unbundling** — a hated all-in-one suite where one module is the real job.
- **Service-to-software** — agencies/consultants doing a repeatable thing by hand.
- **Marketplace exhaust** — Upwork/Fiverr gigs posted repeatedly for the same task.
- **Angry reviews** — 1–2 star reviews of established B2B tools on G2/Capterra.
- **Founder-fit multiplier** — cross the above against the user's unfair
  advantages from `$VENTURE_HOME/constraints.md`. Flag any candidate where they have a real
  edge; these get scoring priority.

Shape candidates against **wedge archetypes** rather than defaulting to
dashboards and copilots — reconciliation, evidence/audit-trail,
exception-management, preflight (catch errors before submission), translation
(system A's format → system B's), monitoring, coordination (replace chasing),
data-enrichment, decision-support, migration, overlay (improve an incumbent
without replacing it), compliance. Label each candidate with its archetype;
spread across several.

Produce 8–15 candidates, each as one line: *who* has *what pain*, *how often*,
what they pay for the alternative today, and — where inferable — the *purchase
trigger* that would make them act now (deadline, audit, growth, system change,
renewal) and the budget line it displaces or joins.

## Step 2 — The cheap screen

This is the highest-leverage part of the skill. For each candidate, run a fast
pass — parallel subagents, one per candidate, when there are more than four.
Spawn one built-in `default` subagent per candidate and instruct each to use `$fx-screen-scout`. Let Codex select the model from the current session policy.

Each runs its checks cheapest-kill-first, stops at the first decisive kill, and
returns:

**a. Customer-count math.** Accounts needed = MRR target ÷ plausible monthly
revenue per account (state the implied ACV = monthly × 12 alongside). State the
number. This single figure reframes everything: 4 accounts at $2k/mo and 40
at $200/mo are different businesses with different validation paths. If the
required account count exceeds what the reachable market plausibly supports,
kill it here.

**b. Demand evidence — graded on the ladder.** Search both *verbal* traces
(1–2 star reviews naming this gap, forum/subreddit/Slack complaints) and
*behavioral* traces (job posts describing the manual workaround, Upwork/Fiverr
gigs, existing paid tools however bad, consultant service menus, roles staffed
to do the work). Grade 0–5: **0 inferred · 1 verbalized · 2 worked-around ·
3 budgeted · 4 sought · 5 switched**. Survival needs **level ≥ 2 from ≥ 2
independent sources** (different domains and source types; syndicated content
counts once) — complaints alone don't clear the bar, and level 0–1 is a kill.
For confidential or regulated workflows where buyers don't complain in public,
behavioral traces are the primary signal, not a fallback. Absence of *both*
trace kinds is data, not a green field. Note the purchase trigger and budget
source when the evidence shows one.

**c. Channel sniff test.** Name one specific, concrete place these buyers
congregate — an association, conference, directory, newsletter, subreddit, trade
publication. Not "LinkedIn". If you can't name one, that's a kill: for a niche
B2B product, no channel means no business regardless of how good the product is.
Then three viability checks: does it allow vendor access, roughly how many
reachable buyers vs. the accounts-needed number, and what trust barrier a
newcomer faces.

**d. Constraint fit.** Score against `$VENTURE_HOME/constraints.md`: maintenance surface
(count brittle integrations, compliance recertification, likely support load),
plausible time to first dollar, capital needed, founder fit.

**e. Feature-or-product, and why now.** Would the obvious incumbent ship this
next quarter? Can it be cloned in a weekend now that the LLM does the hard part?
Say so plainly — but note the two rescues: an incumbent with distribution yet
weak economic incentive to serve this segment, or a job requiring
cross-incumbent neutrality, can make a "feature" a viable wedge. Then: why is
this more buildable or sellable now than three years ago? No credible answer is
a flag — long-standing gaps usually persist because they're structurally
unattractive.

**f. Adoption friction.** Time to first value, and can it run alongside the
incumbent without migrating the system of record? Heavy migration + multiple
stakeholders + slow time-to-value kills otherwise-attractive gaps.

Kill anything failing b, c, or the account math; treat a hard f failure the same
way. Be ruthless — the point of this skill is that killing is cheap here and
expensive later.

## Step 3 — Present and choose

Show a compact table: candidate | accounts needed @ $/mo | demand ladder level |
channel | why now | fit | verdict. Order by strength. Include the killed ones
with one-line reasons — the user should see what died and why.

Then use a direct question to the user to let them pick 1–3 to research. Offer "none of
these, generate more" as an option and mean it.

## Step 4 — Write the brief and hand off

For each chosen candidate, create `$VENTURE_HOME/<slug>/brief.md` from
`../../templates/brief.md`. This is the sequential step that everything downstream
depends on — the parallel research lanes are meaningless without a fixed segment
and per-account revenue assumption, so the brief must pin down:

- The **one** buyer persona (title, company size, who signs)
- The specific pain, in the buyer's own language, with a real quote if you found one
- The purchase trigger and the budget line this displaces or joins
- The wedge — narrowest useful first version
- Monthly revenue per account, implied ACV, and the accounts-needed math
- Named channel hypothesis
- **Constraint overrides** — any deviation from the standing constraints for this
  venture specifically (different MRR target, higher maintenance tolerance,
  longer runway). Ask; don't assume the baseline applies. Record the deviation
  and the reason, leaving `constraints.md` untouched.
- **Pre-committed kill criteria** — 3–5 findings that would end this, written
  *now*, before research, so they can't be rationalized away later. Be concrete:
  "more than 3 funded competitors with this exact wedge", "the incumbent's API
  terms forbid it", "sales cycle over 90 days", "requires SOC 2 before first
  customer".

Draft the brief, but **do not write it to disk yet** — go to Step 5.

## Step 5 — Approval gate (required, never skipped)

The kill criteria are the load-bearing part of this whole workflow: `fx-go-nogo`
treats a tripped criterion as an automatic No-Go. If this skill both authors them
and later grades against them, the check is circular and worthless. **The user
owns the criteria.** Get explicit sign-off before any research spends time or
tokens.

Present the drafted brief in chat — full text, not a summary — and call out the
three fields that most change the outcome downstream:

1. **The persona.** Too broad and every research lane returns mush. If it names
   more than one title, say so and push to narrow it.
2. **The money-math assumption.** The monthly revenue per account drives the
   accounts-needed math, which drives the sizing and distribution lanes. State
   where the number came from and how confident you are.
3. **The kill criteria.** Read them out individually. For each, state plainly what
   research finding would trip it.

Then use a direct question to the user:

- **Approve as drafted** — write the file, continue.
- **Edit the kill criteria** — take their replacements verbatim. Do not
  reinterpret, soften, or "improve" what they write; if a criterion seems too
  strict, say so once and then record it as written.
- **Edit the persona or the money math** — apply, then re-derive the
  accounts-needed math and re-present, since changing the per-account revenue
  changes everything below it.
- **Drop this candidate** — ledger it and move to the next.

Only after approval, write `$VENTURE_HOME/<slug>/brief.md` and add a line at the top
of the kill-criteria section: `Approved by user on <date>. Overriding any of
these requires an explicit decision recorded in decision.md.`

If the user says something like "just go" or declines to review, still show the
criteria and get a yes. This is the one gate worth being slightly annoying about
— everything downstream inherits it. Batch it across candidates if they picked
several: present all briefs together, approve in one pass.

Append every killed candidate to `$VENTURE_HOME/_ledger.md` with date and reason.

Then offer to run `fx-market-research` on the approved survivors.

## Anti-patterns

- Producing generic ideas ("an AI tool for lawyers") with no named persona.
- Treating "no competitors" as good news. It usually means no market.
- Skipping the demand-evidence step because the idea feels obviously good.
- Researching deeply here. That's the next skill's job — if you're reading a
  competitor's pricing page in detail, you've overrun this skill's scope.
- Letting a candidate through with a vague channel. "We'd do content marketing"
  is not a channel.
- Writing a brief to disk without the Step 5 approval, or treating your own
  drafted kill criteria as authoritative. They are a proposal until the user
  signs off.
