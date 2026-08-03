---
name: "fx-ship"
description: "Orchestrate an already-defined plan or GitHub issue from start to a reviewed PR — route it to the right implementer, run the matching QA, surface Rex's review, and stop at the human gates (never auto-merge). Use when asked to \"ship this issue\", \"take this plan to a PR\", \"implement and QA #42\", \"run the full pipeline on this\", or \"deliver this plan\". For many independent items at once it can launch a parallel batch workflow."
---

## Codex execution

Before running this workflow, read `../../references/runtime.md` and apply its
Codex-specific delegation, interaction, and model-selection rules. Those rules
override any provider-specific wording that remains below.

# /fx-ship: plan/issue → implement → QA → PR (human-gated)

The connective tissue for the frxnls delivery pipeline. **You (the main session) are
the orchestrator; this skill is the playbook.** It takes work that is *already
defined* — a plan file or a GitHub issue — and drives it to a **reviewed PR**, then
hands back to the human. It does not plan, and it does not merge.

```
plan/issue ─▶ classify ─▶ set up branch/worktree ─▶ implement ─▶ PR ─▶ review (CI) + QA ─▶ (revisions) ─▶ [you merge] ─▶ /fx-teardown
```

Upstream of this skill: shaping an idea into a plan — `fx-brainstorm` (WHAT) then
`fx-plan` (HOW, → `docs/plans/*.md`), or Codex plan mode. Downstream: you
review and merge, then `fx-compound` captures what was learned.

## Inputs
- A plan file path (`docs/plans/*.md` from `fx-plan`, or `docs/plans/*.md`) or a
  GitHub issue (`#N` / URL).
- Several of them at once → see **Batch mode**.

## Routing (the decisions this skill encodes)

| Decision | Rule |
|---|---|
| **Implementer** | touches DB / migrations / schema / RLS / API contracts → `$plan-implementer-backend`; otherwise `$plan-implementer` |
| **QA** | PR changes a web surface → `fx-qa-web`; changes an iOS/RN surface → `fx-qa-mobile-ios` (boot the sim first with `fx-expo-worktree-dev`); both → run both; pure infra/no UI → skip, and say so |
| **Workspace** | smart default → **confirm with the user**: a new **worktree** when you'll run items in parallel, want your main checkout untouched, or expect mobile QA (pairs with `fx-expo-worktree-dev`); **branch-in-place** for a single quick task. *You* create it; the implementer only uses it |
| **Sequencing** | independent items → parallel, each in its **own worktree** (you create them); dependent items → serial in dependency order |

## Workflow (interactive — the default)

1. **Resolve** the input(s). If handed a rough *idea* rather than an approved
   plan/issue, **stop** — planning is upstream (`fx-plan`, or plan mode /
   `fx-brainstorm`). This skill starts from a defined plan or issue.
2. **Classify** each item → implementer + expected QA surface. Show the routing
   decision before acting.
3. **Set up the workspace — you own this.** Pick a branch name (`codex/issue-<n>-<slug>`
   or `codex/plan-<slug>`), then choose branch-in-place vs a new worktree per the
   **Workspace** rule above — recommend one and **confirm with the user**. Create it:
   - branch-in-place → `git checkout -b <branch>`
   - worktree → `git worktree add <path> -b <branch>` (one per independent item)
4. **Implement** — delegate each item to the chosen `plan-implementer[-backend]`,
   launched **in the workspace you created**. It works on that branch, strictly in
   scope, verifies until green, and opens the PR — it will **not** create or destroy
   any branch/worktree. Independent items in parallel; dependent ones serial.
   **Codex dispatch.** Use the built-in role from `../../references/runtime.md`; let Codex choose the subagent model unless the user explicitly requests one.
5. **Review** — Rex CI reviews each PR automatically on open. (You can also run
   `$rex-code-reviewer` on the PR for a local pass.)
6. **QA** — from each PR's diff, pick the surface and run `fx-qa-web` and/or
   `fx-qa-mobile-ios` (mobile: use `fx-expo-worktree-dev` to get the app onto the sim).
7. **Revisions** — for corrections after review/QA, **re-invoke the implementer on the
   same branch/worktree**: it pushes more commits and *updates* the existing PR. The
   workspace stays alive for exactly this — it is never torn down mid-flight.
8. **Report** per item: PR URL, implementer used, verification, QA, review status, and
   any assumptions/blockers surfaced.
9. **GATE — stop before merge.** Hand back the PR(s) + QA + review for *you* to merge;
   never merge automatically (especially backend work). Once the PR is merged or
   abandoned, retire the workspace with **`$fx-teardown`** — nothing auto-cleans.

## Batch mode (parallel, for many independent items)

For several genuinely independent items, use Codex's native collaboration tools:

1. Confirm the items do not share files or ordering dependencies.
2. Create one `codex/<slug>` branch and linked worktree per item.
3. Spawn one built-in `worker` per worktree, give it exclusive ownership of that
   worktree, and instruct it to use `$plan-implementer` or
   `$plan-implementer-backend`.
4. Wait for every worker and return one PR per item. Batch mode stops at PRs;
   interactive QA and the human merge gate remain separate.

Use batch mode only when the user explicitly asks for parallel delivery.

## Compose with
- `$plan-implementer` / `$plan-implementer-backend` — the implementers (they work on the workspace *you* set up).
- [`fx-qa-web`](../fx-qa-web/SKILL.md) / [`fx-qa-mobile-ios`](../fx-qa-mobile-ios/SKILL.md) — post-PR QA.
- [`fx-expo-worktree-dev`](../fx-expo-worktree-dev/SKILL.md) — boot the app on a sim for mobile QA.
- [`fx-teardown`](../fx-teardown/SKILL.md) — retire the branch/worktree (+ sim) once the PR is merged or abandoned.
- `$rex-code-reviewer` — local PR review (CI runs it automatically).
