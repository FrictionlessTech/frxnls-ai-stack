---
date: 2026-07-20
topic: agent-model-config
---

## Summary

Make every model assignment in the frxnls plugin — the five agents' frontmatter
models and Rex's per-finder tiers — configurable at the install site via a
project-level config file, with repo defaults consolidated into one canonical map
and resolved deterministically at spawn time.

---

## Problem Frame

Model assignments are hard-coded as literals scattered through the plugin: `model:
sonnet` in all five agent frontmatters, plus inline per-finder tiers in
`rex-code-reviewer.md` (docs=haiku, security=opus, others=sonnet). Changing any of
them requires editing this repo and cutting a plugin release — which has already
happened once for exactly this reason. Installed repos have different stakes and
budgets and should set their own policy.

Per-invocation "dynamic routing" (compound-engineering style) was considered and
rejected: task-type complexity is static and already captured by perspective-level
tiering, and a runtime complexity judge costs tokens and can silently misroute
(e.g. security review on haiku).

---

## Key Decisions

- **Static map, not a router.** Model choice varies by task *type* (static), not
  per invocation. No runtime complexity assessment.
- **Enforcement by convention via the Agent tool.** Claude Code has no native
  per-install override for plugin agent frontmatter. frxnls skills and Rex read the
  config and pass the resolved model as the Agent tool's `model` parameter on each
  spawn. Agents invoked directly outside a frxnls skill fall back to frontmatter
  defaults — an accepted seam.
- **Deterministic resolution over prose convention.** A small resolver script
  shipped with the plugin (approach B), not "read the config" instructions restated
  in every skill (approach A, rejected as drift-prone and unverifiable).
- **One override level.** Repo defaults → project config file. No user-level file,
  no precedence cascade.
- **Project-level, because stakes differ per repo** — a high-stakes product repo
  and a throwaway side project should be able to run different maps.

---

## Requirements

**Configurability**

R1. Every model assignment currently hard-coded in the plugin (five agent
frontmatters; Rex's five finder perspectives) must be changeable in the repo where
the plugin is installed, without a plugin release.

R2. Repo defaults live in **one** canonical defaults map inside the plugin,
replacing the scattered literals as the source of truth. Agent frontmatter `model:`
values remain only as the direct-invocation fallback and must agree with the map.

R3. The override is a single project-level config file at a stable, documented path
in the installed repo. No user-level config, no merge cascade.

R4. Config keys address both whole agents (e.g. `plan-implementer`) and Rex finder
perspectives (e.g. `rex-code-reviewer.security`).

R5. Config values are Claude Code model aliases (`haiku` / `sonnet` / `opus`), not
pinned model IDs, so new model generations don't invalidate existing config files.

**Resolution & enforcement**

R6. A resolver shipped with the plugin returns the effective model for a key
(project override if set, else repo default) deterministically — callable by skills
and Rex via Bash before each spawn.

R7. Every frxnls spawner passes the resolved model as the Agent tool's `model`
parameter: fx-ship, fx-plan (research scouts), Rex (finder fan-out),
and any skill that spawns plan-implementer / plan-implementer-backend /
fx-repo-research / fx-learnings-research.

R8. A repo with no config file (or an unreadable/malformed one, or an unknown key)
behaves exactly as today: repo defaults apply. Malformed config must never abort a
review or build.

**Observability**

R9. The resolved model per spawn is visible in output — Rex's summary comment
lists which model each finder actually ran on; other skills state the model when
they spawn an implementer/scout. Silent misrouting must be detectable.

---

## Acceptance Examples

AE1. **Covers R6, R7.** Given a project config setting
`rex-code-reviewer.security: sonnet`, when Rex runs a full review in that repo,
then the security finder is spawned with `model: sonnet` and the summary comment
reports it.

AE2. **Covers R8.** Given no config file in the repo, when any frxnls skill spawns
an agent, then the model matches today's behavior (defaults map) exactly.

AE3. **Covers R8.** Given a config file with invalid JSON, when Rex runs, then the
review completes on repo defaults (a warning may be surfaced, but never a failure).

AE4. **Covers R4, R8.** Given a config containing an unknown key
(`rex-code-reviewer.styling: haiku`), when the resolver runs, then the unknown key
is ignored and all known keys resolve normally.

---

## Scope Boundaries

### Deferred for later
- Wiring beyond the MVP slice: MVP is defaults map + resolver + **Rex** (most
  tiers, most spend); remaining skills follow the established pattern.

### Outside this product's identity
- **Per-invocation complexity routing** — rejected (see Key Decisions).
- **Tier indirection** (`simple/medium/complex` → model): the Claude aliases are
  the tiers; no second vocabulary.
- **User-level config or precedence chains.**
- **Config validation tooling, schema versioning, env-var overrides** — missing or
  malformed means defaults; that is the whole error-handling story.

---

## Outstanding Questions

### Resolve Before Planning
- Hand-write the desired config for two real repos (Forked Up, plus the
  lowest-stakes side project). Identical files weaken the project-level premise;
  differing files fix the schema and key names from evidence. The file path + key
  schema is the hardest-to-undo decision — every install depends on it.

### Deferred to Planning
- Exact config file path/name and format (JSON vs YAML).
- Resolver implementation (bash vs node) and how skills invoke it
  (`${CLAUDE_PLUGIN_ROOT}`-relative).
- Whether frontmatter fallback values are generated from the canonical map or
  merely convention-checked (e.g. a CI lint).
- Whether/how a malformed-config warning is surfaced.

---

## Sources / Research

- Current hard-coded assignments: `frxnls/agents/*.md:5` (all `model: sonnet`);
  Rex finder tiers at `frxnls/agents/rex-code-reviewer.md:237-341`
  (docs=haiku, security=opus, simplicity/correctness/data-integrity=sonnet).
- Prior art: everyinc/compound-engineering-plugin's YAML model routing — the
  install-site-config idea is adopted; its dynamic complexity routing is not.
