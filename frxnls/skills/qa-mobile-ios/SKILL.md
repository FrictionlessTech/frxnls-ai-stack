---
name: qa-mobile-ios
description: Systematically QA-test a running iOS app on the Simulator, then fix the bugs found and verify each fix. Use when asked to "qa the app", "test this on the simulator", "find bugs in the iOS app", "test and fix the mobile app", or "does this screen work?" for an iOS/Expo app. Drives the simulator via serve-sim (accessibility tree + tap/gesture/type + device logs). For a web app use qa-web instead.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Edit
  - Write
---

# /qa-mobile-ios: Test → Fix → Verify (iOS Simulator)

Native-app QA — the mobile sibling of [`qa-web`](../qa-web/SKILL.md). Test a running
iOS app as a user, document bugs with screenshot evidence, fix them at the React
Native source, and verify each fix.

The driver is **[serve-sim](https://github.com/EvanBacon/serve-sim)** (Evan Bacon):
it streams the Simulator framebuffer and exposes an **accessibility tree** plus input
commands. This skill is the QA *methodology*; serve-sim is the *driver* — don't
re-document its internals here. Install serve-sim's own skill for the full driver
reference (gesture JSON, permissions, camera, helper scripts):

```bash
bunx add-skill EvanBacon/serve-sim
```

iOS only. To get the app onto a sim first, compose with
[`expo-worktree-dev`](../expo-worktree-dev/SKILL.md). For web QA, use `qa-web`.

> Not yet validated against a live Simulator from this repo — endpoints/commands
> below are from serve-sim's published docs. Trust `npx serve-sim --help` and
> serve-sim's references if anything differs on your machine.

## Driver mapping (serve-sim)

Observe-then-act, like `qa-web`'s snapshot-then-click — but the "snapshot" is the
**AX tree**, and you act by **normalized (0–1) coordinates**. Every command is scoped
to **this worktree's** device + serve-sim instance — resolve them once in **Step 0**
into `$UDID`, `$STREAM` (stream port), and `$PREVIEW` (preview port). Never assume
`booted` or the default 3100/3200; both are wrong the moment a second worktree is up.

| Need | serve-sim | Notes |
|------|-----------|-------|
| discover instances | `npx serve-sim --list -q` | JSON of running streams — device + ports/URLs for each. Step 0 picks ours |
| **element tree** | `curl -s localhost:$STREAM/ax` | axe-style JSON: labels + normalized positions. **Find targets here first** |
| screen config | `curl -s localhost:$STREAM/config` | width/height/orientation (px→0–1 conversion) |
| foreground app | `curl -s localhost:$STREAM/foreground` | bundle id + pid — confirm you're on the right app/screen |
| **tap** | `npx serve-sim tap <x> <y> -d "$UDID"` | normalized 0–1 from an AX element — never a guess |
| swipe / scroll / pinch | `npx serve-sim gesture '{"type":"begin",…}' -d "$UDID"` → `move` → `end` | exact JSON in serve-sim's `references/gestures.md` |
| type text | `npx serve-sim type "<text>" -d "$UDID"` | into the focused field |
| hardware button | `npx serve-sim button home -d "$UDID"` (lock, …) | |
| rotate | `npx serve-sim rotate <orientation> -d "$UDID"` | `portrait` / `landscape_left` / … |
| **device logs** (console) | `curl -sN localhost:$PREVIEW/.sim/logs` | SSE/NDJSON — RN LogBox/redbox, JS errors, native logs |
| screenshot (evidence) | `xcrun simctl io "$UDID" screenshot <file>` | **always `$UDID`, never `booted`** — `booted` is ambiguous with multiple sims |

**AX-first rule (serve-sim's own guidance):** fetch `/ax` to locate a target; if the
query returns nothing, **fail loudly** ("target not found") — tapping a guessed spot
is almost always worse than reporting it.

## Step 0 — Resolve the target device + serve-sim instance (do this first)

With multiple worktrees running there are multiple booted sims and multiple serve-sim
instances on different ports. Pin to **this worktree's** device. Resolution order:

1. **Explicit override** — a device name/UDID given in the prompt wins.
2. **This worktree's dedicated device** — `expo-worktree-dev` boots a device named
   `expo-wt-<slug>`; derive the *same* slug and resolve its UDID. This device name is
   the shared key between the two skills — both compute it identically:
   ```bash
   BRANCH=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git rev-parse --short HEAD)
   SLUG=$(printf '%s' "$BRANCH" | tr '/:@ ' '----' | tr -cd 'A-Za-z0-9._-' | cut -c1-40)
   DEVICE="expo-wt-$SLUG"
   UDID=$(xcrun simctl list devices | grep -F "$DEVICE (" | grep -oiE '[0-9a-f-]{36}' | head -1)
   ```
3. **Single instance** — no worktree device, but exactly one serve-sim instance up → use it.
4. Otherwise **fail loudly** — list candidates and ask which device; do not guess:
   `npx serve-sim --list -q`.

Then find (or start) the serve-sim instance bound to `$UDID` and capture its ports:

```bash
# match the `--list -q` entry whose device == $UDID; if none stream it, start one
# (serve-sim picks a free port — it does NOT reuse 3100/3200 when those are taken):
#   npx serve-sim "$DEVICE"        # or "$UDID"
# read THAT instance's ports from --list -q, or each instance's
# GET :<preview>/.sim/api -> {device, port, streamUrl, wsUrl}
STREAM=...    # that instance's stream port  (3100 only if it's the sole instance)
PREVIEW=...   # that instance's preview port (3200 only if it's the sole instance)
```

Hold `$UDID`, `$STREAM`, `$PREVIEW` for every command this run.

## Setup (after Step 0)

```bash
REPORT_DIR=".qa-reports/$(date +%Y-%m-%d)"; mkdir -p "$REPORT_DIR/screenshots"
BASE=$(git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p' || echo main)
```

Precondition: `curl -s localhost:$STREAM/ax` returns a tree **for our device**. If it
doesn't, stop and say so — do not fall back to another sim or to unit tests (this
skill is driver-based by definition).

## Modes (mirror qa-web)

- **Diff-aware** (default on a feature branch, no screen named): `git diff "$BASE"...HEAD
  --name-only` → map changed RN files to screens (route/screen files → screens,
  components → screens that render them, hooks/services → screens using them) and test those.
- **Full** (a flow/screen named): walk the app systematically.
- **Quick** (`--quick`): launch + top flows smoke test, health score only.

## Workflow

### Phase 1 — Initialize
Run Setup. Note the time.

### Phase 2 — Orient
Confirm the foreground app (`/foreground`), capture an initial screenshot
(`simctl io`), fetch `/ax` to map the first screen, and read `/.sim/logs` for
launch-time errors (RN redbox, native warnings).

### Phase 3 — Explore (per screen, like a user)
At each screen:
1. **Screenshot** for the visual record.
2. **`/ax`** → enumerate interactive elements (buttons, inputs, tabs, list rows).
3. **Visual scan** of the screenshot — layout, safe-area/notch clipping, overflow,
   truncation, contrast, loading placeholders that never resolve.
4. **Interact** — tap controls (by AX-derived coords), `type` into fields, submit;
   test empty / invalid / boundary input.
5. **Gestures** — scroll long lists, swipe, pull-to-refresh, pinch where relevant.
6. **States** — empty, loading, error, **offline**, long-content/overflow.
7. **Permissions** — trigger the OS dialogs the feature needs; exercise allow *and*
   deny paths (serve-sim `references/permissions.md`).
8. **Orientation** — `rotate` if the screen supports it; re-screenshot to check reflow.
9. **Logs** — after each interaction, check `/.sim/logs` for new JS/native errors.
   Invisible RN warnings/errors are still bugs.

Depth over breadth: core flows + the changed feature get the time; less on static screens.

### Phase 4 — Document (immediately, not batched)
Per bug: screenshot **before** → perform action → screenshot **after** → describe
what changed → repro steps referencing the screenshots **and** the relevant
`/.sim/logs` lines. Append to the report as you go. `Read` each screenshot file so it
renders inline for the user.

### Phase 5 — Wrap up
Health score, "Top 3 Things to Fix", aggregate log errors, metadata (device, OS,
screens visited, screenshot count). Save `baseline.json` (same shape as `qa-web`).

## Fix Loop (same discipline as qa-web)
For each fixable bug, severity order:
- **Locate** the RN source — Grep component names / on-screen strings; Glob
  `screens/`, `components/`, `app/` for the screen.
- **Fix** minimally at the source — no refactors, no unrelated changes.
- **Commit** one per fix: `git commit -m "fix(qa-ios): ISSUE-NNN - <desc>"`.
- **Re-test** — reload via Fast Refresh, re-screenshot, re-check `/ax` and
  `/.sim/logs`; classify `verified` / `best-effort` / `reverted`.
- **Self-regulation** — every 5 fixes or after any revert, STOP and evaluate before
  continuing. Hard cap 50 fixes. (See `qa-web` for the full WTF-likelihood rubric.)

## Important Rules
1. **Repro is everything** — every bug needs ≥1 screenshot.
2. **AX-first** — never tap a guessed coordinate; fail loudly if `/ax` can't find the target.
3. **Check `/.sim/logs` after every interaction** — RN errors are often invisible on screen.
4. **Show screenshots to the user** — `Read` each file so it renders inline.
5. **Test as a user during discovery**; read source only in the fix loop.
6. **Never refuse the driver** — if serve-sim or the sim isn't up, set it up (or ask); don't fall back to unit tests.
7. **Defer driver depth** (gesture JSON, camera, permissions) to serve-sim's references — don't reinvent them here.

## Output Structure
```
.qa-reports/<YYYY-MM-DD>/
├── qa-ios-report-<slug>-<YYYY-MM-DD>.md
├── screenshots/  (initial.png, issue-001-before.png, issue-001-after.png, …)
└── baseline.json
```

## Compose with
- **serve-sim skill** — the full driver. Install: `bunx add-skill EvanBacon/serve-sim`.
- [`expo-worktree-dev`](../expo-worktree-dev/SKILL.md) — boot the app on a per-worktree sim before QA.
- [`qa-web`](../qa-web/SKILL.md) — the web sibling (same loop, Playwright driver).
