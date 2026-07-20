---
name: fx-plan
description: Turn a feature idea, brainstorm doc, GitHub issue, or rough description into a durable, implementation-ready plan under docs/plans/ — researched, broken into ID'd units with test scenarios, and confidence-checked. Also deepens an existing plan ("deepen the plan"). Use when the user says "plan this", "create a plan", "how should we build", "break this down", or a brainstorm is ready for planning. This is the HOW step: fx-brainstorm defines WHAT, fx-plan defines HOW, fx-ship executes it to a PR. Plans, never codes.
argument-hint: "[optional: feature description, requirements doc path, or plan path to deepen]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
---

# /fx-plan: idea → researched, implementation-ready plan

`fx-brainstorm` defines **WHAT** to build. `fx-plan` defines **HOW**. `fx-ship`
executes the plan to a reviewed PR. A prior brainstorm is useful context but never
required — `fx-plan` works from any input: a requirements doc, a GitHub issue, a
feature idea, or a rough description.

```
idea ─▶ fx-brainstorm ─▶ fx-plan ─▶ fx-ship ─▶ plan-implementer ─▶ PR
        (WHAT)            (HOW)      (orchestrate)  (execute)
                             │
                  reads docs/solutions/ learnings & docs/brainstorms/ to plan informed
```

This produces a **decision artifact** — it does not implement code, run tests, or
learn from execution-time results. If the answer depends on changing code and seeing
what happens, that's `fx-ship`/implementation, not here. **When directly invoked,
always plan** — never classify a direct invocation as "not a planning task" and
abandon. If the input is unclear, ask one or two questions or run the bootstrap, but
stay in the workflow.

Adapted from EveryInc's compound-engineering `ce-plan`, trimmed to markdown-only
output and this stack's research agents (no `output:html`, `ce-proof`,
`ce-doc-review`, or config file).

## Interaction

Ask via `AskUserQuestion` (load its schema with `ToolSearch` → `select:AskUserQuestion`
first if needed); fall back to numbered chat options only if unavailable. One
question at a time; prefer single-select. Never silently skip a question.

## Core principles

1. **Requirements are the source of truth** — if a brainstorm/requirements doc
   exists, build from it rather than re-inventing behavior.
2. **Decisions, not code** — capture approach, boundaries, files, dependencies,
   risks, test scenarios. Pseudo-code sketches are fine as *directional* guidance.
3. **Research before structuring** — explore the codebase and prior learnings (and,
   when warranted, external sources) before finalizing.
4. **Right-size the artifact** — small work gets a compact plan; large work gets more
   structure. Same philosophy at every depth.
5. **Separate planning from execution discovery** — resolve planning-time questions
   here; explicitly defer execution-time unknowns to implementation.
6. **Honor named resources** — when the user names a CLI, URL, file, or prior
   artifact, treat it as authoritative; discover it before assuming it's unavailable.
7. **Repo-relative paths everywhere** — never absolute paths (they break portability
   across machines, worktrees, teammates).

## Plan quality bar

A plan is ready when the `plan-implementer` agent (or a human) can start confidently
without the plan having to write the code for them: a clear problem frame and scope;
requirements traced to the request/origin; repo-relative file paths and explicit
test-file paths for feature-bearing units; decisions with rationale; existing
patterns to follow; enumerated test scenarios per unit; clear dependencies and
sequencing.

---

## Workflow

### Phase 0 — Source and scope

**0.1 Resume / deepen fast path.** If the user references an existing plan in
`docs/plans/` (or says "deepen the plan"/"deepening pass"), read it. "Deepen" targets
a **plan**, not a brainstorm. For a complete plan (`status: active`, units defined),
short-circuit to **Phase 5 (Confidence Check) in interactive mode** — don't re-run
the whole workflow. Normal edits ("update the test scenarios", "add a unit") follow
the standard resume flow, not the fast path. Bare words like "strengthen"/"gaps"
aren't deepening intent unless they target the plan as a whole.

**0.2 Is this a software implementation plan?** If the task asks to build, modify,
refactor, deploy, or architect software, continue. If it's answer-seeking
("how does X compare?", "how often does Y happen?") — that's research, not an
implementation plan; tell the user and stop (or answer directly). If genuinely
ambiguous, ask.

