---
name: expo-worktree-dev
description: Ensure the CURRENT git worktree has its own dedicated iOS simulator and Expo dev server — idempotently and without colliding with any other worktree's sim or port. Reuses this worktree's sim/bundler if it already has them; otherwise spins up a dedicated sim named for the worktree and allocates a free port. Use when asked to "run the app in this worktree", "spin up a sim for this branch", "preview this worktree", "launch the app here", or when an agent needs to run the app it built in a worktree. macOS + Xcode only.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# /expo-worktree-dev: one sim + bundler per worktree, idempotently

This skill operates on **the current worktree only**. It does *not* decide whether
to run multiple branches — you run it once per worktree, and each run gives *that*
worktree its own isolated simulator and Expo dev server. Run it in two worktrees and
you get two isolated setups; run it twice in the same worktree and the second run is
a no-op that reattaches to what's already there.

It's also the "run the app to see/verify it" step for worktree agents (e.g.
`plan-implementer`): after building a mobile change in a worktree, call this to
launch it. To QA the running **web** build in a browser, compose with [`qa`](../qa/SKILL.md).

## What it guarantees

| Concern | Mechanism |
|---|---|
| **Idempotent** — don't double-spawn | Reuse this worktree's recorded sim + bundler if they're still alive |
| **No two worktrees share a sim** | Each worktree owns a **dedicated device named `expo-wt-<slug>`** — the name *is* the binding, so contention is impossible and it's never a sim you drive by hand |
| **No port collision with a sibling** | Allocate a **free** port and persist it per-worktree; a running sibling holds its port, so the scan skips it |
| **The sim actually exists** | Create the device from a device type + runtime that `simctl` reports available — never a hardcoded name |

## Prerequisites (check, don't assume)

```bash
sw_vers -productName >/dev/null 2>&1 || { echo "not macOS"; exit 1; }
xcrun simctl help >/dev/null 2>&1 || { echo "no Xcode CLT"; exit 1; }
```

Detect the project shape in this worktree (decides the run commands — never hardcode):

```bash
# package manager + Expo SDK (use commands valid for THIS project)
[ -f bun.lockb ] && PM=bunx; [ -f pnpm-lock.yaml ] && PM="pnpm exec"; [ -f yarn.lock ] && PM=yarn; : "${PM:=npx}"
grep -E '"expo"' package.json
# Expo Go vs custom dev client → dev client needs a per-worktree prebuild
grep -q '"expo-dev-client"' package.json && echo "DEV CLIENT" || echo "Expo Go (maybe)"
```

## Identity & state (per worktree)

Derive a stable slug and a state file that lives **outside the repo** (so it never
dirties git, and survives `git status`). The dedicated device name is recoverable
from `simctl` even if the state file is lost.

```bash
ROOT=$(git rev-parse --show-toplevel)
BRANCH=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git rev-parse --short HEAD)
SLUG=$(printf '%s' "$BRANCH" | tr '/:@ ' '----' | tr -cd 'A-Za-z0-9._-' | cut -c1-40)
DEVICE="expo-wt-$SLUG"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/expo-worktree-dev"; mkdir -p "$STATE_DIR"
STATE="$STATE_DIR/$(printf '%s' "$ROOT" | shasum | cut -c1-12).env"
[ -f "$STATE" ] && . "$STATE"   # loads prior DEVICE/UDID/PORT/BUNDLER_PID, if any
```

## Workflow (single worktree)

### Step 1 — Ensure this worktree's dedicated simulator exists and is booted

Find the device by its dedicated name (reuse on re-runs); create it only if missing,
choosing an **available** iPhone type + the newest installed iOS runtime:

```bash
UDID=$(xcrun simctl list devices | grep -F "$DEVICE (" | grep -oiE '[0-9a-f-]{36}' | head -1)
if [ -z "$UDID" ]; then
  DEVTYPE=$(xcrun simctl list devicetypes | grep -i 'iPhone' | tail -1 | grep -oE 'com\.apple[^ )]*')
  RUNTIME=$(xcrun simctl list runtimes  | grep -i 'iOS' | grep -vi unavailable | tail -1 | grep -oE 'com\.apple\.CoreSimulator\.SimRuntime[^ ]*')
  UDID=$(xcrun simctl create "$DEVICE" "$DEVTYPE" "$RUNTIME")
fi
xcrun simctl boot "$UDID" 2>/dev/null || true   # no-op if already booted
open -a Simulator
```

