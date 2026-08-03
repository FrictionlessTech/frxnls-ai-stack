---
name: "fx-compound"
description: "Capture a just-solved problem (or a hard-won decision/pattern) as a durable learning in docs/solutions/, and seed the project's CONCEPTS.md vocabulary — so the next occurrence is a lookup, not a re-investigation. Use after a bug is fixed, a QA pass closes out, an fx-ship PR lands, or when the user says \"that worked\", \"it's fixed\", \"document this\", \"capture this learning\", or \"compound this\". Drops the ce-only refresh/sessions ecosystem — frxnls keeps one capture skill. For planning the next change, use fx-plan; for finding past learnings while planning, fx-learnings-research does it automatically."
---

## Codex execution

Before running this workflow, read `../../references/runtime.md` and apply its
Codex-specific delegation, interaction, and model-selection rules. Those rules
override any provider-specific wording that remains below.

# /fx-compound: capture a learning so knowledge compounds

The first time you solve a problem it costs research. Document it, and the next
occurrence costs minutes. `fx-compound` writes that documentation while the
context is still fresh — a structured doc under `docs/solutions/` with searchable
YAML frontmatter, plus a seed of the project's shared vocabulary in `CONCEPTS.md`.

This is the **learning** half of the loop. `fx-plan` and the `plan-implementer`
agents read `docs/solutions/` to start informed; `fx-compound` is what fills it.
**Each unit of work should make the next one easier — not harder.**

```
fix a bug / land a PR / finish a QA pass ─▶ /fx-compound ─▶ docs/solutions/<category>/<slug>.md (+ CONCEPTS.md)
                                                                         ▲
                                          fx-plan & plan-implementer read this before the next change
```

Adapted from EveryInc's compound-engineering `ce-compound`, retargeted to this
stack and trimmed of the ce-only ecosystem (no `ce-sessions`, no
`ce-compound-refresh`, no bespoke reviewer agents).

## Preconditions (advisory)

Capture is worth it when the problem is **solved**, the fix is **verified**, and it
was **non-trivial** (not a typo or one-liner). If the problem isn't actually solved
yet, say so and stop rather than documenting a guess.

## Modes

Strip a `mode:headless` token from `the user-provided input` before treating the remainder as a
brief context hint (`mode:` is a flag prefix, not context).

| Mode | When | Behavior |
|------|------|----------|
| **Interactive** (default) | no mode token | Ask Full vs Lightweight; run; end with a "What's next?" question |
| **Headless** | `mode:headless` present | No blocking questions. Run **Full without the interactive review**. Apply the discoverability edit silently. End with a structured terminal report and the literal line `Documentation complete` (or `Documentation skipped`). |

Headless is for automations and skill-to-skill calls (e.g. an `fx-ship` batch run).
Once detected, it holds for the whole run.

## Interaction

When input is required, ask the user directly in chat. Use a structured user-input tool only when one is available in the current mode, and never silently skip a required question.

In **interactive** mode, ask once before proceeding:

- **Full** (recommended) — researches related docs, detects duplicates,
  cross-references, then writes. Best quality.
- **Lightweight** — single pass, same doc shape, no duplicate detection. Faster /
  fewer tokens. Good for simple fixes or a long session near its context limit.

Do not pre-select; wait for the choice. Headless always runs Full (minus the
interactive review).

## CONCEPTS.md bootstrap requests

If invoked specifically to **create `CONCEPTS.md` from scratch** (a repo-wide
glossary) rather than to document a solved problem: that is the repo-wide bootstrap
path in `references/concepts-vocabulary.md`. Read that reference, seed the whole
project's declared domain model, and exit — do not run the capture phases below. A
normal capture only seeds the *learning's area*, never the whole repo.

---

## Full Mode

> **One deliverable: the learning doc.** Research happens in your context or via
> read-only sub-agents that **return text, never write files**. Only this skill
> writes — the solution doc, plus two expected maintenance side-effects: a
> `CONCEPTS.md` create/update, and a small instruction-file edit for
> discoverability. Nothing else.

