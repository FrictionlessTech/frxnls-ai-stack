---
name: fx-triage
description:
  'Scan the project''s work sources, rank what''s actionable, and surface a
  triage digest — the front of the frxnls loop. Use when asked to "triage",
  "what should I work on", "what needs attention", "morning triage", "check for
  new work", or when run as a scheduled routine. Reads GitHub (issues/PRs/CI)
  first; enriches from Sentry/Linear/etc. when those MCP connectors are present.
  Discovers and ranks — it never implements; it hands green-lit items to fx-ship
  / fx-debug.'
argument-hint:
  "[optional: source filter, label, or focus — e.g. 'bugs', 'label:ready', 'PRs
  only']"
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
  - AskUserQuestion
  - Agent
  - Skill
  - WebFetch
---

# /fx-triage: discover work → rank it → surface it (the front of the loop)

The **trigger** for the frxnls delivery pipeline. Where `fx-ship` is the
assembly line and `fx-compound` closes the loop on the maker side, this skill is
what _starts_ a run without you having to be the one who prompts: it scans your
work sources, classifies and ranks what's actionable, cross-references what's
already known, and **surfaces a digest** for you to green-light. It is the
"automation that discovers and triages work, surfacing findings for human
review" — deliberately read-only on the work itself.

```
sources (gh + optional MCP) ─▶ classify + rank ─▶ cross-ref docs/solutions/ ─▶ DIGEST ─▶ [you green-light] ─▶ fx-ship / fx-debug
```

<focus> #$ARGUMENTS </focus>

**It discovers and ranks; it does not implement.** Triage that silently kicks
off work is the failure mode the loop is meant to avoid. This skill stops at the
digest and the hand-off prompt — _you_ (or, interactively, a confirmed
selection) decide what enters the pipeline. The human gate at the front mirrors
the one `fx-ship` keeps before merge.

## Design constraints (why it's built this way)

This skill is meant to run **unattended in a cloud routine** as well as
interactively, so it is built to survive a bare environment:

- **`gh`-first.** GitHub via the `gh` CLI is the backbone — it's present in any
  repo clone, local or cloud, no MCP required. Everything essential works from
  `gh` alone.
- **MCP sources are optional enrichment.** Cloud routines get MCP connectors
  configured _per routine_, not inherited from your session, so a scheduled run
  may have none. Treat Sentry / Linear / PostHog / Slack as enrichment: probe
  for the tool, use it if present, and **note its absence in the digest**
  ("Sentry not checked — connector unavailable") rather than failing the run.
- **No silent truncation.** If you cap the scan (top-N issues, one label, last N
  days), say so in the digest. A triage that quietly drops items reads as "all
  clear" when it isn't.

## Modes

| Mode                      | When                                              | Behavior                                                                                                                                                                         |
| ------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Interactive** (default) | You run `/frxnls:fx-triage` in a session          | Produce the digest, then offer to hand selected items to `fx-ship` / `fx-debug` via `AskUserQuestion`.                                                                           |
| **Headless**              | Scheduled routine, or `mode:headless` in the args | No questions. Produce the digest, write it to `docs/triage/<date>-triage.md`, and surface it to whatever reporting connector is configured (see **Surface**). Never starts work. |

Detect headless from the args (`mode:headless`) or from running as a scheduled
task (a `<scheduled-task …>` tag at the top of the conversation). When unsure,
default to interactive.

## Sources (probe each; skip-and-note any that are unavailable)

**GitHub — always, via `gh`:**

- **Open issues**, ranked. Favor actionable labels (`bug`, `ready`, `triage`,
  `p0/p1`); call out unlabeled/unassigned issues as "needs triage decision".
  `gh issue list --state open --json number,title,labels,assignees,updatedAt,comments --limit 50`
- **PRs needing attention**: review requested, failing checks, merge conflicts,
  or stale (no update in N days).
  `gh pr list --state open --json number,title,reviewDecision,statusCheckRollup,updatedAt,isDraft`
- **CI health on the default branch**: recent failing runs.
  `gh run list --branch "$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)" --status failure --limit 10`
- **Security**: open Dependabot / code-scanning alerts if accessible
  (`gh api repos/{owner}/{repo}/dependabot/alerts` — may 403 without perms; note
  if so).

