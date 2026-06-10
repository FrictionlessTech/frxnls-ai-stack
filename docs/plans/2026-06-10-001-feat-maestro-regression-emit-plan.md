---
title: "feat: Emit Maestro regression flows from fx-qa-mobile-ios"
type: feat
status: active
date: 2026-06-10
deepened: 2026-06-10
origin: docs/brainstorms/2026-06-10-maestro-ios-regression-requirements.md
scope: skill-side only (frxnls-ai-stack). App-side Maestro setup + nightly CI tracked
  in a separate GitHub issue in forked-up/fu.
---

# feat: Emit Maestro regression flows from fx-qa-mobile-ios

## Problem & Scope

`fx-qa-mobile-ios` explores a running iOS app via serve-sim, finds bugs, fixes them,
and verifies — but the run is one-shot. Nothing it confirms becomes a re-runnable
regression test. Its web sibling `fx-qa-web` already closes this loop: Phase 8e of its
fix loop writes a bun regression test tagged `// Regression: ISSUE-NNN`. The iOS skill
makes the same promise in prose ("Fix Loop — same discipline as fx-qa-web") but never
delivers the artifact.

This plan brings the iOS skill to parity by teaching its Fix Loop to **emit a Maestro
YAML flow** when a fix is `verified` — translated from the bug's documented repro,
keyed on accessibility ids, asserting the fixed outcome, stored in `.maestro/` in the
app repo under test. serve-sim stays the
interactive driver for discovery/find-fix; Maestro is the replay back end
(see origin: `docs/brainstorms/2026-06-10-maestro-ios-regression-requirements.md`).

**In scope** (this repo, the frxnls plugin source):
- A new emit sub-step in `fx-qa-mobile-ios`'s Fix Loop (the iOS analogue of fx-qa-web 8e).
- A `references/maestro-emit.md` carrying the frxnls emit convention.
- Version bump + CHANGELOG.

**Out of scope** (tracked in a `forked-up/fu` issue — created at handoff):
- Installing Maestro, authoring the hand-curated smoke set, the nightly non-blocking CI
  workflow, and the `testID` instrumentation audit. These live in the app repo, not here.
- Any change to `fx-qa-web` beyond a one-line cross-reference (deferred follow-up).

---

## Key Decisions

**KTD-1 — Mirror fx-qa-web's Phase 8e, don't invent.** The emit step is the iOS twin of
the existing web regression step: same trigger (`verified` classification), same
attribution convention (two-line, see KTD-6), same "born from a bug"
discipline. The only difference is the artifact: a Maestro flow instead of a bun test.
This keeps the two QA skills symmetric and honors the iOS skill's existing "same
discipline as fx-qa-web" claim. (Source: `fx-qa-web/SKILL.md:228-240`, Phase 8e/8e.5.)
Faithful-twin parity extends to the details below: attribution format (KTD-6), emit
mechanism (KTD-7), self-containment (KTD-8), skip conditions (KTD-5), and the
fail-once-then-delete policy (U1).

**KTD-2 — One flow per verified fix, not per session.** Maestro's own guidance is "one
user intent per flow." Each verified fix yields one `.maestro/regression-<issue-id>.yaml`
scoped to the minimal action sequence that reproduces the bug's trigger and asserts the
fix. The hand-curated smoke set is authored separately on the app side — the skill never
auto-sprays flows for every screen visited (origin R3, R4).

**KTD-3 — id-first selector resolution; never emit coordinate taps.** Each action the
agent took is resolved back to its `/ax` node and emitted as Maestro `id:` (RN `testID`
→ iOS `accessibilityIdentifier` → Maestro `id`), falling back to `text:` only when the
node exposes no stable id. A `point:`/coordinate tap is **never** emitted — if a node is
unidentifiable, the skill fails loudly and flags it for human review. This is the same
AX-first "fail loudly, don't guess" rule the skill already enforces for tapping
(`fx-qa-mobile-ios/SKILL.md:58-61`, Rule 2). Coordinate-based flows were explicitly
killed in the brainstorm.