### Phase 0 — Extract from the conversation

You are the conversation — you already hold the problem and the fix. Pull together,
from this session's history:

- **The problem** — symptoms, error messages, observable behavior.
- **What didn't work** — dead ends and *why* they failed (this is high-value; it's
  what saves the next person the wasted hours).
- **The fix that worked** — with before/after code where it clarifies.
- **Why it works** — the root cause and why the fix addresses it.
- **The module/component** affected, and the track (bug vs knowledge).

Also scan the "user's auto-memory" block in your system prompt (Codex) for
relevant notes; tag anything you fold in with "(memory context)".

### Phase 1 — Research (parallel, read-only)

Launch in parallel through Codex subagent delegation (skip in Lightweight mode):

- **`fx-learnings-research`** — pass the problem context **and** your draft of the
  learning. It searches `docs/solutions/`, `CONCEPTS.md`, git history, and related
  issues, and returns related docs, refresh candidates, domain vocabulary, and an
  **overlap assessment** (high / moderate / low) against your draft.
- **`fx-repo-research`** (only when the learning needs codebase grounding — e.g. to
  pin the exact component, confirm the affected files, or name the pattern) — pass
  the problem context and scope `patterns`.

**Codex dispatch.** Use the built-in role from `../../references/runtime.md`; let Codex choose the subagent model unless the user explicitly requests one.

Wait for both to return before assembling.

### Phase 2 — Classify, assemble, write

1. **Classify.** Read `references/schema.yaml` and `references/yaml-schema.md`.
   Determine the track (bug vs knowledge), the `problem_type`, the `component`
   (prefer the narrowest), and the category directory.
2. **Check overlap** from `fx-learnings-research` and decide create-vs-update:

   | Overlap | Action |
   |---------|--------|
   | **High** — same problem, root cause, and solution | **Update the existing doc** with fresher context. Keep its path and frontmatter; add `last_updated: YYYY-MM-DD`. Don't duplicate. |
   | **Moderate** — same area, different angle/solution | **Create** the new doc; note the near-neighbor in `## Related`. |
   | **Low / none** | **Create** the new doc. |

3. **Assemble.** Read `assets/resolution-template.md` and fill the track-matching
   template. Fold "what didn't work" findings into **What Didn't Work** (bug) or
   **Context** (knowledge). Keep code examples minimal and clear.
4. **Filename & path.** `docs/solutions/<category>/<sanitized-problem-slug>.md` — no
   date suffix (the `date:` field is canonical). `mkdir -p` the category dir.
5. **Validate YAML.** Apply the YAML-safety quoting rule for array items, then run
   `python3 scripts/validate-frontmatter.py <output-path>`. Exit 0 = parser-safe;
   exit 1 = fix the named field(s) and re-run until green. Do not claim success
   while it fails.
6. **Write** the doc (or update the existing one).

### Phase 2.4 — Vocabulary capture

**Read `references/concepts-vocabulary.md` first — unconditional.** Then, applying
its criteria, scan the new doc **and the surrounding conversation** for qualifying
domain terms:

- If `CONCEPTS.md` exists, add missing qualifying terms and refine entries where new
  precision surfaced.
- If it doesn't exist and ≥1 term qualifies, **create it** with the bootstrap
  preamble and **seed the learning's area** — the core domain nouns of the modules
  this fix touched (not the whole repo; hold borderline terms for later).
- Refresh only the **coherence neighborhood** of any entry you touch (its cluster
  siblings / cross-referenced terms), on evidence you already have — never a
  full-file audit.

Apply edits **silently** in every mode. If nothing qualified, record that explicitly
in the output (e.g. "Vocabulary: scanned, no qualifying terms") — the visible
scan-and-no-result line is the audit signal that the reference was consulted.

Lightweight mode runs an **update-only** version: refine an existing `CONCEPTS.md`,
but defer creation/seeding to a Full run.

### Phase 2.5 — Stale-doc flag (no auto-refresh)

