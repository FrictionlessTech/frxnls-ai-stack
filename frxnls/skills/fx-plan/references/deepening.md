# Deepening Workflow

The confidence-check execution path. Load it only when the gate in the SKILL
(Phase 5) decides the plan is worth strengthening. Distilled from EveryInc's
`ce-plan` deepening workflow and retargeted to frxnls's two research agents.

## Two modes

- **Auto** (default during generation) — runs without asking; findings are
  synthesized straight into the plan; the user sees what's being strengthened.
- **Interactive** (the re-deepen fast path, when the user said "deepen the plan") —
  each agent's findings are presented for accept / reject / discuss before
  integration. Only accepted findings land.

Headless/pipeline runs always use auto.

## 1 — Score confidence gaps

For each section compute: **trigger count** (checklist hits below) + **risk bonus**
(+1 if the topic is high-risk and the section is materially relevant) +
**critical-section bonus** (+1 for KTDs, Implementation Units, System-Wide Impact,
Risks & Dependencies, or Open Questions in Standard/Deep plans).

A section is a candidate if it hits **2+ points**, or **1+ point** in a high-risk
domain where it's materially important. Pick only the **top 2-5** by score (cap 1-2
for a Lightweight high-risk plan). Don't deepen everything.

### Section checklists (trigger = the statement is true)

**Requirements** — vague or disconnected from units; success criteria missing or not
reflected downstream; units don't clearly advance traced requirements; origin
requirements/IDs not carried forward.

**Context & Research / Sources** — repo patterns named but never used in decisions;
cited learnings/references don't shape the plan; high-risk work lacks grounding;
research is generic instead of tied to this repo.

**Key Technical Decisions** — a decision stated without rationale; rationale omits
tradeoffs or rejected alternatives; decision doesn't connect to scope/requirements;
an obvious design fork the plan never addresses.

**Open Questions** — product blockers hidden as assumptions; planning-owned questions
wrongly deferred to implementation; resolved questions with no basis in
repo/research; deferred items too vague to be useful later.

**High-Level Technical Design** — present: wrong medium, contains implementation
code, weak/missing non-prescriptive framing, doesn't connect to KTDs/units. Absent
(Standard/Deep): the work involves DSL/API-surface design, multi-component
integration, complex data flow, or a state-heavy lifecycle and a sketch would make
the KTDs easier to validate.

**Implementation Units / Verification** — dependency order unclear or wrong; file or
test-file paths missing where they should be explicit; units too large/vague or
broken into micro-steps; approach notes thin or don't name a pattern; test scenarios
vague (no input/expected outcome) or skip applicable categories (no error paths for
a unit with failure modes; no integration scenarios for a cross-layer unit);
feature-bearing units with blank scenarios; verification not expressed as observable
outcomes; **existing U-IDs renumbered** after a reorder/split/delete (never allowed).

**System-Wide Impact** — affected interfaces/callbacks/entry points/parity surfaces
missing; failure propagation underexplored; state lifecycle, caching, RLS, or data
integrity risks absent where relevant.

**Risks & Dependencies / Operational Notes** — risks listed without mitigation;
rollout/monitoring/migration implications missing when warranted; external
dependency assumptions weak; security, privacy, performance, or data risks absent
where they obviously apply.

Use the plan's own Context/Sources as evidence: if it cites a pattern, learning, or
risk that never affects a decision, unit, or verification, that's a gap.

## 2 — Report and dispatch targeted research

Announce first: `Strengthening [sections] — [brief reason each]`.

Per selected section, dispatch the **smallest** useful agent set (1-3 per section,
~6 total max) via the `Agent` tool, in parallel. Map by section:

| Section | Agent(s) |
|---------|----------|
| Requirements / Open Questions / Implementation Units / Verification | `fx-repo-research` (scope `patterns`) — concrete file/test targets, sequencing clues, patterns to follow |
| Context & Research / Sources | `fx-learnings-research` for past solved problems & conventions; a generic `Agent` web search for official framework/library behavior or current best practices when the gap is external |
| Key Technical Decisions / High-Level Technical Design | `fx-repo-research` (scope `architecture, patterns`) to ground the design in existing repo conventions; add a generic web `Agent` only when the decision needs external grounding |
| System-Wide Impact / Risks (security, data, performance) | `fx-repo-research` for cross-boundary effects and interface surfaces; a generic `Agent` with a focused security / data-integrity / performance lens when the risk is real and repo evidence is thin |

Prefer local repo and `docs/solutions/` evidence first; reach external only when the
gap can't be closed responsibly from repo context. Give each agent: a short plan
summary, the exact section text, which triggers fired, the depth/risk profile, and
one specific question. Instruct: findings only, no implementation code, no shell
commands.

## 3 — Interactive review (interactive mode only)

Present each agent's findings one section at a time and ask accept / reject /
discuss via `AskUserQuestion`. On "discuss", talk it through, then re-ask
accept/reject only. Carry forward only accepted findings. If none accepted: report
"No findings accepted — plan unchanged" and go straight to handoff (skip synthesis).

## 4 — Synthesize

Strengthen **only** the selected sections; keep the plan coherent. Allowed: clarify
decision rationale; tighten requirements trace; reorder or split units when
sequencing is weak (**never renumber existing U-IDs**); add missing pattern
references, file/test paths, or verification outcomes; expand system-wide impact /
risk / rollout treatment; reclassify open questions between resolved and deferred;
add or strengthen an HTD sketch; set/refresh `deepened: YYYY-MM-DD`.

Do **not**: add implementation code or shell recipes; sprinkle generic "Research
Insights" subsections; rewrite the whole plan; invent new product requirements or
scope without surfacing them; renumber U-IDs while "tidying". If research reveals a
product-level ambiguity that should change behavior or scope, don't decide it here —
record it under Open Questions and recommend `fx-brainstorm` if it's product-defining.
