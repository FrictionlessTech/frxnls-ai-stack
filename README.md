# frxnls-ai-stack

Miguel's personal Claude Code stack — skills and agents published under the
`frxnls:` namespace via a local plugin marketplace.

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest (name: frxnls)
frxnls/                           # the plugin
├── .claude-plugin/plugin.json    # plugin manifest (name: frxnls)
├── skills/
│   └── qa/SKILL.md               # /frxnls:qa — browser QA via Playwright MCP
└── agents/
    └── rex-code-reviewer.md      # frxnls:rex-code-reviewer — PR review agent
```

## Components

| Type  | Name                | Invoke                     | What it does |
|-------|---------------------|----------------------------|--------------|
| Skill | `qa`                | `/frxnls:qa`               | Test a running web app in a real browser, then fix and verify bugs |
| Agent | `rex-code-reviewer` | `frxnls:rex-code-reviewer` | Multi-reviewer PR review (simplicity, security, docs, contracts) |

## Install / update locally

This repo *is* the marketplace. Register it once, then install:

```bash
claude plugin marketplace add /Users/miguel/projects/frictionless/frxnls-ai-stack --scope user
claude plugin install frxnls@frxnls --scope user
```

After editing any skill or agent file, pull the changes into your session:

```bash
claude plugin marketplace update frxnls
claude plugin update frxnls
```

(Restart Claude Code to load updated components.)

## Adding a component

- New skill: `frxnls/skills/<name>/SKILL.md`
- New agent: `frxnls/agents/<name>.md`

Then `claude plugin update frxnls` and restart.