Because the device is named per worktree, **no other worktree can be using it** —
that's the whole point. If `UDID` came from state but `simctl` no longer lists it
(deleted by hand), the `grep` returns empty and the create branch above recreates it.

### Step 2 — Allocate (or reuse) a free dev-server port

Keep this worktree's persisted port if its bundler is still alive; otherwise keep the
number if it's free, else scan for a free one (a sibling's running bundler holds its
port, so the scan naturally skips it):

```bash
port_free() { ! nc -z localhost "$1" 2>/dev/null; }
if [ -n "$BUNDLER_PID" ] && kill -0 "$BUNDLER_PID" 2>/dev/null; then
  : # our bundler is alive → keep $PORT and reuse it (Step 3 reattaches)
else
  { [ -n "$PORT" ] && port_free "$PORT"; } || \
    for p in $(seq 8081 8181); do port_free "$p" && { PORT=$p; break; }; done
fi
```

### Step 3 — Ensure exactly one bundler for this worktree, on that port

If our recorded bundler is alive, reattach to it (do nothing). Otherwise start one in
the background **from this worktree's directory** so it serves this branch's code.
Picking an explicit free port avoids Expo's interactive "port in use?" prompt, which
would stall an unattended/agent run.

```bash
if ! { [ -n "$BUNDLER_PID" ] && kill -0 "$BUNDLER_PID" 2>/dev/null; }; then
  # command substitution (NOT `... | read`, which sets the var in a dead subshell)
  BUNDLER_PID=$( cd "$ROOT" && nohup $PM expo start --port "$PORT" >"$STATE_DIR/$SLUG.log" 2>&1 & echo $! )
fi
```

### Step 4 — Launch the app onto this worktree's device (deterministically)

⚠️ Don't press `i` in the Expo terminal to "send it to this worktree's sim" — `i`
targets whichever simulator is last-active, not your worktree's. Target by **UDID**,
run from this worktree so it builds/installs/launches against this worktree's bundler:

```bash
# custom dev client? the native binary is branch-specific → prebuild in THIS worktree first
grep -q '"expo-dev-client"' "$ROOT/package.json" && ( cd "$ROOT" && $PM expo prebuild --clean )
( cd "$ROOT" && $PM expo run:ios --device "$UDID" --port "$PORT" )
```

(Expo Go projects skip the prebuild; UDID targeting still routes each branch to its
own device.)

### Step 5 — Persist state

```bash
printf 'DEVICE=%s\nUDID=%s\nPORT=%s\nBUNDLER_PID=%s\n' "$DEVICE" "$UDID" "$PORT" "$BUNDLER_PID" > "$STATE"
```

Re-running the skill in this worktree now reattaches: same device, same port, same
bundler — no duplicates.

## Teardown (when this worktree is done / removed)

```bash
. "$STATE" 2>/dev/null
[ -n "$BUNDLER_PID" ] && kill "$BUNDLER_PID" 2>/dev/null
xcrun simctl shutdown "$UDID" 2>/dev/null
xcrun simctl delete   "$UDID" 2>/dev/null   # removes this worktree's dedicated device
rm -f "$STATE"
```

Do this before `git worktree remove`, or as cleanup if you notice orphaned
`expo-wt-*` devices in `xcrun simctl list devices`.

## Gotchas

1. **Device names aren't portable** — always create from a `simctl`-reported
   available type/runtime; "iPhone 15" may not exist on a given Xcode.
2. **`press i` is non-deterministic** with multiple sims — target by UDID (Step 4).
3. **Free, persisted port** — an interactive port-reassignment prompt stalls agent runs.
4. **Dev client ≠ Expo Go** — only custom dev clients need a per-worktree prebuild.
5. **Install per worktree** the first time (`$PM expo install`); don't assume a
   sibling worktree's `node_modules` applies.
6. **Version-agnostic by design** — this skill discovers devices/ports/SDK at
   runtime. If a command differs for your Expo SDK, trust `$PM expo <cmd> --help`.

## Compose with

- [`qa`](../qa/SKILL.md) — once the app is running, QA-test the web build in a real
  browser. This skill gets it running; `qa` exercises it.
- Worktree agents (e.g. `plan-implementer`) — call this as the "run the app to
  verify" step after building a mobile change in a worktree.