**docs/solutions/ — always, local:** cross-reference each candidate against the
learnings store. If an issue matches a documented root cause, the digest should
say so — that item is a _lookup_, not a fresh investigation (the `fx-compound` ↔
`fx-debug` payoff). Quick pass: `grep`/`Glob` over `docs/solutions/` +
`CONCEPTS.md`. For a non-trivial match, dispatch the **`fx-learnings-research`**
agent.

**Resolve the model before dispatch.** Resolve via `python3 "<skill-base>/../../scripts/resolve-model.py" <agent-name>` (skills know their injected base directory), pass the result as the Agent tool's `model` parameter, and mention it in the dispatch announcement. If the resolver script is missing or errors, omit `model` — the agent's frontmatter default applies.

**Optional MCP enrichment (use if the tool resolves; otherwise note absent):**

- **Sentry** (`mcp__*Sentry*__search_issues` / `search_events`): unresolved or
  spiking errors, ranked by event count / users affected. Strong signal for
  what's actually breaking in prod.
- **PostHog** (`mcp__*PostHog*`): only if a specific metric/alert is the triage
  focus.

Load any MCP tool's schema via `ToolSearch` before calling it. If `ToolSearch`
returns no match, the connector isn't available in this environment — record
that and move on.

## Workflow

1. **Scope.** Read `<focus>` for a filter (a label, "bugs", "PRs only", a source
   name). No focus → full scan across all available sources.
2. **Gather.** Probe each source above. Collect raw candidates with their
   source, link, timestamp, and any severity signal (label, Sentry event count,
   CI failure).
3. **Cross-reference `docs/solutions/`.** Tag each candidate as `known`
   (documented fix exists — link it), `near-miss`, or `new`.
4. **Rank.** Order by a simple, explainable priority — don't overthink it:
   - **P0** — breaking prod now (spiking Sentry error, failing CI on default
     branch, security alert).
   - **P1** — blocks users or a release (labeled `bug`/`p1`, PR that's been
     approved but not merged, review-requested PR going stale).
   - **P2** — ready, well-scoped work (issue labeled `ready` with a clear spec).
   - **P3** — needs a human decision before it can enter the pipeline
     (unlabeled, ambiguous, or design-level). State the _why_ for each ranking —
     the digest must be skimmable and defensible.
5. **Suggest a route per item** (a recommendation, not an action):
   - clear bug / error / failing test → **`fx-debug`**
   - defined plan or ready, well-scoped issue → **`fx-ship`**
   - rough idea / unclear requirements → **`fx-plan`** (or `fx-brainstorm`
     first)
   - PR needing review → **`rex-code-reviewer`** / merge decision
   - ambiguous → **needs your decision** (no route)
6. **Emit the digest** (format below).
7. **Hand off** — _interactive only_. Via `AskUserQuestion`, offer to start the
   top item(s) on their suggested route. On confirmation, invoke the target
   skill (`fx-ship` / `fx-debug` / `fx-plan`) via the `Skill` tool. **Confirm
   before starting anything** — never auto-enter the pipeline. _Headless:_ skip
   this step entirely.

## Digest format

```
# Triage — <date>  ·  <repo>  ·  <N items>
_Sources scanned: GitHub ✓ · docs/solutions ✓ · Sentry ✗ (no connector) · Linear ✗_

## P0 — breaking now
- [ ] **#123 — checkout 500s on submit** · `bug` · Sentry: 412 events / 88 users
      → fx-debug · ⚠ NEW (no docs/solutions match)
- [ ] **CI failing on main** — `test_payments` flaking since 2 days → fx-debug

## P1 — blocks users / release
- [ ] **PR #98 — reservation reminders** · approved, not merged, 3 days stale → merge decision
- [ ] **#117 — token refresh race** · `bug` → fx-debug · ✓ KNOWN: docs/solutions/auth/token-refresh-race.md

## P2 — ready work
- [ ] **#120 — add CSV export** · `ready`, scoped → fx-ship

## P3 — needs your decision
- [ ] **#131 — "rethink onboarding"** · unlabeled, no spec → fx-plan / fx-brainstorm

_Capped at 50 issues / 10 PRs. Nothing dropped silently below that._
```