**0.3 Find the upstream brainstorm.** Search `docs/brainstorms/` for
`*-requirements.md` matching the feature (topic match, recent, same problem/scope).
If multiple match, ask which. If one is relevant, read it thoroughly, announce it as
the `origin:`, and carry forward everything — problem frame, requirements, scope
boundaries (including deferred/out-of-scope), key decisions, dependencies, and open
questions (preserving blocking vs deferred). Reference carried decisions with
`(see origin: <path>)`. Don't silently drop origin content.

**0.4 Bootstrap (no doc / unclear input).** If no relevant requirements doc exists or
the input needs structure: if it's already clear enough, continue. If the ambiguity
is product framing/scope, suggest `fx-brainstorm` — but offer to continue here. If
continuing, briefly establish problem frame, intended behavior, scope boundaries /
non-goals, success criteria, and blocking assumptions. Keep it brief. If it surfaces
a **bug** with a reachable surface, offer to route to implementation directly; if a
**clear, ready task**, suggest `fx-ship` as a faster path. The user decides.

**0.5 Assess depth.** **Lightweight** (small, bounded, low ambiguity) · **Standard**
(normal feature / bounded refactor with decisions to document) · **Deep**
(cross-cutting, strategic, high-risk, or highly ambiguous). Ask one question if
unclear.

**0.6 Confirm scope before spending research.** Before dispatching research, state
the scope you're about to plan against — what it targets, what it won't — at
affirm-or-redirect level (a scope claim, **not** an enumeration of units or file
paths). Surface any **call-outs**: specific forks where the user's input materially
changes the plan. For Standard/Deep plans, or any tier with a surviving call-out,
wait for confirmation. For a Lightweight plan with zero call-outs, announce and
proceed ("Interrupt if I have the scope wrong"). The user can redirect to
`fx-brainstorm` here if it's bigger than they thought.

### Phase 1 — Research

**1.1 Local (always).** Prepare a 1-2 paragraph planning-context summary (from the
origin doc, or the feature description). Dispatch in parallel via the `Agent` tool:

- **`fx-repo-research`** — scope `technology, architecture, patterns`, plus the
  context summary. Returns stack/versions, conventions, patterns and the files/tests
  this work touches, and whether local patterns are **strong / thin / absent**.
- **`fx-learnings-research`** — the context summary. Returns relevant
  `docs/solutions/` learnings, refresh candidates, domain vocabulary from
  `CONCEPTS.md`, and related issues.

**Resolve the model before dispatch.** Resolve via `python3 "<skill-base>/../../scripts/resolve-model.py" <agent-name>` (skills know their injected base directory), pass the result as the Agent tool's `model` parameter, and mention it in the dispatch announcement. If the resolver script is missing or errors, omit `model` — the agent's frontmatter default applies.

If `CONCEPTS.md` exists, plan in its vocabulary.

**1.2 Decide on external research.** An **explicit** request (or origin doc asking
for it) — "what should we borrow", "best practices", "official docs", "alternatives
to", a competitor scan, or a named external technology — makes external research
**required** (honor an explicit opt-out). Otherwise lean toward it when: the topic is
high-risk (security, payments, privacy, migrations, external APIs); local patterns
are **thin or absent** (per `fx-repo-research`); or the plan depends on an unsettled
external option set (which library/provider/approach). **Skip** it when local
patterns are strong, the user already knows the shape, or it would add little. When
running it, dispatch a generic `Agent` (general-purpose) web search with the exact
frameworks/versions from `fx-repo-research` and a focused question. Announce the
decision in one line. If web tools are unavailable, say so and carry the gap into the
plan honestly.

**1.3 Consolidate.** Summarize relevant patterns and file paths, prior learnings,
external findings, related issues, and constraints that shape the plan. **Land
external findings in decisions** (a KTD, Alternative, Risk, or Sources section) — not
an appendix. If a finding shaped nothing, drop it. Note an internal flag if external
research was load-bearing (Phase 5 reads it).

**1.4 Flow analysis (Standard/Deep).** For non-trivial plans, think through user
flows and edge cases — missing state transitions, handoff gaps, failure paths — and
fold only the details that materially improve the plan.

### Phase 2 — Resolve planning questions

Build a question list from origin deferred questions, research gaps, and decisions
needed to produce a useful plan. For each, decide: **resolve during planning** (the
answer is knowable from repo context, docs, or a user choice) or **defer to
implementation** (depends on code changes or runtime behavior). Ask the user only
when the answer materially affects architecture, scope, sequencing, or risk and can't
be responsibly inferred. **Do not** run tests or probe runtime behavior — the goal is
a strong plan, not partial execution.

