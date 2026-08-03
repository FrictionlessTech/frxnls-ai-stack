---
name: fx-idea-scout
description: Generate or frame business ideas, then cheaply screen them down to a researchable shortlist. Use when the user says "brainstorm business ideas", "find gaps in X", "what software do Y use", "ideas for a niche SaaS", "I have an idea for...", "help me find a business to build", or names a target market/vertical they want to probe for opportunity. Handles both a specific idea/category AND open-ended search. This is step 1 of the venture loop — it produces a shortlist and a brief, then hands off to fx-market-research. Screens, never researches deeply.
---

# fx-idea-scout: raw intent → screened shortlist + brief

Step 1 of three:

```
fx-idea-scout ─▶ fx-market-research ─▶ fx-go-nogo ─▶ (handoff packet)
  (WHAT could      (EVIDENCE, in       (DECIDE)
   work)            parallel lanes)
```

This skill is **cheap and fast**. Its job is to kill ideas before they cost real
research. Target: under 15 minutes of tool time, ending in 2–3 survivors.

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

Bundle assets (templates, lane briefs, scorecard) live under `EXT_HOME`:

1. `$FX_EXT_HOME` if set
2. `~/.gemini/extensions/frxnls-venture` — Gemini CLI extension
3. `~/.gemini/config/plugins/frxnls-venture` — Antigravity global plugin
4. `.agents/plugins/frxnls-venture` — Antigravity workspace plugin

Resolve both with one shell call before anything else:

```bash
EXT_HOME="$FX_EXT_HOME"
for c in "$HOME/.gemini/extensions/frxnls-venture" \
         "$HOME/.gemini/config/plugins/frxnls-venture" \
         ".agents/plugins/frxnls-venture"; do
  [ -n "$EXT_HOME" ] && break
  [ -d "$c" ] && EXT_HOME="$c"
done
VENTURE_HOME="${FX_VENTURE_HOME:-$(cat ~/.frxnls/venture-home 2>/dev/null)}"
echo "EXT_HOME=${EXT_HOME:-UNSET}"; echo "VENTURE_HOME=${VENTURE_HOME:-UNSET}"
ls "$EXT_HOME/skills/fx-idea-scout/templates" 2>/dev/null || echo "TEMPLATES MISSING"
```

If `VENTURE_HOME=UNSET`, this is a first run — go to Step 0a. If
`TEMPLATES MISSING`, tell the user the extension is not installed where expected
and ask for the path rather than guessing or inventing template content.

## Step 0 — First-run setup and constraints

### 0a. Locate the root (first run only)

If `VENTURE_HOME` can't be resolved, ask once via `ask_user`:

> Where should ventures live? **`~/ventures` (default)** / **another folder**

On "another folder", ask for the path with a `text` type question. Then:

1. `mkdir -p` the root
2. Write the resolved absolute path to `~/.frxnls/venture-home` so every later
   run finds it without asking again
3. Seed `_ledger.md` from `$EXT_HOME/skills/fx-idea-scout/templates/ledger-entry.md`
4. Tell the user the resolved path and mention they can override per-session with
   `FX_VENTURE_HOME`, or `git init` the root if they want history

Never ask about location again once the pointer file exists.

### 0b. Constraints

Read `$VENTURE_HOME/constraints.md`. If missing, interview from
`$EXT_HOME/skills/fx-idea-scout/templates/constraints.md` via `ask_user`: MRR
target, max ongoing maintenance hours/week, capital available, time-to-first-dollar
tolerance, verticals to avoid, unfair advantages. `ask_user` takes up to four
questions per call, so batch them across two or three calls rather than
interrogating one field at a time. Write the file with today's date in
`last_reviewed`.

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
and the constraints in effect at the time — then ask what's changed. Do not
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
2. **Tool census.** What software do they actually run? Use `google_web_search`
   for stack surveys, vendor comparison posts, "day in the life" content, and job
   postings for that role (job posts name the tools explicitly and are the
   highest-signal source).
3. **Seam mapping.** Gaps live at the *seams between tools* and in the
   *spreadsheet residue* — the manual step someone does to get data from system A
   into system B. List every seam you can find.