frxnls has no separate refresh skill. If `fx-learnings-research` surfaced a doc the
new learning **contradicts or supersedes** (a refresh candidate), surface it as a
recommendation in the output with the specific path — let the user decide whether to
edit it. Do not silently rewrite other docs. Always capture the new learning first;
refresh is optional follow-up.

### Discoverability Check

Runs every time (the store only compounds when agents can find it). Identify the
root instruction file with substantive content (`AGENTS.md` or `CLAUDE.md`; follow a
shim that just `@`-includes the other). If neither exists, skip.

Assess whether an agent reading it would learn that (1) a searchable solutions store
exists, (2) enough of its structure to search (categories, frontmatter fields like
`module`, `tags`, `problem_type`), and (3) that it's relevant when implementing or
debugging in documented areas. This is semantic, not a string match.

If the spirit is met, do nothing. If not, draft the **smallest** addition that
communicates those three things — prefer a single line in an existing section (an
architecture tree, a docs section) over a new heading. Keep it informational, not
imperative ("relevant when implementing or debugging in documented areas", not
"always search before implementing"). Example line:

```
docs/solutions/  # documented learnings (bugs, patterns, conventions), by category with YAML frontmatter (module, tags, problem_type)
```

In **Full interactive** mode, show the proposed edit and get consent via
a direct question to the user before applying. In **Lightweight** mode, emit a one-line tip
instead of editing. In **headless** mode, apply silently and report it.

If `CONCEPTS.md` exists, run the same check for it (add a one-line mention if the
instruction file doesn't surface the shared vocabulary). Skip entirely if it doesn't
exist — never nag for an artifact the project hasn't adopted.

---

## Lightweight Mode

Single sequential pass, no sub-agents, same doc shape — fewer tokens, no
duplicate detection:

1. Extract the problem and fix from the conversation (and auto-memory).
2. Read `references/schema.yaml` + `references/yaml-schema.md`; classify track,
   category, filename.
3. Write `docs/solutions/<category>/<slug>.md` from the track template with
   track-appropriate frontmatter (apply YAML-safety quoting); run
   `validate-frontmatter.py` until green.
4. Vocabulary capture **update-only** (refine an existing `CONCEPTS.md`; defer
   creation to a Full run).
5. Emit the lightweight output, including discoverability/vocabulary **tips** (it
   does not edit instruction files).

Overlap detection is skipped, so a Lightweight run may create a near-duplicate —
acceptable; a later Full run or manual edit reconciles it.

---

## Output

### Headless

Structured terminal report, then end the turn — no questions. End with the literal
`Documentation complete` (or `Documentation skipped` when nothing was written, e.g.
the problem isn't actually solved) so callers can detect completion.

```
✓ Documentation complete (headless mode)

File: docs/solutions/<category>/<slug>.md  (created | updated)
Track: <bug | knowledge>   Category: <category>   Severity: <…>
Overlap: <none | low | moderate — see <path> | high — existing doc updated>
Instruction-file edit: <none needed | applied to <path>>
CONCEPTS.md: <scanned, no qualifying terms | created with N entries (M seeded) | updated — N added, N refined>
Stale-doc flag: <none | <path> may now be superseded>

Documentation complete
```

### Interactive

Report what was written and learned, then ask "What's next?" via a direct question to the user
(don't end the turn without the user's pick):

```
✓ Documentation complete

File written: docs/solutions/<category>/<slug>.md (created | updated)
Track / Category / Severity: …
Related: <links from fx-learnings-research, or none>
CONCEPTS.md: <created with N entries | updated | scanned, no qualifying terms>
```

What's next options: **Done** (recommended) · **Plan the follow-up** (hand to
`$fx-plan`) · **Open the doc** · **Flag a stale doc to revise**.

## Auto-invoke

Trigger phrases: "that worked", "it's fixed", "working now", "problem solved",
"document this", "capture this learning". Manual override: `/fx-compound [context]`
to document immediately.
