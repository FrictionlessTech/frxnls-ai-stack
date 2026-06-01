// Batch implementer for the frxnls `ship` skill.
// Run via the Workflow tool: pass this file's contents as `script` and the list of
// work items as `args`, e.g. args = ["#40", "#41", ".claude/plans/add-orders.md"].
// Each item is classified, routed to the right implementer agent, and opened as its
// own PR — in parallel. It STOPS at PRs: no QA, no merge. Rex CI reviews each PR on
// open; run qa-web / qa-mobile-ios interactively afterward.
//
// Requires the frxnls plugin installed (agentType resolves frxnls:plan-implementer
// and frxnls:plan-implementer-backend). Untested end-to-end — exercise on real,
// independent issues before trusting it unattended.

export const meta = {
  name: 'ship-batch',
  description: 'Implement N independent plans/issues in parallel — classify each, route to the right implementer, open one PR per item. Stops at PRs (no QA, no merge).',
  phases: [
    { title: 'Classify', detail: 'route each item to plan-implementer or plan-implementer-backend' },
    { title: 'Implement', detail: 'one implementer agent per item; each opens its own PR' },
  ],
}

const CLASSIFY_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    implementer: { type: 'string', enum: ['frxnls:plan-implementer', 'frxnls:plan-implementer-backend'] },
    title: { type: 'string' },
    rationale: { type: 'string' },
  },
  required: ['implementer', 'title'],
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
  (item) => agent(
    `Classify this work item for routing: "${item}". Read it — a GitHub issue (#N or URL) or a plan .md path — and decide which implementer should build it. Choose plan-implementer-backend if it touches the database, migrations, schema, RLS, or API contracts; otherwise plan-implementer.`,
    { label: `classify ${item}`, phase: 'Classify', schema: CLASSIFY_SCHEMA },
  ),
  (route, item) => agent(
    `Implement this work item end-to-end and open a PR: "${item}"${route && route.title ? ` (${route.title})` : ''}. Follow your full workflow: isolate in your own worktree, implement strictly in scope, verify until green, open the PR, and report the PR URL.`,
    {
      label: `implement ${item}`,
      phase: 'Implement',
      agentType: (route && route.implementer) || 'frxnls:plan-implementer',
      schema: IMPLEMENT_SCHEMA,
    },
  ),
)

const prs = results.filter(Boolean)
log(`ship-batch done: ${prs.length}/${items.length} processed. Rex CI reviews each PR on open; run qa-web / qa-mobile-ios interactively afterward.`)
return { items: items.length, prs }