4. **Gap candidates.** For each seam: who feels the pain, how often, what they do
   today instead, why the incumbent hasn't closed it.

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
- **Regulatory change** — new rules create a mandatory-purchase window.
- **Unbundling** — a hated all-in-one suite where one module is the real job.
- **Service-to-software** — agencies/consultants doing a repeatable thing by hand.
- **Marketplace exhaust** — Upwork/Fiverr gigs posted repeatedly for the same task.
- **Angry reviews** — 1–2 star reviews of established B2B tools on G2/Capterra.
- **Founder-fit multiplier** — cross the above against the user's unfair
  advantages from `$VENTURE_HOME/constraints.md`. Flag any candidate where they
  have a real edge; these get scoring priority.

Produce 8–15 candidates, each as one line: *who* has *what pain*, *how often*,
and what they pay for the alternative today.

## Step 2 — The cheap screen

This is the highest-leverage part of the skill. For each candidate, run a fast
pass. When there are more than four candidates, delegate to the **`fx-screen-scout`**
subagent — it is exposed as a tool of that name. Request every candidate's screen
in a single turn so the runtime can overlap them; if it serializes, accept that,
but never let one scout read another's output.

This step is broad, shallow retrieval — the whole point of the screen is that
it's cheap. Cost is held down by `max_turns: 12` in
`$EXT_HOME/agents/fx-screen-scout.md`, not by a pinned model; keep the scouts
shallow rather than expecting the runtime to make them cheap for you.

Each returns:

**a. Customer-count math.** MRR target ÷ plausible ACV = accounts needed. State
the number. This single figure reframes everything: 4 accounts at $2k/mo and 40
at $200/mo are different businesses with different validation paths. If the
required account count exceeds what the reachable market plausibly supports,
kill it here.

**b. Demand evidence — is the pain publicly verbalized?** Look for people
complaining about this *in their own words*, unprompted:
- 1–2 star reviews of incumbents naming this specific gap
- forum/subreddit/Slack-community complaints
- job posts describing the manual workaround
- Upwork/Fiverr gigs for the task
- existing paid tools, however bad

Grade the evidence: **observed** (found real complaints, quote them),
**adjacent** (people complain about neighbors of this problem), or
**speculated** (you're inferring it and found nothing). *Speculated is a kill by
default.* The absence of anyone complaining is data, not a green field.

**c. Channel sniff test.** Name one specific, concrete place these buyers
congregate — an association, conference, directory, newsletter, subreddit, trade
publication. Not "LinkedIn". If you can't name one, that's a kill: for a niche
B2B product, no channel means no business regardless of how good the product is.

**d. Constraint fit.** Score against `$VENTURE_HOME/constraints.md`: maintenance
surface (count brittle integrations, compliance recertification, likely support
load), plausible time to first dollar, capital needed, founder fit.

**e. Feature-or-product.** Would the obvious incumbent ship this next quarter?
Can it be cloned in a weekend now that the LLM does the hard part? Say so plainly.

Kill anything failing b, c, or the account math. Be ruthless — the point of this
skill is that killing is cheap here and expensive later.

## Step 3 — Present and choose

Show a compact table: candidate | accounts needed @ ACV | demand evidence grade |
channel | fit | verdict. Order by strength. Include the killed ones with
one-line reasons — the user should see what died and why.

Then use `ask_user` (type `choice`, `multiSelect: true`) to let them pick 1–3 to
research. Offer "none of these, generate more" as an option and mean it.

## Step 4 — Write the brief and hand off

For each chosen candidate, create `$VENTURE_HOME/<slug>/brief.md` from
`$EXT_HOME/skills/fx-idea-scout/templates/brief.md`. This is the sequential step
that everything downstream depends on — the parallel research lanes are
meaningless without a fixed segment and ACV assumption, so the brief must pin
down:

- The **one** buyer persona (title, company size, who signs)
- The specific pain, in the buyer's own language, with a real quote if you found one
- The wedge — narrowest useful first version
- ACV assumption and accounts-needed math
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
2. **The ACV assumption.** This drives the accounts-needed math, which drives the
   sizing and distribution lanes. State where the number came from and how
   confident you are.
3. **The kill criteria.** Read them out individually. For each, state plainly what
   research finding would trip it.

Then use `ask_user`:

- **Approve as drafted** — write the file, continue.
- **Edit the kill criteria** — take their replacements verbatim. Do not
  reinterpret, soften, or "improve" what they write; if a criterion seems too
  strict, say so once and then record it as written.
- **Edit the persona or ACV** — apply, then re-derive the accounts-needed math
  and re-present, since changing ACV changes everything below it.
- **Drop this candidate** — ledger it and move to the next.

Only after approval, write `$VENTURE_HOME/<slug>/brief.md` and add a line at the
top of the kill-criteria section: `Approved by user on <date>. Overriding any of
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
