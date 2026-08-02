# Changelog

All notable changes to the **frxnls** plugin are recorded here. Versions track
`frxnls/.claude-plugin/plugin.json`. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
[Semantic Versioning](https://semver.org/) — while on `0.x`, anything may change
between minor versions.

## [Unreleased]

_Nothing yet._

## [0.20.0] — 2026-08-02

### Added
- **Venture discovery loop — `fx-idea-scout` → `fx-market-research` → `fx-go-nogo`.** A
  three-skill research loop that runs *upstream* of the delivery pipeline: deciding
  whether an idea is worth building, before `fx-brainstorm` starts on what and how.
  `fx-idea-scout` generates candidates (open mode) or frames the one you brought
  (targeted mode) and cheaply screens them — accounts-needed math, publicly verbalized
  demand graded observed/adjacent/speculated, a named channel, constraint fit — down to a
  2–3 idea shortlist. `fx-market-research` fans out seven independent lanes concurrently
  (competitors, demand, bottom-up sizing, economics, risk, distribution, build/maintenance,
  plus an optional switching-cost lane) into a sourced evidence dossier, and renders no
  verdict. `fx-go-nogo` reads the full lane files and returns GO / CONDITIONAL GO / PIVOT /
  NO-GO against a ten-dimension weighted scorecard, always naming what would change the
  answer and the single cheapest next experiment with a pre-declared pass threshold.
  The loop is deliberately **standalone** — it runs outside any product repo, since the
  repo doesn't exist yet at decision time, and never writes to the working directory.
  First run asks where ventures should live (default `~/ventures`), persists the answer to
  `~/.frxnls/venture-home`, and resolves `$FX_VENTURE_HOME` ahead of it. `constraints.md`
  and `_ledger.md` sit at that root so the ledger stays comparable across ventures and
  years; per-venture deviations are recorded as overrides in each `brief.md` rather than by
  editing the standing file. Three design constraints keep the verdict honest: kill
  criteria are written into the brief *before* research begins and signed off by the user
  at an explicit gate (so `fx-go-nogo` isn't grading against criteria it authored itself);
  demand, distribution, and blocking risk are **gates rather than score components** —
  failing one is a No-Go regardless of weighted total; and every quantitative claim carries
  a `[CITED]`/`[DERIVED]`/`[ASSUMED]` tag, with sizing bottom-up from real registries only
  and each lane required to report disconfirming evidence or state that it searched and
  found none. On a Go, `fx-go-nogo` emits a portable `handoff.md` rather than invoking
  `fx-brainstorm` — the user drops it into the new repo as `docs/brainstorms/<slug>.md`.
  It carries the scorecard's low scores forward as known weaknesses, so the new repo
  doesn't restart from the clean story and rediscover what this loop already paid to find.
  Ships with `frxnls/templates/` scaffolds (`brief.md`, `constraints.md`,
  `ledger-entry.md`) and per-skill references (`fx-market-research/references/lanes.md`,
  `fx-go-nogo/references/scorecard.md`).
- **Three research agents wired to the existing resolver** — `fx-lane-researcher`
  (sonnet), `fx-risk-researcher` (opus), `fx-screen-scout` (haiku), with matching
  `model-defaults.json` keys. Risk gets the top tier on the same reasoning as
  `rex-code-reviewer.security`: it close-reads terms of service and licensing for the one
  clause that disqualifies a business, and a cheaper model skimming past that sentence
  invalidates every other lane's work. The venture skills resolve models through
  `resolve-model.py` with `--repo-root` pinned to `$VENTURE_HOME`, since the loop runs
  outside a git repo where the script's default root detection has nothing to find — which
  also makes `$VENTURE_HOME/.frxnls/model-tiers.json` the override file for these three
  keys. `fx-go-nogo` is intentionally unkeyed and runs on the session model: it's the
  judgment step, and the one place in the loop where cheaping out is false economy.
  `resolve-model.py --check` passes; `test_resolve_model.py` stays green at 15 tests.

### Changed
- **README** — documents the venture loop (flow diagram, `$VENTURE_HOME` layout and
  resolution order, the three honesty mechanisms, the handoff into a new repo), adds the
  six new components to the layout tree and component table, extends the model-configuration
  key table to all 13 keys, and reframes `fx-triage` as the front of the *delivery
  pipeline* now that the venture loop sits upstream of it. Also backfills `fx-debug`, which
  shipped in 0.8.0 but was never added to the tree or the table.
- `.gitignore` — ignore `.claude/`.

## [0.19.0] — 2026-07-20

### Added
- **Install-site model configuration.** Every model assignment the plugin makes — the
  five agent frontmatters and Rex's five finder perspectives — now resolves from one
  canonical map (`frxnls/model-defaults.json`) through a deterministic, never-failing
  python3 resolver (`frxnls/scripts/resolve-model.py`), overridable per install site via
  `.frxnls/model-tiers.json`. Wired at every frxnls spawn site: Rex's finder fan-out
  (with resolved models in the summary's Coverage `Models:` line), `fx-plan`,
  `fx-compound`, `fx-debug`, `fx-triage`'s research-agent dispatches, and `fx-ship`'s
  interactive and batch (`ship-batch.workflow.js`) implementer spawns. A missing,
  unreadable, or malformed config — or an unknown key/value — degrades silently to the
  repo default; resolution never blocks a spawn. `resolve-model.py --check` lints agent
  frontmatter against the defaults map. Two example configs
  (`examples/model-tiers.high-stakes.json`, `examples/model-tiers.side-project.json`)
  and a README "Model configuration" section document the key table and fallback
  contract. `fx-security-audit`'s ad-hoc verifier sub-task intentionally has no
  canonical key and continues to inherit the session default. The bare
  `rex-code-reviewer` key is lint-only (`--check` only) — no flow in this repo
  resolves it at spawn time before invoking Rex itself. Rex's fan-out dials
  (partitions/rolls) remain **not** configurable — models only.

### Fixed
- **`resolve-model.py`** — a non-string `.frxnls/model-tiers.json` override value
  (e.g. a list or object) no longer crashes resolution with an unhandled
  `TypeError`; it's now treated the same as any other invalid alias (falls back
  to the default, warns). Warnings about invalid/unknown config content no
  longer echo attacker-controlled config text verbatim (fixed-vocabulary
  messages only) — closes an indirect prompt-injection path where a PR's own
  `.frxnls/model-tiers.json` could otherwise land arbitrary text in Rex's
  review summary. `--check` now also flags an `agents/*.md` file that has a
  frontmatter `model:` but no matching `model-defaults.json` key, and tolerates
  a trailing `# comment` after the frontmatter's `model:` value.
- **`ship-batch.workflow.js`** — validates a resolved model against the known
  aliases before passing it to `agent()`'s `model:` option; an invalid value is
  omitted rather than passed through.

## [0.18.0] — 2026-07-17

### Changed
- **`fx-ship`** — reverted the v0.17.0 auto-run of `frxnls:rex-code-reviewer` in the
  review step (5). The phantom "won't self-approve my own PR's gate / Awaiting local Rex"
  behavior is now handled another way, so forcing a local Rex pass in fx-ship only
  duplicated the effort. Step 5 goes back to describing the local pass as optional —
  Rex CI still reviews each PR on open.

## [0.17.0] — 2026-07-15

### Changed
- **`fx-ship`** — the review step (5) now **runs `frxnls:rex-code-reviewer` on each PR
  automatically** as a normal step, instead of describing it as an optional parenthetical
  pass. The orchestrator was conflating *running Rex* (read-only analysis that emits an
  `APPROVE`/`REQUEST CHANGES` verdict) with *approving/merging its own PR* — so it would
  refuse with an invented "won't self-approve my own PR's gate / Awaiting local Rex" and
  leave the review perpetually pending. Step 5 now states plainly that generating the
  review is analysis for the human, not self-approval and not a merge; there is no
  local-Rex gate to wait on; and the **only** human gate remains the merge (step 9).

## [0.16.0] — 2026-07-06

### Changed
- **`rex-code-reviewer`** — partitioned ensemble for the three variance-driven finders,
  to front-load recall so a single review stops dripping findings across multiple runs.
  On a **full** review, correctness / security / data-integrity now fan out into
  partitioned passes (each aimed at a different failure class); simplicity and
  documentation stay single-pass. Stage 3 gains a fan-out table with two dials —
  partitions (breadth) and rolls/partition (depth), full-review passes = partitions ×
  rolls (defaults: security 2×1, correctness 3×1, data-integrity 2×1). Stage 4 unions
  all passes and extends cross-reviewer promotion to cross-pass agreement, so a
  corroborated confidence-50 finding is promoted rather than lowering the gate.
  Incremental re-runs stay single-pass over the delta, so the ensemble cost is paid
  once on the first full review.

## [0.15.0] — 2026-07-06

### Changed
- **`rex-code-reviewer`** — incremental-by-default reviews with stateful reconciliation
  (CodeRabbit/Gemini model). The first review is full; every re-run compares the
  last-reviewed sha to HEAD, reviews only the new commits plus the blast radius of
  changed symbols, and reconciles prior findings — resolving fixed ones, carrying
  still-open ones — instead of re-scanning the whole PR. Stage 1 determines mode via the
  GitHub compare API (ahead → incremental; identical → no-op; diverged/behind → full
  fallback); Stage 4 re-checks prior open findings and computes the verdict over new +
  carried-forward; Stage 5 persists per-PR state in a hidden `rex-state` block inside the
  idempotent summary comment (Rex's only memory) and adds a Resolved section.

## [0.14.0] — 2026-07-04

### Changed
- **Sonnet agents** — reverted the v0.13.0 pin: `plan-implementer`,
  `plan-implementer-backend`, `fx-repo-research`, `fx-learnings-research`,
  `rex-code-reviewer`, and rex's Sonnet subagent dispatch prose (Subagents 1, 4, 5) go
  back to the rolling `sonnet` alias as the default.

## [0.13.0] — 2026-07-02

### Changed
- **Sonnet agents** — pinned the rolling `sonnet` alias to the explicit
  `claude-sonnet-4-6` model ID in the five agents that run on Sonnet
  (`plan-implementer`, `plan-implementer-backend`, `fx-repo-research`,
  `fx-learnings-research`, `rex-code-reviewer`) and in rex's Sonnet subagent dispatch
  prose (Subagents 1, 4, 5). Opus/Haiku subagents left as aliases. _(Reverted in
  v0.14.0.)_

## [0.12.0] — 2026-06-22

### Changed
- **`plan-implementer`** and **`plan-implementer-backend`** — added a **YAGNI /
  simplest-construct** Operating Principle to both implementers. They already
  enforced *scope* discipline ("build only what the plan specifies"); this adds the
  orthogonal *how-simply* axis: favor a plain function over a new abstraction, a
  literal over a config layer, the fewest lines that read clearly, and don't add
  generality, options, or indirection the plan doesn't call for. Pulls the simplicity
  principle — previously only at the brainstorm stage (`fx-brainstorm`'s 80/20 DHH
  audit) and the review stage (`rex-code-reviewer`'s Code Simplicity reviewer) — into
  the implement stage, so Rex catches less over-engineering after the fact. Wording
  is byte-identical across both forked agents to keep them trivially in sync.

## [0.11.0] — 2026-06-10

### Added
- **`fx-qa-mobile-ios`** now emits a **Maestro regression flow** on every verified
  fix — the iOS parity with `fx-qa-web`'s Phase 8e.5 regression test step. When a
  fix reaches `verified`, the skill translates the bug's already-documented Phase-4
  repro steps (the `/ax` targets, actions, and fixed outcome) into a minimal
  `.maestro/regression-<issue-id>.yaml` flow, resolves each action to an `id:`
  selector (RN `testID` → iOS `accessibilityIdentifier`), never emits coordinate
  taps, and commits it separately (`test(qa-ios): regression flow for ISSUE-NNN`).
  Skips silently when the fix is not `verified`, purely visual/layout-only, or
  no Maestro setup exists. Ships with a fail-once-then-delete policy so no red
  flow is ever left behind. Convention detail carried in a new
  `frxnls/skills/fx-qa-mobile-ios/references/maestro-emit.md`.
  Origin brainstorm: `docs/brainstorms/2026-06-10-maestro-ios-regression-requirements.md`.
  App-side Maestro install + CI wiring: `forked-up/fu#519`.

## [0.10.0] — 2026-06-10

### Changed
- **`rex-code-reviewer`** — widened the review remit beyond simplicity/security/docs
  so Rex catches the correctness and data-integrity classes it was structurally
  blind to (the kind `gemini-code-assist` was surfacing and Rex was missing):
  - New always-on **Correctness & Runtime Safety** reviewer (Subagent 4): logic/edge
    cases, null/undefined/**NaN-into-DB** propagation, `||` vs `??`, error handling
    (missing `.catch()` in `Promise.all`, silent failures, env-less crons),
    concurrency/lifecycle (TOCTOU races, leaked pages/timers/listeners,
    permanently-rejected promises), array-element type assumptions, and test guards
    that silently pass.
  - Expanded the conditional **Contracts & Migrations** reviewer into **Data
    Integrity, Contracts & Migrations** (Subagent 5): FK `onDelete` gaps via
    delete-path tracing, UNIQUE-constraint violations simulated against pre-existing
    **inactive/soft-deleted** rows, SQL↔app hash/serialization parity, soft-delete
    read leaks, non-sargable queries, and connection-pool exhaustion.
  - Broadened the Stage 2 triggers so the data-integrity reviewer fires on
    repositories, query builders, and backfill/sweep/cron scripts — not just
    `migrations/`.
  - Carved first-party reliability bugs (pool exhaustion, OOM, leaked
    handles/timers) out of the DoS hard-exclusion so they survive the merge gate.
  - Separated **confidence** (mechanism verified via the quoted line) from
    **trigger likelihood** (encoded in the P-level), so a verified-but-latent finding
    stays ≥75 instead of being wrongly suppressed by the confidence gate.
  - Validated by a blind backtest against `forked-up/fu` PRs #509/#518/#480: Rex
    independently reproduced gemini's P0 constraint-violation, FK-cascade, null-crash,
    and NaN-divide-by-zero findings (and found an extra P0 on #509).

## [0.9.0] — 2026-06-09

### Added
- **`fx-triage`** skill — the front of the loop: scans the project's work sources,
  ranks what's actionable, and surfaces a triage digest for you to green-light. It
  discovers and ranks but never implements — it hands green-lit items to `fx-ship`
  / `fx-debug`, keeping a human gate at the *front* of the pipeline that mirrors the
  one `fx-ship` keeps before merge. Built `gh`-first so it works in any clone (local
  or unattended cloud routine) with no MCP; Sentry/Linear/PostHog/Slack are optional
  enrichment that degrade gracefully (absence is noted in the digest, never fatal).
  Runs interactively or headless (scheduled routine → writes `docs/triage/<date>.md`
  and surfaces to a reporting connector). Documents both local-cron and cloud-routine
  provisioning, including how to configure the routine's OAuth connectors.

## [0.8.0] — 2026-06-03

### Added
- **`fx-debug`** skill — systematically find a bug's root cause, then fix it.
  Investigates before fixing (causal-chain gate, prediction-tested hypotheses,
  smart escalation) and optionally implements a test-first fix. Adapted from
  EveryInc's compound-engineering `ce-debug`, retargeted to the frxnls stack:
  it checks `docs/solutions/` first (dispatching `fx-learnings-research`) so a
  documented bug is a lookup not a re-investigation, drives web repro through
  the Playwright MCP / `fx-qa-web` and iOS through serve-sim /
  `fx-qa-mobile-ios`, and hands a fixed branch off via `gh` + `fx-compound`
  rather than the ce-only commit/brainstorm ecosystem. Ships with three
  reference files (`anti-patterns`, `investigation-techniques`,
  `defense-in-depth`).

## [0.7.0] — 2026-06-03

### Changed
- **BREAKING — every skill moved into the `fx-` namespace.** Invoke `fx-ship`,
  `fx-qa-web`, `fx-qa-mobile-ios`, `fx-teardown`, `fx-security-audit`,
  `fx-expo-worktree-dev`, and `fx-brainstorm` (renamed from
  `first-principles-brainstorm`). The old slash commands (`/frxnls:ship`,
  `/frxnls:qa-web`, …) no longer resolve. Agents keep their names
  (`rex-code-reviewer`, `plan-implementer`, `plan-implementer-backend`).
- `fx-brainstorm` can now emit a structured `docs/brainstorms/*-requirements.md`
  (with stable R/A/F/AE IDs) that `fx-plan` carries as its `origin:` — a
  document-based WHAT → HOW handoff.
- `plan-implementer` and `plan-implementer-backend` now read plans from
  `docs/plans/` and consult `docs/solutions/` learnings before implementing.
- `fx-ship` now points upstream at `fx-plan` and downstream at `fx-compound`.

### Added
- **`fx-plan`** skill — turns an idea, brainstorm doc, or GitHub issue into a
  researched, implementation-ready `docs/plans/*.md`: ID'd implementation units
  with test scenarios, a confidence/deepening pass, then a handoff to `fx-ship`.
  Adapted from EveryInc's compound-engineering `ce-plan`.
- **`fx-compound`** skill — captures a just-solved problem into `docs/solutions/`
  with searchable YAML frontmatter and seeds `CONCEPTS.md` vocabulary. Full /
  Lightweight / headless modes, overlap detection, schema retargeted to
  Expo/RN + Supabase/Drizzle. Adapted from EveryInc's `ce-compound`.
- **`fx-repo-research`** and **`fx-learnings-research`** agents — read-only scouts
  (codebase patterns; `docs/solutions/` + history) dispatched by `fx-plan` and
  `fx-compound`.

## [0.6.0] — 2026-06-02

### Changed
- Implementer agents became workspace-agnostic — the `ship` orchestrator owns the
  branch/worktree lifecycle. `plan-implementer`/`-backend` never create or destroy
  a workspace and refuse to commit on the trunk.

## [0.5.0] — 2026-06-01

### Added
- `ship` orchestration skill plus a `ship-batch` workflow — drive a defined
  plan/issue to a reviewed PR with human gates; batch mode runs independent items
  in parallel (one PR each).
- `qa-mobile-ios` skill — iOS Simulator QA driven through serve-sim.
- `plan-implementer` and `plan-implementer-backend` agents — execute a plan/issue
  to a PR; the backend fork adds migration-safety and contract verification.
- `expo-worktree-dev` skill — give the current worktree its own Expo dev server +
  iOS simulator, idempotently and without collisions.

### Changed
- Renamed the `qa` skill to `qa-web`.

## [0.4.0] — 2026-05-29

### Changed
- `rex-code-reviewer`: hybrid inline PR comments plus a Gemini-style severity-badge
  summary.

## [0.3.0] — 2026-05-28

### Added
- `security-audit` skill — whole-system, read-only "CSO" security posture audit.

### Changed
- Hardened the Rex security reviewer.

## [0.2.0] — 2026-05-28

### Added
- `first-principles-brainstorm` save choice — persist the synthesis to a file or
  open a GitHub issue.

## [0.1.0] — 2026-05-28

### Added
- Initial frxnls AI stack: the `qa` skill and the `rex-code-reviewer` agent,
  published via a local plugin marketplace served from GitHub.
- `first-principles-brainstorm` skill — adversarial first-principles interviewer.
