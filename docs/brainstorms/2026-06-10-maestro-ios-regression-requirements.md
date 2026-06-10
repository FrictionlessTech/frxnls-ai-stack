---
date: 2026-06-10
topic: maestro-ios-regression
---

# Maestro-backed iOS regression flows from `fx-qa-mobile-ios`

## Summary

Add a regression-test capability to the iOS QA loop: keep driving the Simulator with
**serve-sim** for exploratory find/fix/verify, and at the moment a fix is *verified*,
distil that confirmed flow into a durable **Maestro** YAML flow keyed on accessibility
ids. Maestro flows run in CI **non-blocking** (nightly against `main` to start), and
earn a merge gate only later, only for a small critical-path subset, only once the
data justifies it. Canary is explicitly **not** in the mobile path.

---

## Problem Frame

iOS QA runs today are one-shot: `fx-qa-mobile-ios` explores, finds bugs, fixes, and
verifies, but leaves behind a report — nothing re-runnable. The goal is for those runs
to deposit regression tests that catch the same breakage again later.

The tempting framing — "extend canary to drive serve-sim" — was rejected on first
principles. canary *is* the Playwright `Page` API (DOM-shaped: `goto`, `click`,
`getByRole`, `locator`). A native RN/Expo screen on the Simulator has no DOM; serve-sim
exposes an **accessibility tree + normalized-coordinate input** instead. serve-sim's
preview *can* be opened in a browser, but it renders the framebuffer into a single
opaque `<canvas>`, so Playwright/canary sees zero semantic structure and degrades to
brittle `mouse.click(x,y)` — the opposite of a durable regression test. The durable,
semantic layer already exists (serve-sim `/ax` labels), and the tool built to *replay*
flows keyed on those labels is Maestro, not canary.

---

## Key Decisions

**serve-sim front, Maestro back — they are complementary, not competing.** serve-sim is
an interactive driver (observe `/ax` → reason → act → re-observe, with live `/.sim/logs`)
and is the right tool for agent-in-the-loop *discovery and find/fix*. Maestro is a
declarative runner (`tapOn`, `assertVisible`, built-in waiting/retry, CI) and is the
right tool for deterministic *replay*. Neither does the other's job well. The bridge
between them is the accessibility id: the label the agent taps during exploration is the
`tapOn` target in the emitted flow.

**Regression tests are born from a bug, not from a screen.** Flows are NOT generated from
exploration breadth (that produces a brittle "screen rendered" suite that everyone learns
to ignore). They are emitted at two moments only: (1) after a fix is verified, encoding
"this broke once, never again"; (2) a hand-curated handful of money/auth-critical happy
paths as smoke. Every kept flow traces to a real defect or a critical path.

**The gate is earned, not assumed.** Maestro runs report-only at first. A merge gate is
switched on later, for the critical-path subset only, only after the false-positive rate
is observed to be low.

**Stable accessibility ids are the shared dependency.** Both serve-sim `/ax` targeting
and Maestro `tapOn` read the same accessibility metadata. Fuzzy/absent `testID` /
`accessibilityLabel`s make exploration guessy *and* replay brittle. This is a
prerequisite, not a nice-to-have.

---

## Requirements

**Emit (inside the `fx-qa-mobile-ios` fix loop)**

R1. When a fix is classified `verified` in the fix loop, the run emits (or updates) a
    Maestro flow that reproduces the bug's trigger and asserts the fixed outcome.
R2. Emitted flows target elements by stable `testID` / accessibility id — never by
    fuzzy visible text and never by raw coordinate.
R3. Flows are NOT auto-generated for screens merely visited during exploration. Breadth
    of exploration must not translate into breadth of emitted flows.
R4. A small, hand-curated smoke set (≈2–3 flows) covers the money/auth-critical happy
    paths, maintained separately from the bug-derived regression flows.
R5. Each emitted flow asserts a meaningful state transition / outcome
    (e.g. `assertVisible: "Order confirmed"`), not cosmetic or layout detail.

**Storage & shape**

R6. Flows live in `.maestro/` in the repo under test, in standard Maestro YAML.
R7. Each bug-derived flow carries a traceable link back to the issue/bug it guards
    (so a failing flow points at the original defect).

**Run & gate**

R8. Maestro runs in CI **non-blocking** (`continue-on-error`) initially — results are
    posted as a PR comment / artifact; the build never fails on them.
