---
name: fx-debug
description: 'Systematically find root causes and fix bugs. Use when debugging errors, investigating test failures, reproducing bugs from issue trackers (GitHub, Linear, Jira), or when stuck on a problem after failed fix attempts. Also use when the user says "debug this", "why is this failing", "fix this bug", "trace this error", or pastes stack traces, error messages, or issue references. Investigates before fixing; checks docs/solutions/ first so a documented bug is a lookup, not a re-investigation.'
argument-hint: "[issue reference, error message, test path, or description of broken behavior]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - WebFetch
---

# /fx-debug: find the root cause, then fix it

Find root causes, then fix them. This skill investigates bugs systematically —
tracing the full causal chain before proposing a fix — and optionally implements the
fix with test-first discipline.

<bug_description> #$ARGUMENTS </bug_description>

Adapted from EveryInc's compound-engineering `ce-debug`, retargeted to the frxnls
stack: it checks `docs/solutions/` first (the store `fx-compound` fills), drives web
repro through the Playwright MCP / `fx-qa-web` and iOS through serve-sim /
`fx-qa-mobile-ios`, and hands a fixed branch off via `gh` + `fx-compound` rather than
the ce-only commit/brainstorm ecosystem.

## Core Principles

1. **Investigate before fixing.** Do not propose a fix until you can explain the full
   causal chain from trigger to symptom with no gaps. "Somehow X leads to Y" is a gap.
2. **Predictions for uncertain links.** When the causal chain has uncertain or
   non-obvious links, form a prediction — something in a different code path or
   scenario that must also be true. If the prediction is wrong but a fix "works," you
   found a symptom, not the cause. When the chain is obvious (missing import, clear
   null reference), the chain explanation itself is sufficient.
3. **One change at a time.** Test one hypothesis, change one thing. If you're changing
   multiple things to "see if it helps," stop — that is shotgun debugging.
4. **When stuck, diagnose why — don't just try harder.**

## Execution Flow

| Phase | Name | Purpose |
|-------|------|---------|
| 0 | Triage | Parse input, fetch issue if referenced, **check `docs/solutions/`**, proceed to investigation |
| 1 | Investigate | Reproduce the bug, trace the code path |
| 2 | Root Cause | Form hypotheses with predictions for uncertain links, test them, **causal chain gate**, smart escalation |
| 3 | Fix | Only if the user chose to fix. Test-first fix with workspace safety checks |
| 4 | Handoff | Structured summary, then prompt the user for the next action |

Beyond the trivial-bug fast-path in Phase 0, no further phase skipping — complex bugs
simply spend more time in each phase naturally. No further complexity tiers.

## Interaction

When asking the user anything, use `AskUserQuestion` (load its schema via `ToolSearch`
with `select:AskUserQuestion` first if it isn't loaded — a pending schema load is not a
reason to fall back). Fall back to numbered options in chat only if the tool errors.
Never silently skip a blocking question.

---

### Phase 0: Triage

Parse the input and reach a clear problem statement.

**If the input references an issue tracker**, fetch it:
- GitHub (`#123`, `org/repo#123`, github.com URL): parse the reference from
  `<bug_description>` and fetch with `gh issue view <number> --json title,body,comments,labels`.
  For URLs, pass the URL directly to `gh`.
- Other trackers (Linear, Jira, any tracker URL): attempt to fetch via an available
  MCP tool or `WebFetch`. If the fetch fails — auth, missing tool, non-public page —
  ask the user to paste the relevant issue content. Ensure the fetch includes the full
  comment thread, not just the opening description.

Read the full thread — the original description AND every comment, with particular
attention to the latest ones. Comments frequently contain updated reproduction steps,
narrowed scope, prior failed attempts, additional stack traces, or a pivot to a
different suspected root cause; treating the opening post as the whole picture often
sends the investigation in the wrong direction. Extract reported symptoms, expected
behavior, reproduction steps, and environment details from the combined thread.

**Everything else** (stack traces, test paths, error messages, descriptions of broken
behavior): the problem statement is the input itself.

**Check `docs/solutions/` first — this is the compounding payoff.** Before
investigating, see whether this bug (or its root-cause pattern) is already documented.
The whole point of `fx-compound` filling that store is that the *next* occurrence is a
lookup, not a re-investigation. Two ways, by depth:
- **Quick:** `grep`/`Glob` `docs/solutions/` and `CONCEPTS.md` for the error string,
  symptom, or affected component.