### Phase 3 — Structure

**Title & filename.** Conventional title (`feat: Add reservation reminders`); type
`feat`/`fix`/`refactor`. Filename:
`docs/plans/YYYY-MM-DD-NNN-<type>-<descriptive-name>-plan.md` — `mkdir -p docs/plans/`
if needed; `NNN` is the next zero-padded sequence for today (count existing files);
keep the name 3-5 kebab-cased words.

**Break into Implementation Units.** Each is one meaningful change an implementer
could land as an atomic commit — focused on one component/seam, a small cluster of
related files, dependency-ordered, concrete without pre-writing code. Avoid 2-5
minute micro-steps and units that span unrelated concerns. Assign stable U-IDs
(`U1`, `U2`, …). See `references/plan-sections.md` for the full per-unit field list
and the section catalog.

**High-Level Technical Design** — include when the approach has shape prose can't
carry (architecture across components, sequencing, state machines, branching gates);
pick the medium (component diagram, sequence, flowchart, state machine, decision
matrix). Skip for one-paragraph pattern application.

**Anti-expansion.** Tangential cleanups, "while we're here" refactors, and
scope-adjacent nice-to-haves go to `### Deferred to Follow-Up Work` under Scope
Boundaries — not active units. The user's explicit ask overrides this.

### Phase 4 — Write the plan

**NEVER CODE during this skill.** Research, decide, write. Compose using
`references/plan-sections.md` (the section contract — hard floor + include-when-
material catalog + ID rules + metadata fields). One philosophy across depths; change
the amount of detail, not the planning/execution boundary:

- **Lightweight** — compact; usually 2-4 units; omit low-value optional sections.
- **Standard** — full core template (omit HTD etc. when they add nothing); 3-6 units.
- **Deep** — full template plus warranted analysis sections (Alternatives Considered,
  Risk Analysis, Phased Delivery, Operational Notes); 4-8 units, phased if it helps.

**Write the file to disk** (`Write`) before presenting any options, then confirm with
its absolute path so it's clickable. If `CONCEPTS.md` exists and the plan uses a
domain term missing from it, add the entry silently (glossary terms only — not file
paths or class names; creation is owned by `fx-compound`).

### Phase 5 — Confidence check, deepening, and handoff

After writing, evaluate whether the plan needs strengthening. Build a risk profile
(auth, payments, migrations/RLS, external APIs, privacy, cross-surface parity,
significant rollout). **Gate:** Lightweight plans usually skip unless high-risk;
Standard plans benefit when a section looks thin; Deep/high-risk plans usually get a
targeted pass; always score when local grounding was thin or external research was
load-bearing. If it's already well-grounded, report "Confidence check passed" and go
to handoff. Otherwise **read `references/deepening.md`** and run the scoring →
targeted-research → synthesis pass (auto mode during generation; interactive mode on
the re-deepen fast path).

**Handoff.** Present `AskUserQuestion`: "Plan ready at `<absolute path>`. What next?"

- **Ship it** (recommended) — invoke `/frxnls:fx-ship` with the plan path so it sets
  up the workspace, routes to the right implementer, runs QA, and surfaces Rex's
  review. Fire it, don't just suggest it.
- **Create an issue** — create a tracked GitHub issue from the plan (`gh`), show the
  URL, then offer to ship.
- **Deepen further** — run another interactive confidence pass.
- **Done** — the plan is saved; stop.

Act on the selection — don't just announce it. This skill isn't complete until the
plan file is written and the chosen handoff action has fired.

**Headless / batch** (invoked by an `fx-ship` batch run or any non-interactive
context): skip the interactive gates — make reasonable scope/question calls, write
the plan, run the confidence check in auto mode, and return the plan path to the
caller without the handoff menu.

## Composes with

- [`fx-brainstorm`](../fx-brainstorm/SKILL.md) — upstream: defines WHAT to build; its
  `*-requirements.md` becomes this plan's `origin:`.
- [`fx-ship`](../fx-ship/SKILL.md) — downstream: takes the plan to a reviewed PR.
- [`fx-compound`](../fx-compound/SKILL.md) — fills `docs/solutions/`, which
  `fx-learnings-research` mines to ground this plan.
- `fx-repo-research` / `fx-learnings-research` — the read-only research agents this
  skill dispatches.
