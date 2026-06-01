# frxnls-ai-stack

Miguel's personal Claude Code stack — skills and agents published under the
`frxnls:` namespace via a local plugin marketplace.

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest (name: frxnls)
frxnls/                           # the plugin
├── .claude-plugin/plugin.json    # plugin manifest (name: frxnls)
├── skills/
│   ├── qa-web/SKILL.md                      # /frxnls:qa-web — browser QA via Playwright MCP
│   ├── qa-mobile-ios/SKILL.md               # /frxnls:qa-mobile-ios — iOS Simulator QA via serve-sim
│   ├── first-principles-brainstorm/SKILL.md # /frxnls:first-principles-brainstorm
│   ├── security-audit/SKILL.md              # /frxnls:security-audit — whole-system CSO audit
│   ├── expo-worktree-dev/SKILL.md           # /frxnls:expo-worktree-dev — give the current worktree its own Expo sim+server
│   └── ship/                                # /frxnls:ship — orchestrate plan/issue → PR (SKILL.md + ship-batch.workflow.js)
└── agents/
    ├── rex-code-reviewer.md      # frxnls:rex-code-reviewer — PR review agent
    ├── plan-implementer.md       # frxnls:plan-implementer — executes a plan/issue → PR
    └── plan-implementer-backend.md # frxnls:plan-implementer-backend — backend/DB-safe executor → PR
```

## Components

| Type  | Name                | Invoke                     | What it does |
|-------|---------------------|----------------------------|--------------|
| Skill | `qa-web`            | `/frxnls:qa-web`           | Test a running web app in a real browser, then fix and verify bugs (Playwright MCP) |
| Skill | `qa-mobile-ios`     | `/frxnls:qa-mobile-ios`    | QA an iOS app on the Simulator — drives it via [serve-sim](https://github.com/EvanBacon/serve-sim) (AX tree + tap/gesture/type, device logs), finds bugs with screenshot evidence, fixes at the RN source, re-verifies |
| Skill | `first-principles-brainstorm` | `/frxnls:first-principles-brainstorm` | Adversarial Socratic interviewer — stress-tests an idea, kills complexity, ends with one concrete action |
| Skill | `security-audit` | `/frxnls:security-audit` | Whole-system "CSO" security audit (repo, git history, deps, CI/CD, infra, LLM, skills) — read-only findings report |
| Skill | `expo-worktree-dev` | `/frxnls:expo-worktree-dev` | Idempotently give the **current** worktree its own Expo dev server + iOS simulator — reuses them if present, else spins up a dedicated device named `expo-wt-<branch>` (never shared with another worktree) and a free persisted port. Run once per worktree; parallel sims just fall out. Targets by UDID, prebuilds per worktree for dev clients |
| Skill | `ship` | `/frxnls:ship` | Orchestrate a defined plan/issue → reviewed PR: routes to `plan-implementer` vs `-backend`, runs matching QA (`qa-web` / `qa-mobile-ios`), surfaces Rex's review, **stops before merge**. Bundles `ship-batch.workflow.js` for parallel batch runs |
| Agent | `rex-code-reviewer` | `frxnls:rex-code-reviewer` | Multi-reviewer PR review (simplicity, security, docs, contracts) — quote-the-line gate, LLM-security lens, hybrid inline comments + summary with severity badges |
| Agent | `plan-implementer` | `frxnls:plan-implementer` | Executes an already-defined plan file or GitHub issue end-to-end on Sonnet — auto-detects the source, isolates git work (own worktree off the main checkout), implements strictly in-scope, verifies until green, opens a PR (`Closes #N`), and reports back |
| Agent | `plan-implementer-backend` | `frxnls:plan-implementer-backend` | Backend/DB-focused fork of `plan-implementer` — detects the project's migration tool (Drizzle/Prisma/Supabase CLI, no Supabase assumption), **generates** migrations and reviews the SQL for data loss, verifies against a **disposable** DB (never prod), enforces RLS/authz + contract-safety, opens a PR. Optional Supabase advisor lints (see below) |