- **Thorough** (the bug looks non-trivial or familiar): dispatch the
  **`fx-learnings-research`** agent with the problem context; it searches
  `docs/solutions/`, `CONCEPTS.md`, git history, and related issues and returns matches.

If a documented learning matches, read it — apply its known fix/diagnosis directly and
jump toward Phase 3/4, confirming it still reproduces and that the fix still applies
(stale docs reflect what was true when written). If it's a near-miss, carry it as a
ranked hypothesis into Phase 2. If nothing matches, proceed normally — and this becomes
a strong `fx-compound` candidate at the end.

**Trivial-bug fast-path:** Once the problem is clear, decide whether the framework is
needed at all. If the cause is immediately readable from the input (single-file typo,
missing import, obvious null deref or off-by-one with a one-line fix) and verification
doesn't require deep tracing, present the cause and the proposed one-line fix and run
Phase 2's **Fix it now / Diagnosis only** user-choice gate before editing — the
fast-path saves investigation ceremony, not the user's choice over whether to apply a
fix. If the user picks fix, run Phase 3's **Workspace and branch check**, apply the
fix, leave a one-line note explaining the cause, and skip to Phase 4's structured
summary. If diagnosis only, write the summary and stop. When in doubt, run the full
framework; getting the wrong root cause costs more than the few minutes of ceremony.

**Otherwise**, proceed to Phase 1.

**Questions:**
- Do not ask questions by default — investigate first (read code, run tests, trace errors).
- Only ask when a genuine ambiguity blocks investigation and cannot be resolved by
  reading code or running tests.
- When asking, ask one specific question.

