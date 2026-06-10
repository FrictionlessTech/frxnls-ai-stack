# Maestro Emit Convention

How `fx-qa-mobile-ios` translates a verified fix into a durable `.maestro/regression-*.yaml`
flow. This reference covers YAML anatomy, selector resolution, robustness flags, lifecycle
rules, and brittleness gotchas.

Authoritative upstream docs:
- Flow syntax: https://maestro.mobile.dev/reference/configuration/flow-configuration
- Selectors: https://maestro.mobile.dev/reference/selectors
- Commands: https://maestro.mobile.dev/reference/commands
- CI integration: https://maestro.mobile.dev/ci-integration/

---

## Flow anatomy

A Maestro flow file is a YAML document with an `appId:` header, an optional
`name:` label, a `---` separator, and a flat command list.

**Minimal real example** — guards a verified fix where the cart badge was not updating:

```yaml
appId: com.example.myapp
name: Regression - cart badge updates after add-to-cart (ISSUE-042)
---
# Regression: ISSUE-042 - cart badge did not update after add-to-cart
# Found by /fx-qa-mobile-ios on 2026-06-10

- launchApp
- tapOn:
    id: "product-list-item-0"
- tapOn:
    id: "add-to-cart-button"
- assertVisible:
    id: "cart-badge"
- assertVisible:
    text: "1"
- assertNotVisible:
    text: "0"
```

The `appId` is the iOS bundle identifier (same as `CFBundleIdentifier` in `Info.plist`
and the `bundleIdentifier` in `app.json`/`app.config.js`). Confirm it with:
```bash
xcrun simctl get_app_container booted <bundleId> app 2>/dev/null || \
  grep -r 'bundleIdentifier' app.json app.config.js 2>/dev/null | head -3
```

---

## Selector resolution

Maestro selects elements by the iOS accessibility metadata that React Native exposes.
Resolve in this order — id first, text fallback, never coordinates:

| Situation | RN attribute | iOS metadata | Maestro selector | Notes |
|-----------|-------------|--------------|-----------------|-------|
| Stable programmatic id | `testID="cart-badge"` | `accessibilityIdentifier` | `id: "cart-badge"` | **Preferred.** Survives label/text changes. |
| No testID, readable label | `accessibilityLabel="Add to cart"` | `accessibilityLabel` | `text: "Add to cart"` | Weaker — breaks if copy changes. Note the weaker target in a comment. |
| No id, no label, visual-only | — | — | **Do not emit.** Flag for human review. | Never emit a `point:` coordinate tap. |

**id-first rule:** always prefer `id:` over `text:`. A `text:` selector is a deliberate
downgrade — comment why no id was available so a future `testID` audit can fix it.

**Never emit `point:`** — coordinate taps are fossils, not regression tests. If a node
is unidentifiable by id or text, fail loudly:
```
[emit] Cannot resolve ISSUE-NNN trigger element to id: or text: — node has no
accessibilityIdentifier or accessibilityLabel. Flagging for human review. Flow not written.
```

---

## Regex-escaping rule

Maestro's `text:` and `id:` values are **regular expressions**, not plain strings.
Characters with special regex meaning must be escaped when you want them matched
literally. Common culprits in mobile UI:

| Raw text | Contains | Escaped value |
|----------|----------|--------------|
| `$12.99` | `$` `.` | `\\$12\\.99` |
| `Order #519` | `#` | `Order #519` (safe — `#` is not a regex metacharacter in most engines) |
| `(Optional)` | `(` `)` | `\\(Optional\\)` |
| `[Beta]` | `[` `]` | `\\[Beta\\]` |
| `Loading...` | `.` | `Loading\\.\\.\\.` |

**Rule of thumb:** prefer an `id:` for any selector containing `$`, `(`, `)`, `.`,
`[`, `]`. Reserve `text:` for labels that are simple words or sentences with no
punctuation that doubles as a regex metacharacter.

For variable values (order numbers, timestamps, prices), use a regex pattern:
```yaml
- assertVisible:
    text: "Order #[0-9]+"
```

---

## Outcome assertions

Every emitted flow must assert a **meaningful state transition**, not cosmetic detail.

**Preferred pattern:**
```yaml
- assertVisible:
    id: "order-confirmation-banner"   # stable outcome id
- assertNotVisible:
    id: "checkout-loading-spinner"    # prior loading/error state gone
```

**Variable text (order numbers, prices, timestamps):**
```yaml
- assertVisible:
    text: "Order #[0-9]+"
```

**Do not assert:**
- Exact volatile values (e.g. a timestamp, a specific order number baked in).
- Layout measurements or pixel coordinates.
- Cosmetic text that isn't load-bearing for the bug being guarded.

---

## Robustness flags