> **Optional — Supabase advisor lints for `plan-implementer-backend`.** The agent
> is portable and assumes no Supabase by default. To have it also run Supabase
> security/performance advisors during verification: (1) add a Supabase MCP server
> to your config **named `supabase`** (so its tools resolve as `mcp__supabase__*`),
> and (2) add `mcp__supabase__get_advisors` to the agent's `tools:` frontmatter.
> When that tool isn't present the agent simply reports "advisors not run."

## Delivery pipeline

The skills and agents compose into one path from idea to merged code. `ship` is the
orchestrator; everything else is a stage it (or you) calls. Each component is forked
only where the **tools or risk** genuinely differ — shared knowledge stays in skills.

```
idea ──▶ plan ───────────▶ ship ──▶ implement ────────────▶ PR ──▶ review ───────▶ QA ─────────────▶ you merge
         first-principles          plan-implementer               rex-code-reviewer   qa-web /
         · plan mode               plan-implementer-backend        + Rex CI            qa-mobile-ios
```

**1 · Shape the work.** `first-principles-brainstorm` to pressure-test an idea, then
Claude Code plan mode (or a GitHub issue) to define it. `ship` starts from a *defined*
plan/issue — it doesn't plan for you.

**2 · Orchestrate — `ship`.** Routes each plan/issue to the right implementer and QA,
sequences them, and **stops before merge** (human gate — it never merges).
- *Interactive* (default): `/frxnls:ship <plan-or-issue>` — one item or a few, you in the loop.
- *Batch*: bundles `ship-batch.workflow.js` to implement many **independent** items in
  parallel (one PR each) via the Workflow tool. Stops at PRs; QA/merge stay interactive.

**3 · Implement — `plan-implementer` / `plan-implementer-backend`.** Take a plan file or
issue, **isolate git work in their own worktree** (branch-in-place when already in a
linked worktree, else a self-managed worktree off your main checkout — your tree is
never disturbed), implement strictly in scope, verify until green, and open a PR
(`Closes #N`). The **backend** fork adds migration safety: detects the migration tool
(Drizzle/Prisma/Supabase CLI — no Supabase assumption), **generates** migrations and
reviews the SQL for data loss, applies them to a **disposable** DB (never prod), and
enforces RLS/authz + API-contract safety.

**4 · Review — `rex-code-reviewer` + Rex CI.** Rex reviews every PR — locally, or via the
CI bot ([below](#ci-rex-as-a-pr-gating-bot)).

**5 · QA — `qa-web` / `qa-mobile-ios`.** Web QA drives a real browser (Playwright MCP).
iOS QA drives the Simulator through [serve-sim](https://github.com/EvanBacon/serve-sim):
an **AX-tree-driven** observe→act→verify loop (tap/gesture/type by element, device logs
as the console) with screenshot evidence. Both find bugs, fix at the source, and re-verify.

**Running the app for mobile QA — `expo-worktree-dev`.** Idempotently gives the *current*
worktree its own Simulator + Expo dev server: a dedicated device named `expo-wt-<branch>`
(never shared across worktrees) on a free, persisted port. Run it once per worktree and
several branches run side by side with no sim/port collisions — and `qa-mobile-ios`
resolves *this* worktree's device by that same name, so it never drives the wrong sim.

```
# single item, interactive, with human gates
/frxnls:ship #42

# or hand the work to an implementer directly
"implement the plan in .claude/plans/add-orders.md"   →  plan-implementer(-backend)

# two branches on two simulators, then QA one of them
/frxnls:expo-worktree-dev   # in worktree A   (boots expo-wt-A)
/frxnls:expo-worktree-dev   # in worktree B   (boots expo-wt-B)
/frxnls:qa-mobile-ios       # in worktree A   (locks onto expo-wt-A)
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