**Prior-attempt awareness:** If the user indicates prior failed attempts ("I've been
trying", "keeps failing", "stuck"), ask what they have already tried before
investigating. This avoids repeating failed approaches and is one of the few cases
where asking first is the right call.

---

### Phase 1: Investigate

#### 1.1 Reproduce the bug

Confirm the bug exists and understand its behavior. Run the test, trigger the error,
follow reported reproduction steps — whatever matches the input.

- **Web bugs:** drive a real browser via the **Playwright MCP server** (the same tool
  `fx-qa-web` uses) — navigate, snapshot the accessibility tree, interact, read console
  and network. If the app isn't running, start the project's dev server first.
- **iOS / Expo bugs:** drive the Simulator via **serve-sim** (the tool
  `fx-qa-mobile-ios` uses); boot the app with **`fx-expo-worktree-dev`** if it isn't
  already on a sim, then reproduce against the accessibility tree + device logs.
- **Manual setup required:** if reproduction needs conditions the agent cannot create
  alone (data states, user roles, external services, env config), document the exact
  setup steps and guide the user through them. Clear step-by-step instructions save
  significant time even when the process is fully manual.
- **Does not reproduce after 2-3 attempts:** read `references/investigation-techniques.md`
  for intermittent-bug techniques.
- **Cannot reproduce at all in this environment:** document what was tried and what
  conditions appear to be missing.
- **Writing the reproduction test:** if the project has testing-conventions guidance — a
  dedicated testing skill, an `AGENTS.md`/`CLAUDE.md` testing section, or a clear style
  across existing tests — apply it. Otherwise write a minimal isolated test that fails
  on the current bug and passes once the corrected behavior lands; name it descriptively
  so the failure message itself explains the bug.

#### 1.2 Verify environment sanity

Before deep code tracing, confirm the environment is what you think it is:

- Correct branch checked out; no unintended uncommitted changes
- Dependencies installed and up to date (`bun install`, `npm install`, etc.) — stale
  `node_modules` is a frequent false lead
- Expected interpreter or runtime version (check `.tool-versions`, `.nvmrc`, etc.
  against what's actually active)
- Required env vars present and non-empty
- No stale build artifacts (`dist/`, `.next/`, prebuilt native binaries from an earlier branch)
- Dependent local services (database, cache, queue) running at expected versions *when
  the bug plausibly involves them*

#### 1.3 Trace the code path

Trace data flow backward from the symptom to where valid state first became invalid.
Read code-shape to form a hypothesis, then verify with observed values — do not theorize
from code alone.

Concrete recipe:

1. Read the stack trace bottom-to-top, opening each frame's source. The bottom frame is
   the symptom; the root cause is somewhere upstream.
2. Identify the first frame where the input data is already invalid — that's the upper
   bound on where to look.
3. Instrument the boundaries around that frame: targeted log/print statements, debugger
   breakpoints, or test assertions that capture *actual* values at function entry/exit.
   Assumed values lie; observed values don't.
4. Walk the boundaries until valid input becomes invalid output. That transition is the
   root cause site.

Do not stop at the first function that looks wrong — the root cause is where bad state
originates, not where it is first observed.

As you trace:
- Check recent changes in files you are reading: `git log --oneline -10 -- [file]`
- If the bug looks like a regression ("it worked before"), use `git bisect` (see
  `references/investigation-techniques.md`)
- Check the project's observability tools for additional evidence:
  - Error trackers (Sentry, AppSignal, Datadog, BetterStack, Bugsnag)
  - Application logs; browser console; Simulator device logs
  - Database state (Supabase / Postgres)
- Each project has different systems available; use whatever gives a more complete picture.

---

### Phase 2: Root Cause

*Reminder: investigate before fixing. Do not propose a fix until you can explain the
full causal chain from trigger to symptom with no gaps.*

Read `references/anti-patterns.md` before forming hypotheses. As a load-time preview of
the rationalizations it covers, stop and re-examine if the internal monologue contains
any of these:

- "Quick fix for now, investigate later"
- "This should work" (without a tested prediction)
- "Let me just try..." (without a hypothesis)

These phrases mark mode-drift toward symptom patches, not progress on the root cause.

**Assumption audit (before hypothesis formation):** List the concrete "this must be
true" beliefs your understanding depends on — the framework behaves as expected here,
this function returns what its name implies, the config loads before this runs, the
caller passes a non-null value, the database is in the state the test implies. For each,
mark *verified* (you read the code, checked state, or ran it) or *assumed*. Assumptions
are the most common source of stuck debugging. Many "wrong hypotheses" are actually
correct hypotheses tested against a wrong assumption.

**Form hypotheses** ranked by likelihood. For each, state:
- What is wrong and where (file:line)
- **At least one concrete observation that supports it** — a runtime variable value, a
  log line, an instrumented boundary capture, a behavior delta against a working
  comparison case, or a specific code reference. "X seems off" is not evidence; "X
  equals null at line 42 because Y was never initialized in the constructor path that
  runs under condition Z" is. Hypotheses without grounding observations are theorizing —
  go back to Phase 1 and instrument.
- The causal chain: how the trigger leads to the observed symptom, step by step
- **For uncertain links in the chain**: a prediction — something in a different code
  path or scenario that must also be true if this link is correct

When the causal chain is obvious and has no uncertain links (missing import, clear type
error, explicit null dereference), the chain explanation itself is the gate — no
prediction required. Predictions are a tool for testing uncertain links, not a ritual
for every hypothesis.

Before forming a new hypothesis, review what has already been ruled out and why.

**Causal chain gate:** Do not proceed to Phase 3 until you can explain the full causal
chain — from the original trigger through every step to the observed symptom — with no
gaps. The user can explicitly authorize proceeding with the best-available hypothesis if
investigation is stuck.

*Reminder: if a prediction was wrong but the fix appears to work, you found a symptom.
The real cause is still active.*

#### Present findings

Once the root cause is confirmed, present:
- The root cause (causal chain summary with file:line references)
- The proposed fix and which files would change
- Which tests to add or modify to prevent recurrence (specific test file, test case
  description, what the assertion should verify)
- Whether existing tests should have caught this and why they did not

Then offer next steps via `AskUserQuestion`. Do not assume the user wants action right
now. The test recommendations are part of the diagnosis regardless of which path is
chosen. Options to offer:

1. **Fix it now** — proceed to Phase 3
2. **Diagnosis only — I'll take it from here** — skip the fix, proceed to Phase 4's
   summary, and end the skill
3. **Rethink the design** (`/frxnls:fx-brainstorm`) — only when the root cause reveals a
   design problem (see below)

**When to suggest brainstorm:** Only when investigation reveals the bug cannot be
properly fixed within the current design — the design itself needs to change. Concrete
signals observable during debugging:

- **The root cause is a wrong responsibility or interface**, not wrong logic. The module
  should not be doing this at all, or the boundary between components is in the wrong
  place. (Observable: the fix requires moving responsibility between modules, not
  correcting code within one.)
- **The requirements are wrong or incomplete.** The system behaves as designed, but the
  design does not match what users actually need. The "bug" is really a product gap.
  (Observable: the code is doing exactly what it was written to do — the spec is the
  problem.)
- **Every fix is a workaround.** You can patch the symptom but cannot articulate a clean
  fix because the surrounding code was built on an assumption that no longer holds.
  (Observable: you keep wanting to add special cases or flags rather than a direct
  correction.)

Do not suggest brainstorm for bugs that are large but have a clear fix — size alone does
not make something a design problem.

#### Smart escalation

If 2-3 hypotheses are exhausted without confirmation, diagnose why:

| Pattern | Diagnosis | Next move |
|---------|-----------|-----------|
| Hypotheses point to different subsystems | Architecture/design problem, not a localized bug | Present findings, suggest `/frxnls:fx-brainstorm` |
| Evidence contradicts itself | Wrong mental model of the code | Step back, re-read the code path without assumptions |
| Works locally, fails in CI/prod | Environment problem | Focus on env differences, config, dependencies, timing |
| Fix works but prediction was wrong | Symptom fix, not root cause | The real cause is still active — keep investigating |

**Parallel investigation option:** When hypotheses are evidence-bottlenecked across
clearly independent subsystems, dispatch read-only sub-agents via the `Agent` tool in
parallel, each with an explicit hypothesis and a structured evidence-return format. No
code edits by sub-agents, and skip this when hypotheses depend on each other's outcomes.

Present the diagnosis to the user before proceeding.

---

### Phase 3: Fix

*Reminder: one change at a time. If you are changing multiple things, stop.*

If the user chose "Diagnosis only" at the end of Phase 2, skip this phase and go straight
to Phase 4 for the summary. If they chose "Rethink the design", control transfers to
`/frxnls:fx-brainstorm` and this skill ends.

**Workspace and branch check:** Before editing files:

- Check for uncommitted changes (`git status`). If the user has unstaged work in files
  that need modification, confirm before editing — do not overwrite in-progress changes.
- If the current branch is the default branch, ask (via `AskUserQuestion`) whether to
  create a feature branch first. To detect the default branch, compare against `main`,
  `master`, or `git rev-parse --abbrev-ref origin/HEAD` with its `origin/` prefix
  stripped (the raw output is `origin/<name>`, so an unstripped comparison never
  matches). Default to creating one; derive a name from the bug
  (`claude/fix-<slug>`) and run `git checkout -b <name>`. On any other branch, proceed.

**Test-first:**
1. Write a failing test that captures the bug (or use the existing failing test)
2. Verify it fails for the right reason — the root cause, not unrelated setup
3. Implement the minimal fix — address the root cause and nothing else. Do not bundle
   drive-by refactors, formatting, or unrelated cleanup into a bug-fix change; those
   belong in separate commits.
4. Verify the test passes
5. Run the broader test suite for regressions
6. Self-review the diff before declaring the fix done: read every changed line and check
   for style violations, missed edge cases, regressions in adjacent behavior, and missing
   test coverage. For non-trivial fixes (multiple files, risky surface area), also run
   the lightweight `/code-review` — not the full `frxnls:rex-code-reviewer` PR-tier flow,
   which is over-sized for a single bug fix.

**On a failed fix:** return to Phase 2 and *explicitly invalidate the current hypothesis*
before forming a new one. State out loud what evidence ruled out the prior hypothesis,
then form a new one with its own grounding observation and prediction. Do not retry
variants of the same theory ("maybe it was the other branch", "let me also catch this
case") — that is the rationalization spiral, not iteration.

**3 failed fix attempts = smart escalation.** Diagnose using the same table from Phase 2.
If fixes keep failing, the root cause identification was likely wrong. Return to Phase 2.

**Conditional defense-in-depth** (trigger: grep for the root-cause pattern found it in 3+
other files, OR the bug would have been catastrophic if it reached production): read
`references/defense-in-depth.md` for the four-layer model (entry validation, invariant
check, environment guard, diagnostic breadcrumb) and choose which layers apply. Skip when
the root cause is a one-off error with no realistic recurrence path.

**Conditional post-mortem** (trigger: the bug was in production, OR the pattern appears in
3+ locations): analyze how this was introduced and what allowed it to survive. Note any
systemic gap or repeated pattern found — it informs Phase 4's decision on whether to offer
learning capture.

---

### Phase 4: Handoff

**Structured summary** — always write this first:

```
## Debug Summary
**Problem**: [What was broken]
**Root Cause**: [Full causal chain, with file:line references]
**Recommended Tests**: [Tests to add/modify to prevent recurrence, with specific file and assertion guidance]
**Fix**: [What was changed — or "diagnosis only" if Phase 3 was skipped]
**Prevention**: [Test coverage added; defense-in-depth if applicable]
**Prior learning**: [docs/solutions/ doc this matched, or "none found — capture candidate"]
**Confidence**: [High/Medium/Low]
```

**If Phase 3 was skipped** (user chose "Diagnosis only" in Phase 2), stop after the
summary — the user already told you they were taking it from here. Do not prompt.

**If Phase 3 ran**, the next move depends on whether the skill created the branch in
Phase 3. Ask via `AskUserQuestion` (don't end the phase without a response); the option
set differs by case:

#### Skill-owned branch (created in Phase 3): default to committing + opening a PR

First check the user's original prompt, loaded memories, and `AGENTS.md`/`CLAUDE.md` for
an explicit preference that conflicts with auto commit-and-PR ("always review before
pushing", "open PRs as drafts", "don't open PRs from skills"). If one applies, honor it —
fall to the menu below. Otherwise briefly preview what will be committed and that a PR
will open, then:
1. `git commit -m "fix: <short description>"` (one focused commit; add a regression-test
   commit if separate).
2. `git push -u origin <branch>` and `gh pr create`. When the entry came from an issue
   tracker, include the auto-close syntax in the PR body (`Fixes #N` for GitHub, `Closes
   ABC-123` for Linear) so it closes on merge. Surface the PR URL.

frxnls never auto-merges — hand the PR back for the human to merge, then retire any
worktree with `/frxnls:fx-teardown`.

#### Pre-existing branch (skill did not create it): ask the user

Options:
1. **Commit and open a PR** (`git commit` → `git push` → `gh pr create`) — default
2. **Commit the fix only** (`git commit`) — local commit, no PR
3. **Stop here** — user takes it from there

#### After the fix lands (either path): consider offering learning capture

This closes the compounding loop — a captured learning makes the *next* occurrence of
this bug a `docs/solutions/` lookup. Decide which path applies:

- **Skip silently** when the fix is mechanical and there's no generalizable insight
  (typo, missed null check, missing import). Default to this when in doubt.
- **Offer neutrally** when the lesson can be stated in one sentence — e.g., "X.foo()
  returns T | undefined when Y, not just T", or "the diagnostic path was non-obvious and
  worth recording." If you cannot articulate the lesson, skip rather than offer.
- **Lean into the offer** when the pattern appears in 3+ locations OR the root cause
  reveals a wrong assumption about a shared dependency, framework, or convention that
  other code is likely to repeat — **or no `docs/solutions/` match existed in Phase 0**
  (a genuinely new learning).

When offering, use `AskUserQuestion`. If the user accepts, run `/frxnls:fx-compound`
(pass `mode:headless` for a non-interactive capture), then commit the resulting learning
doc to the same branch and push so any open PR picks it up.

---

## Compose with
- [`fx-compound`](../fx-compound/SKILL.md) — capture the learning once fixed; fills the
  `docs/solutions/` store this skill reads in Phase 0.
- `frxnls:fx-learnings-research` — the agent that searches `docs/solutions/` for a prior
  match (Phase 0, thorough path).
- [`fx-qa-web`](../fx-qa-web/SKILL.md) / [`fx-qa-mobile-ios`](../fx-qa-mobile-ios/SKILL.md)
  — the QA skills whose repro tooling (Playwright MCP / serve-sim) this skill reuses.
- [`fx-expo-worktree-dev`](../fx-expo-worktree-dev/SKILL.md) — boot the app on a sim to
  reproduce an iOS bug.
- [`fx-brainstorm`](../fx-brainstorm/SKILL.md) — when the root cause is a design problem,
  not a localized bug.
- [`fx-teardown`](../fx-teardown/SKILL.md) — retire a worktree once the fix PR is merged.

## Auto-invoke

Trigger phrases: "debug this", "why is this failing", "fix this bug", "trace this error",
"this test is failing", "I'm stuck on", or a pasted stack trace / error message / issue
reference. Manual override: `/frxnls:fx-debug [issue ref | error | test path]`.
