---
name: ship
description: Orchestrate an already-defined plan or GitHub issue from start to a reviewed PR — route it to the right implementer, run the matching QA, surface Rex's review, and stop at the human gates (never auto-merge). Use when asked to "ship this issue", "take this plan to a PR", "implement and QA #42", "run the full pipeline on this", or "deliver this plan". For many independent items at once it can launch a parallel batch workflow.
---

# /ship: plan/issue → implement → QA → PR (human-gated)

The connective tissue for the frxnls delivery pipeline. **You (the main session) are
the orchestrator; this skill is the playbook.** It takes work that is *already
defined* — a plan file or a GitHub issue — and drives it to a **reviewed PR**, then
hands back to the human. It does not plan, and it does not merge.

```
plan/issue ─▶ classify ─▶ set up branch/worktree ─▶ implement ─▶ PR ─▶ review (CI) + QA ─▶ (revisions) ─▶ [you merge] ─▶ /teardown
```

Upstream of this skill: shaping an idea into a plan (Claude Code plan mode, or
`first-principles-brainstorm`). Downstream: you review and merge.

## Inputs
- A plan file path (`.claude/plans/*.md`) or a GitHub issue (`#N` / URL).
- Several of them at once → see **Batch mode**.

## Routing (the decisions this skill encodes)

| Decision | Rule |
|---|---|
| **Implementer** | touches DB / migrations / schema / RLS / API contracts → `frxnls:plan-implementer-backend`; otherwise `frxnls:plan-implementer` |
| **QA** | PR changes a web surface → `qa-web`; changes an iOS/RN surface → `qa-mobile-ios` (boot the sim first with `expo-worktree-dev`); both → run both; pure infra/no UI → skip, and say so |
| **Workspace** | smart default → **confirm with the user**: a new **worktree** when you'll run items in parallel, want your main checkout untouched, or expect mobile QA (pairs with `expo-worktree-dev`); **branch-in-place** for a single quick task. *You* create it; the implementer only uses it |
| **Sequencing** | independent items → parallel, each in its **own worktree** (you create them); dependent items → serial in dependency order |

## Workflow (interactive — the default)

1. **Resolve** the input(s). If handed a rough *idea* rather than an approved
   plan/issue, **stop** — planning is upstream (plan mode / `first-principles-brainstorm`).
   This skill starts from a defined plan or issue.
2. **Classify** each item → implementer + expected QA surface. Show the routing
   decision before acting.
3. **Set up the workspace — you own this.** Pick a branch name (`claude/issue-<n>-<slug>`
   or `claude/plan-<slug>`), then choose branch-in-place vs a new worktree per the
   **Workspace** rule above — recommend one and **confirm with the user**. Create it:
   - branch-in-place → `git checkout -b <branch>`
   - worktree → `git worktree add <path> -b <branch>` (one per independent item)
4. **Implement** — delegate each item to the chosen `plan-implementer[-backend]`,
   launched **in the workspace you created**. It works on that branch, strictly in
   scope, verifies until green, and opens the PR — it will **not** create or destroy
   any branch/worktree. Independent items in parallel; dependent ones serial.
5. **Review** — Rex CI reviews each PR automatically on open. (You can also run
   `frxnls:rex-code-reviewer` on the PR for a local pass.)
6. **QA** — from each PR's diff, pick the surface and run `qa-web` and/or
   `qa-mobile-ios` (mobile: use `expo-worktree-dev` to get the app onto the sim).
7. **Revisions** — for corrections after review/QA, **re-invoke the implementer on the
   same branch/worktree**: it pushes more commits and *updates* the existing PR. The
   workspace stays alive for exactly this — it is never torn down mid-flight.
8. **Report** per item: PR URL, implementer used, verification, QA, review status, and
   any assumptions/blockers surfaced.
9. **GATE — stop before merge.** Hand back the PR(s) + QA + review for *you* to merge;
   never merge automatically (especially backend work). Once the PR is merged or
   abandoned, retire the workspace with **`/frxnls:teardown`** — nothing auto-cleans.

## Batch mode (parallel, for many independent items)

For several **independent** items at once ("ship #40, #41, #42"), run the bundled
Workflow instead of looping by hand:

- Read the sibling script [`ship-batch.workflow.js`](ship-batch.workflow.js) and pass
  its contents to the **Workflow tool** (`script`), with `args` set to the list of
  items, e.g. `["#40", "#41", ".claude/plans/x.md"]`.
- It classifies and implements each item in parallel, **each in its own worktree**
  (the script sets `isolation: 'worktree'`, since implementers no longer self-isolate)
  — each opens its own PR.
- **It stops at PRs** — no interactive QA. Rex CI still reviews each PR on open; run
  QA yourself afterward via the interactive path above.
- **Cost / safety:** it spawns one classifier + one implementer agent per item. Only
  launch it when the user explicitly asks for a batch/parallel run, and only for
  items that are genuinely independent (no shared files / ordering).

## Compose with
- `frxnls:plan-implementer` / `frxnls:plan-implementer-backend` — the implementers (they work on the workspace *you* set up).
- [`qa-web`](../qa-web/SKILL.md) / [`qa-mobile-ios`](../qa-mobile-ios/SKILL.md) — post-PR QA.
- [`expo-worktree-dev`](../expo-worktree-dev/SKILL.md) — boot the app on a sim for mobile QA.
- [`teardown`](../teardown/SKILL.md) — retire the branch/worktree (+ sim) once the PR is merged or abandoned.
- `frxnls:rex-code-reviewer` — local PR review (CI runs it automatically).
