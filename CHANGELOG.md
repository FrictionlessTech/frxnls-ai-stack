# Changelog

All notable changes to the **frxnls** plugin are recorded here. Versions track
`frxnls/.claude-plugin/plugin.json`. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
[Semantic Versioning](https://semver.org/) — while on `0.x`, anything may change
between minor versions.

## [Unreleased]

_Nothing yet._

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
