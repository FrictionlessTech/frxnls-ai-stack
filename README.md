# frxnls-ai-stack

Miguel's personal Claude Code stack — skills and agents published under the
`frxnls:` namespace via a local plugin marketplace.

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest (name: frxnls)
frxnls/                           # the plugin
├── .claude-plugin/plugin.json    # plugin manifest (name: frxnls)
├── skills/
│   ├── fx-triage/SKILL.md            # /frxnls:fx-triage — scan work sources → ranked digest (front of the loop)
│   ├── fx-brainstorm/SKILL.md        # /frxnls:fx-brainstorm — adversarial first-principles interviewer
│   ├── fx-plan/                      # /frxnls:fx-plan — idea → researched, implementation-ready plan (SKILL.md + references/)
│   ├── fx-ship/                      # /frxnls:fx-ship — orchestrate plan/issue → PR (SKILL.md + ship-batch.workflow.js)
│   ├── fx-qa-web/SKILL.md            # /frxnls:fx-qa-web — browser QA via Playwright MCP
│   ├── fx-qa-mobile-ios/SKILL.md     # /frxnls:fx-qa-mobile-ios — iOS Simulator QA via serve-sim
│   ├── fx-expo-worktree-dev/SKILL.md # /frxnls:fx-expo-worktree-dev — give the current worktree its own Expo sim+server
│   ├── fx-teardown/SKILL.md          # /frxnls:fx-teardown — retire a task's worktree/branch (+ sim) post-merge
│   ├── fx-compound/                  # /frxnls:fx-compound — capture a solved problem → docs/solutions/ (+ CONCEPTS.md)
│   └── fx-security-audit/SKILL.md    # /frxnls:fx-security-audit — whole-system CSO audit
└── agents/
    ├── rex-code-reviewer.md       # frxnls:rex-code-reviewer — PR review agent
    ├── plan-implementer.md        # frxnls:plan-implementer — executes a plan/issue → PR
    ├── plan-implementer-backend.md # frxnls:plan-implementer-backend — backend/DB-safe executor → PR
    ├── fx-repo-research.md        # frxnls:fx-repo-research — read-only codebase scout
    └── fx-learnings-research.md   # frxnls:fx-learnings-research — read-only docs/solutions + history scout
