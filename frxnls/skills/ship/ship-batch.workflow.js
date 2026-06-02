// Batch implementer for the frxnls `ship` skill.
// Run via the Workflow tool: pass this file's contents as `script` and the list of
// work items as `args`, e.g. args = ["#40", "#41", ".claude/plans/add-orders.md"].
//
// Per item, in parallel:
//   1. PREPARE — classify backend-vs-generic AND create a dedicated git worktree on a
//      fresh feature branch (the implementers are workspace-agnostic and never make
//      branches/worktrees, so the batch sets the workspace up for them).
//   2. IMPLEMENT — run the chosen implementer agent INSIDE that worktree; it works on
//      the branch it was handed and opens its own PR.
//
// It STOPS at PRs: no QA, no merge. Rex CI reviews each PR on open. The worktrees
// PERSIST (for revisions) — retire each later with /frxnls:teardown.
// Requires the frxnls plugin installed (agentType resolves the implementer agents).
// Untested end-to-end — exercise on real, independent items first.

export const meta = {
  name: 'ship-batch',
  description: 'Implement N independent plans/issues in parallel — prepare a worktree+branch and route each to the right implementer, one PR per item. Stops at PRs (no QA, no merge).',
  phases: [
    { title: 'Prepare', detail: 'classify backend-vs-generic + create a worktree on a fresh branch' },
    { title: 'Implement', detail: 'run the chosen implementer in that worktree; each opens a PR' },
  ],
}

const PREPARE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    path: { type: 'string', description: 'absolute path of the created worktree' },
    branch: { type: 'string' },
    implementer: { type: 'string', enum: ['frxnls:plan-implementer', 'frxnls:plan-implementer-backend'] },
    title: { type: 'string' },
  },
  required: ['path', 'branch', 'implementer'],
}

const IMPLEMENT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    prUrl: { type: 'string' },
    branch: { type: 'string' },
    status: { type: 'string', enum: ['opened-pr', 'blocked', 'failed'] },
    note: { type: 'string' },
  },
  required: ['status'],
}

const items = Array.isArray(args) ? args : (args ? [args] : [])
if (!items.length) {
  log('No items in args. Pass an array of issue refs / plan paths, e.g. ["#40","#41",".claude/plans/x.md"].')
  return { items: 0, prs: [] }
}
log(`ship-batch: ${items.length} independent item(s), in parallel.`)

const results = await pipeline(
  items,
  // 1 — classify + create the workspace (NOT the implementer agent, so implementers stay pure)
  (item, _orig, i) => agent(
    `Prepare an isolated workspace to implement this work item: "${item}" (index ${i}).
1. Read it — a GitHub issue (#N or URL) or a plan .md path — to understand the work.
2. Decide the implementer: "frxnls:plan-implementer-backend" if it touches the database, migrations, schema, RLS, or API contracts; otherwise "frxnls:plan-implementer".
3. Create a dedicated git worktree on a NEW feature branch off the default branch:
     base=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
     git fetch -q origin "$base"
     root=$(git rev-parse --show-toplevel)
     git worktree add "$root/../ship-${i}-<slug>" -b "claude/<slug>" "origin/$base"
   Pick a short <slug> from the item; the "${i}" index keeps parallel paths unique.
Report the absolute worktree path, the branch name, the chosen implementer, and a one-line title. Do NOT implement anything yet.`,
    { label: `prepare ${item}`, phase: 'Prepare', schema: PREPARE_SCHEMA },
  ),
  // 2 — implement INSIDE that worktree, on the branch it was handed
  (prep, item) => agent(
    `cd into the worktree at "${prep.path}" — it is already checked out on feature branch "${prep.branch}". Implement this work item there, end-to-end: "${item}"${prep && prep.title ? ` (${prep.title})` : ''}. Work on the current branch (never create or remove worktrees/branches), implement strictly in scope, verify until green, open the PR, and report the PR URL.`,
    {
      label: `implement ${item}`,
      phase: 'Implement',
      agentType: (prep && prep.implementer) || 'frxnls:plan-implementer',
      schema: IMPLEMENT_SCHEMA,
    },
  ),
)

const prs = results.filter(Boolean)
log(`ship-batch done: ${prs.length}/${items.length} processed. Rex CI reviews each PR on open; run qa-web / qa-mobile-ios interactively, and /frxnls:teardown to retire each worktree.`)
return { items: items.length, prs }
