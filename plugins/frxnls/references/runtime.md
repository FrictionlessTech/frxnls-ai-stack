# Codex runtime rules

These rules adapt the canonical frxnls workflows to Codex. They take precedence
over provider-specific terms that remain in generated skill text.

## Invoke skills

- Refer to a bundled skill as `$<skill-name>`, for example `$fx-plan` or
  `$rex-code-reviewer`.
- When one workflow hands off to another, invoke that skill directly. Do not use
  Claude-style slash commands or namespaced agent identifiers.

## Delegate work

Use Codex subagent/collaboration tools. Spawn independent read-only work in
parallel, wait for all required results, and keep write ownership explicit.

| Specialist skill | Built-in Codex role | Dispatch instruction |
| --- | --- | --- |
| `$fx-repo-research`, `$fx-learnings-research` | `explorer` | Tell the subagent to use the named skill and include the exact research scope. |
| `$plan-implementer`, `$plan-implementer-backend` | `worker` | Tell the subagent it owns implementation in the current worktree and must use the named skill. |
| `$fx-screen-scout`, `$fx-lane-researcher`, `$fx-risk-researcher`, `$rex-code-reviewer` | `default` | Tell the subagent to use the named skill and pass the complete bounded task. |

If a specialist role is unavailable, use `default` with the same skill
instruction. Do not invent a custom agent type.

## Models and tools

- Let Codex select the current/session subagent model unless the user explicitly
  requests a model. Claude model aliases and `model-defaults.json` do not apply.
- Ask the user directly in chat, or use a user-input tool only when one is
  available in the current mode.
- Use the tools available in the current Codex session. Treat old Claude tool
  names as descriptions of intent, not literal tool requirements.
- Preserve the current sandbox and approval boundaries. A skill never grants
  permissions by naming a tool.