R9. The initial cadence is **nightly against `main`**, not per-PR, to control macOS
    runner cost while the suite is non-gating.
R10. A flow that fails twice for a non-bug reason (legitimate UI change) is either
     hardened (id-based selector) or deleted. Un-stabilizable flows are removed.
R11. A merge gate is introduced only later, scoped to the critical-path smoke subset,
     and only after the observed false-positive rate is low. Per-PR execution can
     accompany that gate.

**Boundary**

R12. Canary is not introduced into the mobile/iOS path in any form. If canary is ever
     used, it is pointed at the **web build** (react-native-web) via `fx-qa-web`, as a
     separate, deliberate decision — out of scope here.

---

## Key Flows

F1. **Bug → regression flow**
    - **Trigger:** a fix reaches `verified` in the `fx-qa-mobile-ios` fix loop.
    - **Steps:** capture the sequence of semantic actions that reproduce the bug
      (the `/ax` labels the agent tapped/typed) → emit/update a `.maestro/<flow>.yaml`
      that replays them → assert the fixed outcome → link the flow to the bug/issue.
    - **Outcome:** a durable, id-targeted Maestro flow that fails if the bug recurs.

F2. **Nightly regression run**
    - **Trigger:** scheduled nightly job on `main` (macOS runner).
    - **Steps:** boot a Simulator → `maestro test .maestro/` → collect results →
      post as comment/artifact.
    - **Outcome:** non-blocking signal on whether any guarded flow regressed; no build
      failure.

---

## Scope Boundaries

### Deferred for later
- Per-PR execution and any **merge gate** — only after non-blocking data shows a low
  false-positive rate, and only for the critical-path subset (R11).
- Broadening the suite beyond bug-derived flows + the small smoke set.
- Detox — consider only if async-timing flakiness becomes the dominant pain; it buys
  RN-bridge-synced determinism at the cost of instrumented binaries and heavier,
  less agent-authorable test code.

### Outside this product's identity
- Extending/forking canary onto serve-sim, or browser-over-framebuffer automation —
  rejected on layer-mismatch grounds (see Problem Frame).
- Coordinate-based "reproducible" scripts in any form — they are fossils, not
  regression tests.

---

## Dependencies / Assumptions

- **Stable `testID` / `accessibilityLabel`s** on the RN components under test. This is
  load-bearing for R2/R5 and for serve-sim targeting generally.
- macOS CI runners available for Simulator + Maestro (idb/XCUITest).
- The exploratory find/fix half of QA is genuinely wanted (it justifies keeping
  serve-sim). If only the regression artifact were wanted, Maestro alone — authored via
  its Studio inspector — would suffice and serve-sim's role would shrink.

---

## Outstanding Questions

### Resolve Before Planning
- Are the critical-path screens' elements addressable by stable id **today**? Audit one
  flow's `/ax` output before building the emitter — if labels are fuzzy, the real first
  project is instrumenting `testID`s, not the emit step.

### Deferred to Planning
- Exact emit mechanism: does the agent author the YAML directly from the recorded action
  sequence, or capture a structured action log during the fix and template it?
- How the bug→flow link (R7) is represented (filename convention, in-file comment,
  issue id).
- Concrete CI wiring (which macOS runner, Maestro install/caching, result-posting
  format).

---

## The Assignment (validate before building)

Pick the single highest-value flow (login / checkout). Inspect each screen's
`curl -s localhost:$STREAM/ax` for stable ids, **hand-write the Maestro YAML for that one
flow, and run it twice** against the Simulator. If it passes twice and survives a trivial
layout tweak, the approach is proven in an afternoon with zero integration code. If the
ids are too fuzzy to target, you've found the real work (instrumentation) before building
anything.

---

## Sources / Research

- serve-sim — `https://github.com/EvanBacon/serve-sim` (AX tree `/ax`, `tap/gesture/type`,
  device logs `/.sim/logs`). See memory `ios-simulator-driver-serve-sim`.
- canary — `https://github.com/wizenheimer/canary` (Playwright + QuickJS, web-only;
  reproducible-script output is Playwright JS).
- `fx-qa-mobile-ios` skill — existing serve-sim-driven find/fix/verify loop the emit step
  hooks into.
- Maestro — declarative mobile E2E (YAML flows, iOS Simulator via idb/XCUITest, CI/cloud).
