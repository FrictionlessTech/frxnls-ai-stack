# frxnls-venture (Gemini CLI extension)

The venture discovery loop — `fx-idea-scout` → `fx-market-research` → `fx-go-nogo`
— ported from the `frxnls` Claude Code plugin.

Both copies read and write the same `$VENTURE_HOME` (default `~/ventures`), the
same `constraints.md`, and the same append-only `_ledger.md`. You can scout in
Claude Code and decide in Gemini CLI, or the reverse. The pointer file
`~/.frxnls/venture-home` is shared.

## Install — Gemini CLI

```bash
gemini extensions link ./gemini/frxnls-venture
```

`link` symlinks into `~/.gemini/extensions/frxnls-venture`, so edits in this repo
take effect on the next CLI restart — the right mode while the port is still
moving. For a frozen copy, use `gemini extensions install ./gemini/frxnls-venture`
and re-run `gemini extensions update frxnls-venture` after changes.

Restart the CLI, then verify:

```bash
gemini extensions list
```

## Use

Skills activate on their own from the descriptions, or force them explicitly:

```bash
/fx-idea-scout what software do independent insurance adjusters run?
```

`/fx-market-research <slug>` and `/fx-go-nogo <slug>` follow.

## Install — Google Antigravity

Antigravity's plugin layout is `plugin.json` + `skills/` + `agents/`, which this
tree already matches, so the same directory installs in both runtimes. There is
no CLI installer — plugins are discovered by directory scan, so you copy or
symlink it into place:

```bash
mkdir -p ~/.gemini/config/plugins && ln -s "$PWD/gemini/frxnls-venture" ~/.gemini/config/plugins/frxnls-venture
```

Use `<workspace>/.agents/plugins/` instead for a workspace-scoped install, though
this loop is standalone by design and global is the better fit. Restart
Antigravity, then confirm with `/agents` that the three subagents registered.

`gemini-extension.json` and `commands/` are inert here — Antigravity ignores
both. The path probe in each skill's Paths step finds the plugin location
automatically; no `FX_EXT_HOME` needed.

Two caveats, both unverified against a live install:

- **Slash commands don't port.** Antigravity uses workflows (markdown, invoked
  `/name`, 12k-char cap) and the docs don't say they can be bundled in a plugin.
  The skills still auto-activate from their descriptions — you just lose the
  explicit `/fx-idea-scout` trigger unless you hand-write three workflow files.
- **Agent file layout may differ.** Standalone Antigravity subagents live at
  `~/.gemini/config/agents/<name>/agent.md` (a directory per agent), while this
  tree uses Gemini CLI's flat `agents/<name>.md`. If `/agents` doesn't list the
  three researchers after a restart, re-nest them:
  `for a in fx-screen-scout fx-lane-researcher fx-risk-researcher; do mkdir -p ~/.gemini/config/agents/$a && cp agents/$a.md ~/.gemini/config/agents/$a/agent.md; done`

Note the two runtimes use adjacent but non-colliding roots — Gemini CLI reads
`~/.gemini/extensions/`, Antigravity reads `~/.gemini/config/plugins/`. Both can
be installed at once.

## Layout

```
gemini-extension.json               manifest
commands/*.toml                     /fx-idea-scout, /fx-market-research, /fx-go-nogo
agents/*.md                         fx-screen-scout, fx-lane-researcher, fx-risk-researcher
skills/fx-idea-scout/               SKILL.md + templates/ (brief, constraints, ledger)
skills/fx-market-research/          SKILL.md + references/lanes.md
skills/fx-go-nogo/                  SKILL.md + references/scorecard.md
```

## What changed from the Claude Code plugin

The prose — the screening logic, evidence discipline, gates, anti-patterns — is
unchanged. `references/lanes.md`, `references/scorecard.md` and all three
templates are byte-identical copies. Only the mechanics differ:

| Claude Code | Gemini CLI |
|---|---|
| `Bash` | `run_shell_command` |
| `Read` / `Write` / `Edit` | `read_file` / `write_file` / `replace` |
| `Grep` / `Glob` | `grep_search` / `glob` |
| `WebSearch` / `WebFetch` | `google_web_search` / `web_fetch` |
| `AskUserQuestion` | `ask_user` (max 4 questions/call, 16-char headers) |
| `Agent(fx-lane-researcher)` | subagent exposed as a tool named `fx-lane-researcher` |
| `${CLAUDE_PLUGIN_ROOT}` | `$FX_EXT_HOME`, resolved in each skill's Paths step |
| `allowed-tools:` in SKILL.md | dropped — Gemini SKILL.md takes `name` + `description` only |
| `argument-hint:` in SKILL.md | dropped — arg hints live in `commands/*.toml` instead |
| `scripts/resolve-model.py` + `model-defaults.json` | dropped — model pinned in each agent's frontmatter |

Three behavioral notes:

**Model tiering is gone entirely.** Neither runtime has a per-invocation model
override, so the haiku/sonnet/opus resolver doesn't port. All three agents now
omit `model` and inherit the session model — run the loop on your top tier, since
the risk lane is where a cheap model costs you the whole dossier.

`fx-screen-scout` originally pinned `gemini-3-flash-preview` to keep the screen
cheap. **Antigravity silently dropped the agent from its registry** because of it
— it never appeared in `/agents`, with no error, while the two agents lacking a
`model` key registered normally. Cost on that step is now held by `max_turns: 12`
instead, which is portable and was doing most of the work anyway. If you re-pin a
model, verify the agent still appears in `/agents` before trusting a run.

**Fan-out may serialize.** Gemini's docs don't guarantee parallel subagent
delegation. `fx-market-research` now asks for all seven lanes in a single turn and
treats wall-clock parallelism as a bonus — lane *independence* is the property that
actually matters for correctness, and that's preserved either way.

**Subagents can't see `lanes.md`.** They run in a separate context, so
`fx-market-research` quotes each lane brief into the assignment verbatim rather
than pointing at the file. Same for the venture brief and constraints.

## Maintaining this alongside the Claude version

Roughly 95% of each SKILL.md is identical between the two trees. The divergence is
confined to the frontmatter block and the "Paths" section, plus inline tool names.
A change to the *logic* (a new lane, a reworded kill criterion, a scorecard tweak)
usually means editing two files and copying the shared assets. A change to the
*mechanics* means only one side moves.

Before shipping a change to both, re-run the port check:

```bash
python3 gemini/check-port.py
```

It verifies the manifest, TOML, and frontmatter parse; that agent/skill names match
their paths; that the shared assets are still byte-identical to the `frxnls/`
originals; and that no Claude-only tool name leaked into the Gemini tree.
