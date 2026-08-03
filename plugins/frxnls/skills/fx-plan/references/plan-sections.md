# Plan Sections

What makes a great implementation plan, independent of length. The plan is a
**decision artifact** an implementer (the `plan-implementer` agent or a human) can
start from confidently — not a substitute for their own investigation. Markdown
only.

## The outcome

A great plan serves three readers:

- **The implementing agent** starts from an informed baseline — load-bearing
  decisions named, research breadcrumbs to orient, clear unit boundaries.
- **The reviewer** identifies the load-bearing decisions and the scope of the change
  in one pass.
- **The future reader** traces why the work was done and what shaped it.

Sections earn their place by serving one of these. Omit padding — a section filled
with placeholder prose is worse than an absent one.

## Decide whether a plan doc is warranted at all

**Bias toward writing one** — a thin plan for small work is mild ceremony; skipping
one that was warranted costs the implementer reinvented decisions and lost unit
boundaries. **Skip the doc only when ALL hold:** the work is atomic (one commit, no
unit boundaries), there are no design choices that constrain implementation (no
KTDs), scope is self-evident, and no upstream artifact needs traceability.

Stress-test "looks atomic" — many requests hide decisions. *"Add caching"* hides
TTL/invalidation/key-shape KTDs; *"migrate A→B"* hides semantic-difference KTDs;
*"add rate limiting"* hides algorithm/scope KTDs — write the plan. Genuine skips:
*"fix typo on line 47"*, *"rename `oldFn`→`newFn` repo-wide"*, *"bump dep to 2.3.1"*
(unless breaking). When skipping, hand straight to `fx-ship`/implementation and let
decisions land in the commit message or `docs/solutions/`.

## Hard floor

When a plan is warranted, these are present:

- **Summary** — what the plan proposes, 1-3 lines. Forward-looking.
- **Problem Frame** — why the work is being done. May merge into Summary when the
  motivation is one sentence.
- **Requirements** (stable R-IDs) — what must be true after the work ships. The
  reviewer's checklist; downstream code review verifies against these.
- **Key Technical Decisions** (KTDs) — the load-bearing choices that constrain
  implementation, each `<decision>: <rationale>`. Without these the implementer
  can't tell which choices are pinned vs open.
- **Implementation Units** (stable U-IDs) — discrete, independently landable units
  of work. The `plan-implementer` agent consumes these.

## Include when material

Present only when they carry information not covered elsewhere. The test is *"does
THIS plan have content this section would surface?"*

- **High-Level Technical Design** — when the approach has shape prose alone doesn't
  carry: architecture across components, sequencing across processes, state
  machines, branching gates. Mermaid diagrams live here. Skip for one-paragraph
  pattern application.
- **Scope Boundaries** — when scope is contested or non-goals are worth naming.
  Carries the `### Deferred to Follow-Up Work` subsection (tangential cleanups and
  scope-adjacent nice-to-haves go here, not into active units).
- **Open Questions** — when genuinely unresolved items block planning or
  implementation. No empty "none" section.
- **System-Wide Impact** — when the change touches cross-cutting concerns (data
  lifecycles, auth boundaries, RLS, performance posture, shared infra).
- **Risks & Dependencies** — real risks (external service changes, version pins
  under churn, behavioral assumptions) or material upstream dependencies.
- **Acceptance Examples** — when a requirement has a conditional shape ("When X, Y")
  the prose leaves ambiguous.
- **Documentation / Operational Notes** — when docs, monitoring, migration order, or
  rollout steps need explicit notes.
- **Sources / Research** — the breadcrumbs that orient the implementer or justify a
  load-bearing choice (code locations like `services/reports.ts:174-176`, external
  docs, prior plans, `docs/solutions/` learnings). Omit process exhaust (restating
  the prompt). Surface inline next to the KTD/unit it justifies, or as a section.

The catalog is a floor, not a ceiling — introduce a new section when content doesn't
fit. Content drives sections, not vice versa.

## Implementation Units

Each unit is a level-3 heading with a stable U-ID prefix: `### U1. [Name]`. Never
render units as `- [ ]` checkboxes or list items — flush-left per-unit fields break
CommonMark list continuation. Number sequentially from U1. Per unit, include:

- **Goal** — what it accomplishes.
- **Requirements** — which R-IDs (and A/F/AE IDs when an origin supplies them) it
  advances.
- **Dependencies** — what must exist first, cited by U-ID (e.g. "U1, U3").
- **Files** — repo-relative paths to create/modify/test (never absolute).
- **Approach** — key decisions, data flow, boundaries, integration notes.
- **Execution note** — optional; only for a non-default posture (test-first,
  characterization-first). Don't expand into RED/GREEN/REFACTOR substeps.
- **Patterns to follow** — existing code/conventions to mirror.
- **Test scenarios** — the specific cases to write, right-sized to the unit. Name
  input, action, and expected outcome so the implementer doesn't invent coverage.
  Cover every applicable category: happy path, edge cases, error/failure paths,
  integration (behaviors mocks won't prove). For a non-behavioral unit (pure config,
  scaffolding, styling) write `Test expectation: none — [reason]`. Feature-bearing
  units must have real scenarios, not the annotation.
- **Verification** — how the implementer knows it's done, as outcomes, not shell
  recipes.

Every feature-bearing unit lists its test file path in **Files**.

## Plan metadata (YAML frontmatter)

Stable field names downstream tooling depends on — never rename or repurpose:

- **`title`** (required) — verbatim, matches the H1.
- **`type`** (required) — conventional-commit prefix: `feat`, `fix`, `refactor`,
  `chore`, `docs`, `perf`, `test`.
- **`status`** (required) — `active` on creation; an implementer flips it to
  `completed` on ship. The resume fast path keys on `active`.
- **`date`** (required) — ISO 8601 `YYYY-MM-DD`, ASCII digits.
- **`origin`** (optional) — repo-relative path to an upstream brainstorm/requirements
  doc, when one exists. Carried for traceability.
- **`deepened`** (optional) — ISO date marking the first substantive confidence pass.

## ID and content rules

- **Stable IDs** — R-IDs, U-IDs (and A/F/AE when they fire). Never renumber to
  "clean up gaps" — gaps from deletions are fine; reordering preserves IDs in their
  new order; splitting keeps the original ID and takes the next unused number.
- **Plain prefix** — `R1.`, `U1.`; do not bold the prefix.
- **Repo-relative paths** — always. State a `**Target repo:**` once at the top if the
  plan targets a different repo, then use repo-relative paths throughout.
- **No implementation code** — no imports, exact signatures, or framework syntax.
  Pseudo-code/DSL grammars are allowed in HTD and per-unit technical-design fields,
  framed as directional guidance.
- **No process exhaust** — no "captured at Phase X" notes, no `## Next Steps`
  pointing at the next skill, no provenance lines. Process metadata belongs in commit
  messages and tool output, not the artifact.
- **Group Requirements by concern** when they span distinct logical areas (by
  capability, not discussion order); R-IDs stay continuous across groups.
- **Horizontal rules (`---`) between top-level sections** in Standard/Deep plans for
  scannability; omit for Lightweight plans that fit one screen.
- **Mermaid** is encouraged where it clarifies relationships prose can't (ERDs for
  data-model changes, sequence diagrams for multi-service flows, state diagrams for
  lifecycles).
