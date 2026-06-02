---
name: teardown
description: Retire a finished task's workspace — remove its linked git worktree, optionally delete the local branch, and shut down + delete its expo-wt-<branch> simulator + serve-sim if it had one. Use when asked to "tear down this worktree", "clean up the worktree", "retire this branch/task", "I merged the PR, clean up", or "remove the worktree for this task". Run after a PR is merged or abandoned. Never touches the main checkout.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# /teardown: retire a finished task's workspace

The inverse of the workspace setup that `ship` (or you) did, and of
[`expo-worktree-dev`](../expo-worktree-dev/SKILL.md). Implementers and the
orchestrator deliberately **never** auto-clean — so the branch/worktree stays alive
for revisions after PR + QA. Run this **once the PR is merged or abandoned** to
retire it. It never touches your main checkout.

## What it retires

| Thing | Action |
|---|---|
| Linked git **worktree** | `git worktree remove` (the task's working dir) |
| Local **branch** | `git branch -d` *(optional, only if merged; `-D` needs explicit confirm)* |
| **Simulator** (`expo-wt-<slug>`) + serve-sim | shut down + delete the device, stop the bundler — only if the task had one |
| **Remote** branch | left alone — GitHub auto-deletes on merge, or keep it |

## Identify the target

Default to the **current** worktree, or a branch/path named in the prompt.

```bash
TARGET_BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"
# the worktree path checked out on that branch:
TARGET_PATH=$(git worktree list --porcelain | awk -v b="refs/heads/$TARGET_BRANCH" '
  /^worktree /{p=$2} /^branch /{ if($2==b) print p }')
MAIN=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')   # the primary checkout
```

## Safety rules

- **Never** remove the main checkout (`$MAIN`) — only *linked* worktrees.
- You **cannot** remove the worktree you're standing in — `cd "$MAIN"` first.
- Refuse to delete an **unmerged** branch unless the user explicitly confirms (then `-D`).
- Leave the **remote** branch alone by default.
- If the worktree has uncommitted/untracked changes, stop and surface them before
  `--force` — don't silently discard work.

## Steps

1. **Resolve** `TARGET_BRANCH`, `TARGET_PATH`, `MAIN`, and the slug
   (`SLUG=$(printf '%s' "$TARGET_BRANCH" | tr '/:@ ' '----' | tr -cd 'A-Za-z0-9._-' | cut -c1-40)`).
   If `TARGET_PATH` is empty or equals `$MAIN`, there's no linked worktree to remove —
   say so and skip to step 4 (branch only).

2. **Sim teardown (if this was a mobile task)** — if a device `expo-wt-$SLUG` exists,
   retire it (mirrors `expo-worktree-dev`'s Teardown):
   ```bash
   UDID=$(xcrun simctl list devices | grep -F "expo-wt-$SLUG (" | grep -oiE '[0-9a-f-]{36}' | head -1)
   [ -n "$UDID" ] && { xcrun simctl shutdown "$UDID" 2>/dev/null; xcrun simctl delete "$UDID"; }
   # stop the bundler + drop state (see expo-worktree-dev): kill the recorded BUNDLER_PID, rm the state file
   ```

3. **Remove the worktree** (from the main checkout, never from inside it):
   ```bash
   cd "$MAIN"
   git worktree remove "$TARGET_PATH"     # add --force ONLY after confirming changes are disposable
   ```

4. **Delete the local branch (optional)** — only if merged, or with explicit confirm:
   ```bash
   git branch -d "$TARGET_BRANCH"         # -d refuses unless merged; use -D only when the user confirms
   ```

5. **Report** what was removed (worktree path, branch, sim) and what was intentionally
   left (e.g. the remote branch, an unmerged branch you didn't delete).

## Compose with
- [`expo-worktree-dev`](../expo-worktree-dev/SKILL.md) — the create side (sim + worktree).
- [`ship`](../ship/SKILL.md) — drives you here after a PR is merged or abandoned.
