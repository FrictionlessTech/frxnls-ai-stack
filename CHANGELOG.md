# Changelog

All notable changes to the **frxnls** plugin are recorded here. Versions track
`frxnls/.claude-plugin/plugin.json`. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
[Semantic Versioning](https://semver.org/) — while on `0.x`, anything may change
between minor versions.

## [Unreleased]

_Nothing yet._

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