**KTD-4 — Carry the emit convention in a local `references/maestro-emit.md`.** The Maestro
format detail (selector mapping, regex escaping, robustness flags, CI shape) is too long
for the SKILL.md body and is frxnls-specific guidance, not just upstream docs. Three
frxnls skills already use `references/` for deep detail (fx-debug, fx-plan, fx-compound);
this follows that pattern. The SKILL.md keeps a tight summary and links to it. (serve-sim
depth is deferred to serve-sim's external skill; Maestro ships no such skill, so a local
reference is the right call.)

**KTD-5 — Skip conditions, mirroring fx-qa-web 8e.5's three-skip rule.** fx-qa-web skips
emission when *not verified*, *pure CSS*, or *no test setup* (`fx-qa-web/SKILL.md:233`).
The iOS twin skips when: **not `verified`** (a `best-effort` or `reverted` fix can't be
confirmed green — a red/unverifiable flow is worse than none); **purely-visual /
layout-only fix** (no assertable accessibility-node outcome — the iOS analogue of "pure
CSS"); or **no Maestro setup** (no `.maestro/` dir and Maestro absent — the analogue of
"no test setup"; emit is a no-op, not an error).

**KTD-6 — Two-line attribution + separate commit, verbatim twin of 8e.5.** Header comment:
`# Regression: ISSUE-NNN - <what broke>` then `# Found by /fx-qa-mobile-ios on <YYYY-MM-DD>`
— two lines, ASCII dash `-` (not em-dash), matching `fx-qa-web/SKILL.md:237-238`. The
emitted flow gets its **own** commit (`test(qa-ios): regression flow for ISSUE-NNN`),
separate from the fix commit — same cadence as the web twin's `test(qa):` commit.

**KTD-7 — Emit by *translating documented repro steps*, not by recording actions.**
fx-qa-web reconstructs the test from the repro steps its Document phase already wrote
(prose + screenshots), re-reasoning the codepath — it never instruments or logs actions
(`fx-qa-web/SKILL.md:149-153, 233-236`). The iOS twin does the same: the Phase-4 bug repro
(documented `/ax` targets + actions + the fixed outcome) **is** the source material; the
emit step translates those already-recorded steps into Maestro commands. No action-tracking
infrastructure is added — this is a pure translation step, which is why it fits a markdown
skill with no code.

