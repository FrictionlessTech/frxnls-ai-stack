# frxnls-ai-stack

Miguel's personal Claude Code stack — skills and agents published under the
`frxnls:` namespace via a local plugin marketplace.

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest (name: frxnls)
frxnls/                           # the plugin
├── .claude-plugin/plugin.json    # plugin manifest (name: frxnls)
├── skills/
│   ├── qa/SKILL.md                          # /frxnls:qa — browser QA via Playwright MCP
│   ├── first-principles-brainstorm/SKILL.md # /frxnls:first-principles-brainstorm
│   └── security-audit/SKILL.md              # /frxnls:security-audit — whole-system CSO audit
└── agents/
    └── rex-code-reviewer.md      # frxnls:rex-code-reviewer — PR review agent
```

## Components

| Type  | Name                | Invoke                     | What it does |
|-------|---------------------|----------------------------|--------------|
| Skill | `qa`                | `/frxnls:qa`               | Test a running web app in a real browser, then fix and verify bugs |
| Skill | `first-principles-brainstorm` | `/frxnls:first-principles-brainstorm` | Adversarial Socratic interviewer — stress-tests an idea, kills complexity, ends with one concrete action |
| Skill | `security-audit` | `/frxnls:security-audit` | Whole-system "CSO" security audit (repo, git history, deps, CI/CD, infra, LLM, skills) — read-only findings report |
| Agent | `rex-code-reviewer` | `frxnls:rex-code-reviewer` | Multi-reviewer PR review (simplicity, security, docs, contracts) — quote-the-line gate, LLM-security lens, hybrid inline comments + summary with severity badges |

## Install

This repo *is* the marketplace, served from GitHub. On any machine:

```bash
claude plugin marketplace add FrictionlessTech/frxnls-ai-stack --scope user
claude plugin install frxnls@frxnls --scope user
```

(Repo is private — requires `gh`/git auth with access to the org.)

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