```

## Components

| Type  | Name                | Invoke                     | What it does |
|-------|---------------------|----------------------------|--------------|
| Skill | `fx-triage`            | `/frxnls:fx-triage`           | The **front of the loop**: scan work sources (GitHub issues/PRs/CI via `gh`; Sentry/Linear/etc. when those MCP connectors are present), rank what's actionable (P0–P3), cross-reference `docs/solutions/`, and surface a triage digest. Discovers and ranks — **never implements**; hands green-lit items to `fx-ship` / `fx-debug`. Runs interactively or **headless on a schedule** (cloud routine / local cron); `gh`-first so it degrades gracefully when MCP connectors are absent |
| Skill | `fx-qa-web`            | `/frxnls:fx-qa-web`           | Test a running web app in a real browser, then fix and verify bugs (Playwright MCP) |
| Skill | `fx-qa-mobile-ios`     | `/frxnls:fx-qa-mobile-ios`    | QA an iOS app on the Simulator — drives it via [serve-sim](https://github.com/EvanBacon/serve-sim) (AX tree + tap/gesture/type, device logs), finds bugs with screenshot evidence, fixes at the RN source, re-verifies |
| Skill | `fx-brainstorm` | `/frxnls:fx-brainstorm` | Adversarial Socratic interviewer — stress-tests an idea, kills complexity, ends with one concrete action. Optionally emits a structured `docs/brainstorms/*-requirements.md` (R/A/F/AE IDs) that `fx-plan` carries as its `origin:` |
| Skill | `fx-plan` | `/frxnls:fx-plan` | Turn an idea, brainstorm doc, or issue into a durable `docs/plans/*.md` — researches (dispatches `fx-repo-research` + `fx-learnings-research`, optional web), breaks work into ID'd units with test scenarios, runs a confidence/deepening pass, then hands off to `fx-ship`. The **HOW** between `fx-brainstorm` (WHAT) and `fx-ship` (execute). Plans, never codes. Adapted from Every's `ce-plan` |
| Skill | `fx-security-audit` | `/frxnls:fx-security-audit` | Whole-system "CSO" security audit (repo, git history, deps, CI/CD, infra, LLM, skills) — read-only findings report |
| Skill | `fx-expo-worktree-dev` | `/frxnls:fx-expo-worktree-dev` | Idempotently give the **current** worktree its own Expo dev server + iOS simulator — reuses them if present, else spins up a dedicated device named `expo-wt-<branch>` (never shared with another worktree) and a free persisted port. Run once per worktree; parallel sims just fall out. Targets by UDID, prebuilds per worktree for dev clients |
| Skill | `fx-ship` | `/frxnls:fx-ship` | Orchestrate a defined plan/issue → reviewed PR: **sets up the workspace (asks branch vs worktree)**, routes to `plan-implementer` vs `-backend`, runs matching QA (`fx-qa-web` / `fx-qa-mobile-ios`), surfaces Rex's review, keeps it alive for revisions, **stops before merge**. Bundles `ship-batch.workflow.js` for batch runs |
| Skill | `fx-teardown` | `/frxnls:fx-teardown` | Retire a finished task's workspace — remove its linked worktree, optionally delete the local branch, shut down its `expo-wt-*` sim. Run after the PR merges/aborts; never auto-runs, never touches the main checkout |
| Skill | `fx-compound` | `/frxnls:fx-compound` | Capture a just-solved problem (or hard-won decision/pattern) as a durable learning in `docs/solutions/` with searchable frontmatter, and seed `CONCEPTS.md` vocabulary — so the next occurrence is a lookup, not a re-investigation. Full/Lightweight/headless modes; overlap-detects vs existing docs; `plan-implementer` + `fx-learnings-research` read what it writes. Adapted from Every's `ce-compound` |
| Agent | `rex-code-reviewer` | `frxnls:rex-code-reviewer` | Multi-reviewer PR review (simplicity, security, docs, contracts) — quote-the-line gate, LLM-security lens, hybrid inline comments + summary with severity badges |
| Agent | `plan-implementer` | `frxnls:plan-implementer` | Executes an already-defined plan file or GitHub issue end-to-end on Sonnet — auto-detects the source, **works on the branch/worktree the caller set up** (never creates/destroys one; refuses on the trunk), implements strictly in-scope, verifies until green, opens **or updates** a PR (`Closes #N`), and reports back |
| Agent | `plan-implementer-backend` | `frxnls:plan-implementer-backend` | Backend/DB-focused fork of `plan-implementer` — detects the project's migration tool (Drizzle/Prisma/Supabase CLI, no Supabase assumption), **generates** migrations and reviews the SQL for data loss, verifies against a **disposable** DB (never prod), enforces RLS/authz + contract-safety, opens a PR. Optional Supabase advisor lints (see below) |
| Agent | `fx-repo-research` | `frxnls:fx-repo-research` | Read-only codebase scout — maps stack/versions, architecture, conventions, and the concrete files/patterns/tests a change touches; flags when local patterns are thin/absent. Dispatched by `fx-plan` (and `fx-compound`); returns a structured brief, never writes |
| Agent | `fx-learnings-research` | `frxnls:fx-learnings-research` | Read-only institutional-knowledge scout — searches `docs/solutions/`, `CONCEPTS.md`, git history, and issues for prior learnings; for `fx-compound`, scores overlap against a doc being written. Returns links + relationships, never writes |

> **Optional — Supabase advisor lints for `plan-implementer-backend`.** The agent
> is portable and assumes no Supabase by default. To have it also run Supabase
> security/performance advisors during verification: (1) add a Supabase MCP server
> to your config **named `supabase`** (so its tools resolve as `mcp__supabase__*`),
> and (2) add `mcp__supabase__get_advisors` to the agent's `tools:` frontmatter.
> When that tool isn't present the agent simply reports "advisors not run."

## Delivery pipeline

The skills and agents compose into one path from idea to merged code. `fx-ship` is the
orchestrator; everything else is a stage it (or you) calls. Each component is forked
only where the **tools or risk** genuinely differ — shared knowledge stays in skills.

```
fx-triage ─▶ idea ─▶ fx-brainstorm ─▶ fx-plan ─▶ fx-ship ─▶ implement ─▶ PR ────────▶ review ─────────▶ QA ────────────▶ you merge ─▶ fx-teardown
discover/rank        WHAT             HOW        orchestrate plan-implementer         rex-code-reviewer fx-qa-web /
+ surface (digest)   · plan mode                            plan-implementer-backend + Rex CI          fx-qa-mobile-ios
   │  ▲                                ▲
   │  └────────────────────────────────┴── docs/solutions/ + CONCEPTS.md ◀── fx-compound (capture each solved problem, after QA / merge)
   └── (scheduled or manual) green-lit items enter at fx-ship / fx-debug / fx-plan
```

**0 · Triage the inbox — `fx-triage`.** Optional front of the loop. Scans GitHub
(issues/PRs/CI via `gh`) and any available MCP sources (Sentry/Linear/…), ranks what's
actionable (P0–P3), cross-references `docs/solutions/`, and **surfaces a digest** — then
stops. *You* green-light items into the pipeline (it never implements). Run it manually,
or on a schedule (local cron / unattended cloud routine) so a run starts without you
being the one to prompt. `gh`-first, so it still produces a useful digest when no MCP
connectors are present.

**1 · Shape the work.** `fx-brainstorm` to pressure-test an idea (the **WHAT**) — when
it's worth preserving, save its `docs/brainstorms/*-requirements.md` and `fx-plan`
picks it up as `origin:`. Then `fx-plan` turns it into a durable, researched plan under
`docs/plans/` (the **HOW**) —
it dispatches `fx-repo-research` + `fx-learnings-research` (and optional web research),
breaks the work into ID'd units with test scenarios, runs a confidence/deepening pass,
and hands off to `fx-ship`. A GitHub issue or Claude Code plan mode also work. `fx-ship`
starts from a *defined* plan/issue — it doesn't plan for you.

**2 · Orchestrate — `fx-ship`.** Owns the **workspace**: recommends branch-in-place vs a new
worktree and **confirms with you**, creates it, routes the work to the right implementer
and QA, keeps the workspace alive through revisions, and **stops before merge** (human
gate — it never merges).
- *Interactive* (default): `/frxnls:fx-ship <plan-or-issue>` — one item or a few, you in the loop.
- *Batch*: bundles `ship-batch.workflow.js` to prepare a worktree+branch per item and
  implement many **independent** items in parallel (one PR each). Stops at PRs; QA/merge stay interactive.

**3 · Implement — `plan-implementer` / `plan-implementer-backend`.** Take a plan file or
issue and **work on the branch/worktree the orchestrator set up** — they never create or
destroy a workspace, and refuse to commit on the trunk. They implement strictly in scope,
verify until green, and open **or update** a PR (`Closes #N`) — re-invoking on the same
branch pushes a revision to the existing PR. The **backend** fork adds migration safety:
detects the migration tool
(Drizzle/Prisma/Supabase CLI — no Supabase assumption), **generates** migrations and
reviews the SQL for data loss, applies them to a **disposable** DB (never prod), and
enforces RLS/authz + API-contract safety.

**4 · Review — `rex-code-reviewer` + Rex CI.** Rex reviews every PR — locally, or via the
CI bot ([below](#ci-rex-as-a-pr-gating-bot)).

**5 · QA — `fx-qa-web` / `fx-qa-mobile-ios`.** Web QA drives a real browser (Playwright MCP).
iOS QA drives the Simulator through [serve-sim](https://github.com/EvanBacon/serve-sim):
an **AX-tree-driven** observe→act→verify loop (tap/gesture/type by element, device logs
as the console) with screenshot evidence. Both find bugs, fix at the source, and re-verify.

**Running the app for mobile QA — `fx-expo-worktree-dev`.** Idempotently gives the *current*
worktree its own Simulator + Expo dev server: a dedicated device named `expo-wt-<branch>`
(never shared across worktrees) on a free, persisted port. Run it once per worktree and
several branches run side by side with no sim/port collisions — and `fx-qa-mobile-ios`
resolves *this* worktree's device by that same name, so it never drives the wrong sim.

**6 · Retire — `fx-teardown`.** Implementers and `fx-ship` never auto-clean, so the branch/worktree
survives PR + QA for revisions. Once the PR is merged or abandoned, `/frxnls:fx-teardown` removes
the worktree, optionally deletes the local branch, and shuts down its `expo-wt-*` sim — never
the main checkout.

**7 · Compound — `fx-compound`.** After a bug is fixed, a QA pass closes out, or a PR
lands, `fx-compound` captures the learning into `docs/solutions/` (searchable frontmatter,
by category) and seeds `CONCEPTS.md` — so the next occurrence is a lookup, not a
re-investigation. The loop closes: `fx-plan` and the `plan-implementer` agents read
`docs/solutions/` to start the *next* change already informed. Each unit of work makes
the next one easier.

```
# shape → plan → ship, the full path
/frxnls:fx-brainstorm                                 # pressure-test the idea (WHAT)
/frxnls:fx-plan "add reservation reminders"           # → docs/plans/YYYY-MM-DD-001-feat-…-plan.md (HOW)
/frxnls:fx-ship docs/plans/2026-06-03-001-feat-reservation-reminders-plan.md

# single item, interactive, with human gates
/frxnls:fx-ship #42

# or hand the work to an implementer directly
"implement the plan in docs/plans/add-orders.md"      →  plan-implementer(-backend)

# after it ships, compound the learning
/frxnls:fx-compound                                   # → docs/solutions/<category>/<slug>.md (+ CONCEPTS.md)

# two branches on two simulators, then QA one of them
/frxnls:fx-expo-worktree-dev   # in worktree A   (boots expo-wt-A)
/frxnls:fx-expo-worktree-dev   # in worktree B   (boots expo-wt-B)
/frxnls:fx-qa-mobile-ios       # in worktree A   (locks onto expo-wt-A)
```

## Install

This repo *is* the marketplace, served from GitHub. On any machine:

```bash
claude plugin marketplace add FrictionlessTech/frxnls-ai-stack --scope user
claude plugin install frxnls@frxnls --scope user
```

(Repo is public — no auth needed to add the marketplace.)

## Editing components

The live source is the GitHub repo, not your local checkout. To ship a change:

```bash
# edit a skill/agent file, BUMP the version in frxnls/.claude-plugin/plugin.json, then:
git add -A && git commit -m "..." && git push

# pull the pushed change into Claude Code:
claude plugin marketplace update frxnls
claude plugin update frxnls@frxnls   # qualified name required; plain `frxnls` errors
```

(Restart Claude Code to load updated components.)

> `plugin update` only pulls when the manifest `version` changed — always bump it.
> To force a refresh without a bump: `claude plugin uninstall frxnls && claude plugin install frxnls@frxnls --scope user`.

## Adding a component

- New skill: `frxnls/skills/<name>/SKILL.md`
- New agent: `frxnls/agents/<name>.md`

Commit, push, then `marketplace update` + `plugin update` as above.

## Model configuration

Every model assignment the plugin makes — four of the five agents
(`plan-implementer`, `plan-implementer-backend`, `fx-repo-research`,
`fx-learnings-research`) and Rex's five finder perspectives — is one canonical map,
[`frxnls/model-defaults.json`](frxnls/model-defaults.json), resolved **at spawn
time** by [`frxnls/scripts/resolve-model.py`](frxnls/scripts/resolve-model.py)
(python3 stdlib, no dependencies). Every skill/agent that spawns one of these
resolves its model through that script before dispatching, so it's visible where
the model came from. `fx-security-audit`'s independent-verifier sub-task is
intentionally the one exception — it's an ad-hoc, unkeyed dispatch with no
canonical model key, so it inherits the session default rather than resolving one.

The bare `rex-code-reviewer` key (top-level agent, distinct from its five
`rex-code-reviewer.*` finder sub-keys below) is **lint-only today** —
`resolve-model.py --check` verifies it against the agent's own frontmatter, but no
flow in this repo actually resolves it at spawn time before invoking Rex itself
(`examples/rex-review.yml` invokes `claude -p "Use the frxnls:rex-code-reviewer
agent..."` directly, with no resolver step). Setting it in
`.frxnls/model-tiers.json` is a no-op until a spawn site is wired for it.

**Override at the install site** — add `.frxnls/model-tiers.json` at your repo's root,
a flat JSON map of any subset of the keys below to a Claude Code model alias
(`haiku` / `sonnet` / `opus`, not a pinned model ID). Partial configs are normal — set
only the keys you want to change; anything you omit falls through to the repo default.

| Key | Default |
|-----|---------|
| `plan-implementer` | sonnet |
| `plan-implementer-backend` | sonnet |
| `fx-repo-research` | sonnet |
| `fx-learnings-research` | sonnet |
| `rex-code-reviewer` (lint-only — see above) | sonnet |
| `rex-code-reviewer.simplicity` | sonnet |
| `rex-code-reviewer.security` | opus |
| `rex-code-reviewer.documentation` | haiku |
| `rex-code-reviewer.correctness` | sonnet |
| `rex-code-reviewer.data-integrity` | sonnet |

Two worked examples: [`examples/model-tiers.high-stakes.json`](examples/model-tiers.high-stakes.json)
(a production repo — backend implementer and security review both stay/move to `opus`)
and [`examples/model-tiers.side-project.json`](examples/model-tiers.side-project.json)
(a low-stakes repo — security review and the research scouts move down to
`sonnet`/`haiku`). Copy whichever is closer to your repo's stakes and edit from there.

**Never-fail fallback.** A missing config file, one that's unreadable or not valid
JSON, an unknown key, or a value that isn't a known alias all degrade silently to the
repo default for that key — a warning goes to stderr, but a spawn is never blocked or
stranded without a model. There is no user-level config and no merge cascade: one
override file, project-scoped, or nothing.

```bash
python3 frxnls/scripts/resolve-model.py rex-code-reviewer.security   # one alias, e.g. "opus"
python3 frxnls/scripts/resolve-model.py --all                        # full resolved map, JSON
python3 frxnls/scripts/resolve-model.py --check                      # lint: agent frontmatter vs the defaults map
```

## CI: Rex as a PR-gating bot

`examples/rex-review.yml` is a reference workflow that runs `frxnls:rex-code-reviewer`
on every PR under a **bot identity**, so it can post a real review (GitHub blocks you
from formally reviewing your own PR). Copy it to `.github/workflows/` in the repo you
want reviewed. **Step-by-step setup: [SETUP.md](SETUP.md).**

**Why a bot:** a review's identity = the token's owner. Run rex under your own token
and GitHub returns 422 on `APPROVE`/`REQUEST_CHANGES`. A GitHub App (or the built-in
`github-actions[bot]`) is a different actor, so the review is allowed.

**Don't gate on the review state** — gate on the **job exit code** as a required status
check. The workflow writes `VERDICT=...` and exits non-zero on `REQUEST_CHANGES`; mark
that job required in branch protection to block merges.

**Setup:**
1. Create a GitHub App (perms: Pull requests RW, Contents RO). Install it on the org +
   repos that run the workflow. Store `REX_APP_ID` + `REX_APP_PRIVATE_KEY` as secrets.
2. Claude auth — pick one secret:
   - `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` (uses your Claude Pro/Max plan,
     no per-token charge, but shares your personal rate limits), or
   - `ANTHROPIC_API_KEY` (Console key — separate billing, easier to scope/rotate; better
     for shared/high-volume CI).
3. Copy `examples/rex-review.yml` into the target repo.
4. Branch protection on the default branch → require the `rex` check.

**Forked PRs:** fork PRs get a read-only token and no secrets. Running rex on untrusted
fork code with secrets needs `pull_request_target` (injection risk). Fine for private
org repos (internal PRs only); for public repos, gate forks behind a label or manual
dispatch.

### Cross-org access (App owned in one org, repo in another)

**This repo is public**, so installing the plugin in CI needs no token — the cross-org
read concern below is moot. The notes remain for reference (and if it ever goes private).

A GitHub App's **owner** and its **install location** are independent. You do not "share"
an App across orgs — you **install** it on each org where you have admin rights,
regardless of which org owns it. So a Rex App registered under **Forked Up** can be
installed onto **FrictionlessTech** and granted access to its repos.

Two access needs, don't conflate them:
- **Posting the review** — the App is installed on the repo *running the workflow*; its
  token posts there. Same-org, no cross-org issue.
- **Reading `frxnls-ai-stack`** (to `plugin install` it) — only a concern if the repo is
  private. Since it's public now, no token is required. If you later make it private:
  1. **Install the Rex App on FrictionlessTech too**, select `frxnls-ai-stack`, and mint a
     token scoped to *that* installation (`actions/create-github-app-token` with
     `owner: FrictionlessTech`, `repositories: frxnls-ai-stack`). A token is per-installation —
     one token can't span both orgs, so you mint a second one for the read.
  2. Or **vendor** the agent file into the reviewed repo
     (`.claude/agents/rex-code-reviewer.md`, the alternative in the workflow).

Org owners installing an App bypass the org's third-party-app access policy, so no extra
allowlisting is needed when you admin both orgs.