Maestro has ~7 s built-in auto-retry for most assertions. Lean on it.
Use explicit flags only when the built-in wait is insufficient:

| Situation | Flag / command | Example |
|-----------|---------------|---------|
| Tap lands but UI doesn't react (swallowed tap) | `retryTapIfNoChange: true` | `tapOn: { id: "submit-btn", retryTapIfNoChange: true }` |
| Animated screen transition | `waitForAnimationToEnd` | `- waitForAnimationToEnd` (before the first assertion) |
| Known-slow API boundary (skeleton → content) | `extendedWaitUntil` | `- extendedWaitUntil: { visible: { id: "feed-list" }, timeout: 15000 }` |
| Permission dialog or one-time UI | `optional: true` | `- tapOn: { text: "Allow", optional: true }` |

**No fixed sleeps** — never use `- runScript: sleep(N)` or similar. Fixed sleeps are
fragile, slow, and mask real timing issues.

---

## One intent per flow — naming and self-containment

**One flow, one bug.** Each emitted flow encodes exactly one verified fix: the minimal
action sequence that reproduces the bug's trigger and asserts the fixed outcome.
Do not combine multiple bugs into one flow.

**Naming:** `.maestro/regression-<issue-id>.yaml`
- Example: `.maestro/regression-042.yaml` for ISSUE-042.
- If one issue id covers two genuinely distinct action sequences (rare), suffix:
  `-a` / `-b` (e.g. `regression-042-a.yaml`). Default: one flow per issue id.

**Self-contained:** every flow starts with `launchApp` and navigates to the trigger
from scratch — no `runFlow` dependency. This keeps each regression flow independently
runnable and independently deletable.

```yaml
# self-contained — always start here
- launchApp
- tapOn:
    id: "tab-orders"
# ... rest of the repro sequence
```

`runFlow`/login sub-flow reuse belongs to the **hand-curated smoke set** (app-side,
`forked-up/fu#519`), not auto-emitted regression flows.

**Attribution header** — always two lines, ASCII dash `-` (not em-dash):
```yaml
# Regression: ISSUE-NNN - {what broke}
# Found by /fx-qa-mobile-ios on {YYYY-MM-DD}
```

---

## Lifecycle rules

**Skip conditions (silent no-ops, not errors):**

1. Fix is not `verified` — a `best-effort` or `reverted` fix can't be confirmed green;
   a red or unverifiable flow is worse than none.
2. Purely-visual / layout-only fix — no assertable accessibility-node outcome exists
   (the iOS analogue of fx-qa-web's "pure CSS" skip).
3. No Maestro setup — no `.maestro/` directory, or `maestro` not on PATH. Emit is a
   no-op; do not create the directory or install Maestro.

**Fail-once-then-delete policy:**

After writing the flow, run it once:
```bash
maestro test .maestro/regression-<issue-id>.yaml
```
- Passes → commit with `test(qa-ios): regression flow for ISSUE-NNN` (separate from the
  fix commit).
- Fails → attempt **one** correction (fix a selector, adjust a timing flag).
  - Corrected run passes → commit.
  - Still fails → **delete the file** and defer. Log: "regression flow for ISSUE-NNN
    deleted — could not be made green; flagged for human review."
  - Never leave a red flow in the repo.

---

## Top brittleness gotchas

These are the most common ways an emitted flow breaks — and the fix for each:

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| **Coordinate tap** | Flow breaks on any layout change | Replace `point:` with `id:` or `text:`; if impossible, delete and flag |
| **Unescaped regex in `text:`** | `ElementNotFound` on prices or labels with `$`/`.`/`(` | Escape metacharacters or switch to `id:` |
| **Fixed sleep** | Flaky on slow CI runners | Replace with `extendedWaitUntil` or `waitForAnimationToEnd` |
| **Volatile-text selector** | Breaks whenever copy/price/order number changes | Use regex pattern (`Order #[0-9]+`) or switch to `id:` |
| **Shared `runFlow` dep** | One broken sub-flow takes down all regression flows | Keep each regression flow self-contained; reuse only in smoke set |
| **Missing `launchApp`** | Flow starts in wrong state if previous run left dirty state | Always begin with `launchApp` |

---

## CI note (brief)

App-side CI wiring is tracked in `forked-up/fu#519`. The frxnls-side convention:

- Run all flows: `maestro test .maestro/`
- Exit codes: 0 = all pass, 1 = any failure.
- Requires a **macOS runner** (Simulator + idb/XCUITest).
- Initial cadence: **nightly against `main`**, non-blocking (`continue-on-error: true`).
- Results posted as PR comment / JUnit artifact; build never fails on them at first.
- A merge gate is earned later, scoped to the critical-path smoke subset only,
  after the observed false-positive rate is low.