**KTD-8 — Self-contained flows; shared setup is an app-side smoke-set concern.** fx-qa-web
has no shared-setup/fixture convention — each test "sets up the triggering state" itself.
So each emitted Maestro regression flow is **self-contained**: its own `launchApp` +
navigation to the trigger, no `runFlow` dependency. The `runFlow`/`login.yaml` sub-flow
reuse the research surfaced belongs to the **hand-curated smoke set** (app-side, fu#519),
not the auto-emitted regression flows — keeping each generated flow independently
runnable and independently deletable (KTD-2). The only "match nearby style" port: if
`.maestro/` already holds flows, match their shape; else fall back to the
`references/maestro-emit.md` template.

---

## Implementation Units

### U1 — Add the emit sub-step to the Fix Loop

**File:** `frxnls/skills/fx-qa-mobile-ios/SKILL.md`

Insert a regression-emit sub-step into the **Fix Loop** section (`SKILL.md:152-161`),
immediately after the `verified` classification in the "Re-test" bullet — the seam
identified in research. Mirror the structure and wording of `fx-qa-web/SKILL.md` Phase 8e
so the two skills read as twins.

The new sub-step (label it **8e.5's iOS twin**, e.g. a "Regression flow" bullet in the
Fix Loop) must say, concisely:
- **Skip unless `verified`** — and also skip purely-visual/layout-only fixes and the
  no-Maestro-setup case (KTD-5). Skips are silent no-ops, not errors.
- **Translate, don't record** — reconstruct the flow from the bug's already-documented
  Phase-4 repro steps (the `/ax` targets, actions, and fixed outcome), not from any action
  log (KTD-7). Emit the **minimal** sequence that triggers the bug and asserts the fix —
  not the whole exploration path (KTD-2).
- **Self-contained** — each flow carries its own `launchApp` + navigation; no `runFlow`
  dependency (KTD-8). Match existing `.maestro/*.yaml` style if any exist, else the
  reference template.
- Resolve each action to a Maestro `id:` selector from the `/ax` node; fall back to
  `text:` only when no id; **never** emit a `point:` tap — fail loudly and flag for human
  review if a node is unidentifiable (KTD-3).
- **Two-line header** (KTD-6): `# Regression: ISSUE-NNN - <what broke>` then
  `# Found by /fx-qa-mobile-ios on <YYYY-MM-DD>`.
- **Fail-once-then-delete** (twin of `fx-qa-web/SKILL.md:239-240`): after emitting, run
  `maestro test .maestro/regression-<id>.yaml`; if it fails, attempt **one** correction,
  else delete the file and defer — never leave a red flow behind.
- **Separate commit** (KTD-6): `test(qa-ios): regression flow for ISSUE-NNN`, distinct
  from the `fix(qa-ios): ...` fix commit.
- Defer all Maestro YAML mechanics to `references/maestro-emit.md` (KTD-4) — keep the
  SKILL.md text to the *when/why/what*, not the *how*.

Also update two existing sections:
- **Output Structure** (`SKILL.md:173-178`): add the app-repo `.maestro/regression-*.yaml`
  output alongside `.qa-reports/`.
- **Compose with** (`SKILL.md:180-183`): add a bullet for Maestro (replay/CI back end)
  and a pointer to the new reference.

`Write` is already in `allowed-tools` — no frontmatter change required.

**Validation scenarios:**
- Given a verified fix whose trigger element exposes a `testID`, the emitted YAML targets
  it with `id:` (not `text:`, not `point:`), opens with its own `launchApp` (self-contained,
  no `runFlow`), and asserts the outcome with `assertVisible`.
- Given a verified fix whose trigger element exposes **no** stable id, the skill emits a
  `text:` selector and notes the weaker target — and does **not** emit a coordinate tap.
- Given a `best-effort` or `reverted` classification, a **purely-visual/layout-only** fix,
  or a repo with **no Maestro setup**, **no** `.maestro/` file is written (silent skip).
- Given an emitted flow that fails its own `maestro test` once: the skill attempts one
  correction, and if it still fails, **deletes** the file and defers (no red flow left behind).
- The emitted file carries the two-line `# Regression: ISSUE-NNN - <what broke>` /
  `# Found by /fx-qa-mobile-ios on <date>` header and lives at
  `.maestro/regression-<issue-id>.yaml`; its flow gets a separate `test(qa-ios):` commit.

### U2 — Add `references/maestro-emit.md` (the emit convention)

**File:** `frxnls/skills/fx-qa-mobile-ios/references/maestro-emit.md` (new; `mkdir`
the `references/` dir — first one for this skill)

A focused reference the emit sub-step links to. Contents, grounded in the external
research:
- **Flow anatomy** — `appId:` header, `---` separator, command list; a minimal real
  example.
- **Selector resolution table** — RN `testID` → iOS `accessibilityIdentifier` → Maestro
  `id:`; `accessibilityLabel` → `text:`. id-first rule and the no-`point:` rule (KTD-3).
- **Regex-escaping rule** — `text:`/`id:` values are regexes; escape captured literals
  containing `$ ( ) . [ ]` (e.g. price/label strings), or prefer an `id:`.
- **Outcome assertions** — `assertVisible` on a stable outcome id + `assertNotVisible` of
  the prior loading/error state; use regex for variable text (`Order #[0-9]+`); never bake
  in volatile values (timestamps, order numbers).
- **Robustness flags** — lean on built-in ~7s auto-retry; `retryTapIfNoChange: true` for
  swallowed taps, `waitForAnimationToEnd` before animated screens, `extendedWaitUntil`
  (condition-based) for known-slow boundaries, `optional: true` for permission
  dialogs/one-time UI. **No fixed sleeps.**
- **One-intent-per-flow + naming + self-containment** — `.maestro/regression-<issue-id>.yaml`,
  the two-line `# Regression: ISSUE-NNN - <what broke>` / `# Found by /fx-qa-mobile-ios on
  <date>` header (KTD-6), each flow self-contained with its own `launchApp` (KTD-8). Note
  that the hand-curated smoke set (app-side) is where shared `runFlow`/`login.yaml` reuse
  lives — not the auto-emitted regression flows.
- **Lifecycle rules** — the skip conditions (KTD-5) and the fail-once-then-delete policy
  (run the new flow once; one correction, else delete) so the reference fully specifies
  when a flow is and isn't written.
- **Top brittleness gotchas** (from research §7): coordinate taps, unescaped regex,
  fixed sleeps, volatile-text selectors — each with the fix.
- **CI note (brief)** — `maestro test .maestro/`, exit 0/1, macOS-runner requirement,
  non-blocking via `continue-on-error`; point to the `forked-up/fu` app-side issue rather
  than specifying the workflow here.

Cite the authoritative Maestro doc URLs gathered in research so the convention is
traceable.

**Validation scenarios:**
- The reference's example flow is valid Maestro YAML (would parse / `maestro test`).
- The selector-resolution and regex-escaping rules are unambiguous enough that two
  implementers emit the same selector for the same `/ax` node.

### U3 — Version bump + CHANGELOG

**Files:** `frxnls/.claude-plugin/plugin.json`, `CHANGELOG.md`

- Bump `frxnls/.claude-plugin/plugin.json` `version` `0.10.0` → `0.11.0` (new skill
  capability = minor bump, per repo convention).
- Add a `## [0.11.0] — 2026-06-10` entry to `CHANGELOG.md` with an `### Added` note:
  fx-qa-mobile-ios now emits Maestro regression flows on verified fixes (iOS parity with
  fx-qa-web's regression step). Reference the origin brainstorm.
- Commit convention for the eventual commit: `feat(frxnls): emit Maestro regression flows
  from fx-qa-mobile-ios (v0.11.0)`.

**Dependency:** land after U1 + U2 (version reflects the shipped change).

---

## Sequencing

U1 and U2 are tightly coupled (U1 links to U2) and can be authored together; U2 is the
substance U1 points at. U3 is last. No app-repo dependency blocks this plan — the skill
change is self-contained text.

---

## Risks

**R-1 (top) — The `testID` prerequisite is unverified.** id-first emission (KTD-3)
assumes app nodes expose stable `accessibilityIdentifier`/`testID`s. This was *not*
validated (the brainstorm's "hand-write one flow" assignment was skipped). If ids are
largely absent, the skill will frequently fall back to `text:` (more brittle) or fail
loudly — degrading the value of emitted flows. **Mitigation:** the no-`point:` rule means
the failure mode is "weaker/needs-review flow," never "silently brittle coordinate flow."
The real fix is the app-side `testID` audit, tracked in the `forked-up/fu` issue.
**This risk lives in the app, not in this plan's code** — but the skill must degrade
gracefully, which U1's validation scenarios cover.

**R-2 — Convention drift from fx-qa-web.** If the iOS emit wording diverges from fx-qa-web
8e, the "twin skills" promise erodes. **Mitigation:** U1 explicitly mirrors 8e's structure;
a deferred follow-up adds a reciprocal cross-reference in fx-qa-web.

**R-3 — Auto-generated flows are brittle by default.** Covered head-on by U2's gotcha
rules (regex escaping, no sleeps, no volatile text, no coordinates). The residual risk is
the agent not following them — bounded by keeping the rules explicit and example-driven.

---

## Deferred to Follow-Up Work

- Reciprocal cross-reference in `fx-qa-web/SKILL.md` pointing to the iOS Maestro emit (and
  noting the artifact difference).
- A future `CONCEPTS.md` could canonize "bug-derived flow", "smoke set", "non-blocking
  gate" — owned by `fx-compound`, not this plan.

---

## Open Questions (deferred to implementation)

- Exact filename when one issue id spans multiple distinct flows (suffix `-a`/`-b`?) —
  decide if/when it arises; default is one flow per issue id.
- Whether to also emit/update a flow index or rely on `maestro test .maestro/` globbing —
  default to globbing (no index) until a need appears.

---

## App-Side Handoff (separate repo: forked-up/fu)

**Tracking issue: forked-up/fu#519** (https://github.com/forked-up/fu/issues/519) covers
the work this plan deliberately excludes: install
Maestro, author the 2–3 hand-curated smoke flows, add the nightly non-blocking CI workflow
(macOS runner, `continue-on-error`, JUnit upload), and run the `testID` instrumentation
audit (the R-1 prerequisite). The merge gate is earned later, critical-path subset only,
once the false-positive rate is observed to be low (origin R8–R11).
