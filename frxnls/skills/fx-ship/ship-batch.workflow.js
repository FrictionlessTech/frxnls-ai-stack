// Batch implementer for the frxnls `fx-ship` skill.
// Run via the Workflow tool: pass this file's contents as `script` and the work items
// as `args`, either the plain array (backward-compatible) or
// `{ items: [...], models: {...} }` — where `models` is the resolved key->model map
// from `resolve-model.py --all` (SKILL.md resolves it once before launching; workflow
// scripts can't shell out themselves). `models` is optional — omit it (or pass `{}`)
// to inherit the session default for every implementer spawn, e.g.
// args = ["#40", "#41", ".claude/plans/add-orders.md"], or
// args = { items: ["#40", "#41"], models: { "plan-implementer": "sonnet", "plan-implementer-backend": "opus" } }.
//
// Per item, in parallel:
//   1. PREPARE — classify backend-vs-generic AND create a dedicated git worktree on a
//      fresh feature branch (the implementers are workspace-agnostic and never make
//      branches/worktrees, so the batch sets the workspace up for them).
//   2. IMPLEMENT — run the chosen implementer agent INSIDE that worktree; it works on
//      the branch it was handed and opens its own PR, spawned with its resolved model
//      (from `models`, when provided).
//
// It STOPS at PRs: no QA, no merge. Rex CI reviews each PR on open. The worktrees
// PERSIST (for revisions) — retire each later with /frxnls:fx-teardown.
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

const items = Array.isArray(args)
  ? args
  : Array.isArray(args && args.items)
    ? args.items
    : (args ? [args] : [])
// Resolved key->model map from `resolve-model.py --all` (SKILL.md's batch step). Empty
// when omitted or args was a plain array — every agent() call below then omits `model`
// and the Workflow runtime inherits the session default (R8: never fail, never strand).
const models = (args && !Array.isArray(args) && args.models) || {}
if (!items.length) {
  log('No items in args. Pass an array of issue refs / plan paths, e.g. ["#40","#41",".claude/plans/x.md"], or { items: [...], models: {...} }.')
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
  (prep, item) => {
    const agentType = (prep && prep.implementer) || 'frxnls:plan-implementer'
    const implementerKey = agentType.replace(/^frxnls:/, '')
    return agent(
      `cd into the worktree at "${prep.path}" — it is already checked out on feature branch "${prep.branch}". Implement this work item there, end-to-end: "${item}"${prep && prep.title ? ` (${prep.title})` : ''}. Work on the current branch (never create or remove worktrees/branches), implement strictly in scope, verify until green, open the PR, and report the PR URL.`,
      {
        label: `implement ${item}`,
        phase: 'Implement',
        agentType,
        schema: IMPLEMENT_SCHEMA,
        model: models[implementerKey],
      },
    )
  },
)

const prs = results.filter(Boolean)
const modelsUsed = Object.keys(models).length
  ? `models: ${JSON.stringify(models)}`
  : 'models: session default (no .frxnls/model-tiers.json overrides resolved)'
log(`ship-batch done: ${prs.length}/${items.length} processed (${modelsUsed}). Rex CI reviews each PR on open; run fx-qa-web / fx-qa-mobile-ios interactively, and /frxnls:fx-teardown to retire each worktree.`)
return { items: items.length, prs }