The boxes are intentional: the digest doubles as a checklist you can act on
directly.

## Surface (close the loop back to a human)

A triage nobody sees is wasted. After emitting the digest:

- **Interactive:** the digest is the message — it's already in front of you.
  Optionally also write it to `docs/triage/<date>-triage.md` if asked.
- **Headless:** **always** write `docs/triage/<date>-triage.md` (the durable
  record), and push it to a reporting connector if one is configured:
  - **Slack** (`mcp__*Slack*`) — post the digest (or its P0/P1 summary) to a
    channel.
  - **Linear / GitHub issue** — optionally open/update a single rolling "Triage"
    issue.
  - If no reporting connector resolves, the written file + the routine's own run
    output _are_ the report — say so, don't fail.

Probe the connector via `ToolSearch` exactly as for the source MCPs; absence is
a noted line in the digest, never an error.

## Compose with

- [`fx-ship`](../fx-ship/SKILL.md) — where ready, defined items go (P1/P2). The
  pipeline this skill feeds.
- [`fx-debug`](../fx-debug/SKILL.md) — where bugs / failing CI / errors go
  (P0/P1).
- [`fx-plan`](../fx-plan/SKILL.md) /
  [`fx-brainstorm`](../fx-brainstorm/SKILL.md) — for P3 items that need shaping
  before they can ship.
- `frxnls:fx-learnings-research` — cross-references candidates against
  `docs/solutions/` (step 3).
- `frxnls:rex-code-reviewer` — for PRs surfaced as needing review.

## Run it on a schedule (the automation layer)

This skill is the behavior; a schedule is a thin trigger that invokes it. Build
order: test interactively first (`/frxnls:fx-triage`), then wrap it.

- **Local cron** (your machine, while a session is open): durable `CronCreate` /
  `/schedule` — your user-scope plugins are already present, nothing to
  provision.
- **Cloud routine** (unattended, machine off): runs from a fresh repo clone with
  **no** user-scope plugins. Make `frxnls` available to it by declaring the
  plugin + marketplace in the **target repo's** `.claude/settings.json`
  (`enabledPlugins` + `extraKnownMarketplaces` pointing at the public
  `frxnls-ai-stack` marketplace), or by vendoring this skill into the repo's
  `.claude/skills/`. Configure the routine's MCP connectors (Sentry/Slack) on
  the routine itself (see next) — the `gh`-first design means triage still
  produces a useful digest even with none.

### Configuring connectors for the scheduled run

Sentry, Slack, and Linear are **claude.ai OAuth connectors**, so they're wired
up in the web UI, not a file — two steps:

1. **Connect the service once (account level).** At
   **claude.ai/customize/connectors**, add and authorize Sentry / Slack. This
   runs the browser OAuth flow once; the tokens are stored on your **claude.ai
   account**, which is what lets an unattended routine reuse them with no live
   login at fire time.
2. **Include them per routine.** At **claude.ai/code/routines** → new/edit
   routine, scroll to the **Connectors** section: all connected connectors are
   included by default — keep Sentry/Slack and remove the rest to limit the
   tool surface.

Notes that matter for triage:

- The routine **acts as your identity** and runs autonomously — no approval
  prompts mid-run (that's the difference from an interactive cloud session,
  where you'd authorize via `/mcp` live). Connector traffic is proxied through
  Anthropic, so you don't add their hosts to the environment's Allowed domains.
- This path is for **remote OAuth connectors only**. A local stdio MCP server
  (e.g. one added with `claude mcp add`) isn't on your claude.ai account and
  won't appear in that list — declare those in a committed `.mcp.json`, and only
  if the command can run in the cloud VM. Sentry/Slack don't hit this.
- **No secrets store yet.** Routine environment variables exist but are visible
  to anyone who can edit the environment — fine for non-sensitive config, not
  for raw API keys. OAuth connectors sidestep this, which is why they're the
  right mechanism here.
- Routines are a **research preview** — the exact form layout may shift, but the
  model (connect at `/customize/connectors`, include per-routine) is current.

## Auto-invoke

Trigger phrases: "triage", "what should I work on", "what needs attention",
"morning triage", "check for new work", "anything broken". Manual override:
`/frxnls:fx-triage [focus]`. Runs headless automatically when invoked as a
scheduled task.
