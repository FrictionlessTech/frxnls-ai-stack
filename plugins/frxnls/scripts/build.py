#!/usr/bin/env python3
"""Build the Codex-facing skills from the canonical Claude plugin sources.

The Claude files remain the source of truth. This script keeps the Codex plugin
reviewable and reproducible while applying the small provider-specific rewrites
that Codex needs.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import shutil
import tempfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY_ROOT / "frxnls"
SOURCE_SKILLS = SOURCE_ROOT / "skills"
SOURCE_AGENTS = SOURCE_ROOT / "agents"
SOURCE_TEMPLATES = SOURCE_ROOT / "templates"
OUTPUT_SKILLS = PLUGIN_ROOT / "skills"
OUTPUT_TEMPLATES = PLUGIN_ROOT / "templates"

SUPPORT_DIRS = ("assets", "references", "scripts")
EXPECTED_SKILLS = 22
FORBIDDEN_GENERATED_TEXT = (
    "${CLAUDE_PLUGIN_ROOT}",
    "$ARGUMENTS",
    "/frxnls:",
    "frxnls:",
    "AskUserQuestion",
    "ToolSearch",
    "Claude Code",
)

CODEX_NOTE = """## Codex execution

Before running this workflow, read `../../references/runtime.md` and apply its
Codex-specific delegation, interaction, and model-selection rules. Those rules
override any provider-specific wording that remains below.

"""

MODEL_DISPATCH_RE = re.compile(
    r"\*\*Resolve the model before dispatch\.\*\*.*?agent's frontmatter default applies\.\n",
    re.DOTALL,
)

REX_MODEL_RE = re.compile(
    r"\*\*Pre-step — resolve models\.\*\*.*?"
    r"#### Fan-out policy \(ensemble\)",
    re.DOTALL,
)

TRIAGE_SCHEDULE_RE = re.compile(
    r"## Run it on a schedule \(the automation layer\).*?## Auto-invoke",
    re.DOTALL,
)

MARKET_MODELS_RE = re.compile(
    r"\*\*Resolve models before spawning\*\*.*?"
    r"where the script's default git-root detection has nothing to find\.\n",
    re.DOTALL,
)

SCOUT_MODEL_RE = re.compile(
    r"Spawn via `Agent\(fx-screen-scout\)`, resolving the model first:.*?"
    r"rather than editing the plugin\.\n",
    re.DOTALL,
)

SHIP_BATCH_RE = re.compile(
    r"## Batch mode \(parallel, for many independent items\).*?## Compose with",
    re.DOTALL,
)


def codex_frontmatter(source: str) -> tuple[str, str]:
    if not source.startswith("---\n"):
        raise ValueError("source file is missing YAML frontmatter")

    _, header, body = source.split("---", 2)
    lines = header.strip("\n").splitlines()
    field_starts = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^[A-Za-z][A-Za-z0-9_-]*:", line)
    ]

    try:
        name_start = next(index for index in field_starts if lines[index].startswith("name:"))
        description_start = next(
            index for index in field_starts if lines[index].startswith("description:")
        )
    except StopIteration as error:
        raise ValueError("source frontmatter requires name and description") from error

    description_end = next(
        (index for index in field_starts if index > description_start), len(lines)
    )
    raw_name = lines[name_start].split(":", 1)[1].strip()
    if raw_name.startswith(("'", '"')):
        name = ast.literal_eval(raw_name)
    else:
        name = raw_name

    description_lines = lines[description_start:description_end]
    raw_description = description_lines[0].split(":", 1)[1].strip()
    if raw_description:
        if raw_description.startswith(("'", '"')):
            description = ast.literal_eval(raw_description)
        else:
            description = raw_description
    else:
        folded = " ".join(line.strip() for line in description_lines[1:])
        if folded.startswith("'") and folded.endswith("'"):
            description = folded[1:-1].replace("''", "'")
        elif folded.startswith('"') and folded.endswith('"'):
            description = ast.literal_eval(folded)
        else:
            description = folded

    frontmatter = (
        "---\n"
        f"name: {json.dumps(name, ensure_ascii=False)}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "---\n"
    )
    return frontmatter, body.lstrip("\n")


def rewrite_for_codex(text: str) -> str:
    text = re.sub(
        r"\. End the commit message with:\n\s*```\n\s*"
        r"Co-Authored-By: Claude <noreply@anthropic\.com>\n\s*```",
        ".",
        text,
    )
    text = re.sub(
        r" ending with\n`Co-Authored-By: Claude <noreply@anthropic\.com>`, then",
        ", then",
        text,
    )
    text = re.sub(
        r"Ask via `AskUserQuestion` \(load its schema with `ToolSearch`.*?"
        r"chat options only if unavailable\.",
        "Ask the user directly in chat; use a structured user-input tool only "
        "when one is available in the current mode.",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"When asking the user anything, use `AskUserQuestion` \(load its schema via.*?"
        r"Never silently skip (?:a blocking question|a question)\.",
        "When input is required, ask the user directly in chat. Use a structured "
        "user-input tool only when one is available in the current mode, and never "
        "silently skip a required question.",
        text,
        flags=re.DOTALL,
    )
    text = MODEL_DISPATCH_RE.sub(
        "**Codex dispatch.** Use the built-in role from "
        "`../../references/runtime.md`; let Codex choose the subagent model "
        "unless the user explicitly requests one.\n",
        text,
    )
    text = REX_MODEL_RE.sub(
        "**Codex model policy.** Let Codex choose each review subagent's model "
        "unless the user explicitly requests one. Keep the review lanes and "
        "fan-out policy below unchanged.\n\n#### Fan-out policy (ensemble)",
        text,
    )
    text = TRIAGE_SCHEDULE_RE.sub(
        """## Run it on a schedule (the automation layer)

This skill is the behavior; a Codex scheduled task is the thin trigger. Test
`$fx-triage` interactively first, then create a scheduled task that invokes it.
Configure GitHub and any optional Sentry, Slack, or Linear plugins/connectors in
the scheduled task's workspace. Missing optional connectors are reported in the
digest and never make GitHub-first triage fail.

## Auto-invoke""",
        text,
    )
    text = MARKET_MODELS_RE.sub(
        "**Codex dispatch.** Spawn `$fx-lane-researcher` with the built-in "
        "`default` role for the seven general lanes and `$fx-risk-researcher` "
        "with `default` for risk. Let Codex select models from the current "
        "session policy.\n",
        text,
    )
    text = SCOUT_MODEL_RE.sub(
        "Spawn one built-in `default` subagent per candidate and instruct each "
        "to use `$fx-screen-scout`. Let Codex select the model from the current "
        "session policy.\n",
        text,
    )
    text = SHIP_BATCH_RE.sub(
        """## Batch mode (parallel, for many independent items)

For several genuinely independent items, use Codex's native collaboration tools:

1. Confirm the items do not share files or ordering dependencies.
2. Create one `codex/<slug>` branch and linked worktree per item.
3. Spawn one built-in `worker` per worktree, give it exclusive ownership of that
   worktree, and instruct it to use `$plan-implementer` or
   `$plan-implementer-backend`.
4. Wait for every worker and return one PR per item. Batch mode stops at PRs;
   interactive QA and the human merge gate remain separate.

Use batch mode only when the user explicitly asks for parallel delivery.

## Compose with""",
        text,
    )

    replacements = {
        "/frxnls:": "$",
        "via the `Agent` tool": "through Codex subagent delegation",
        "via `Agent`": "through Codex subagent delegation",
        "the `Agent` tool": "Codex subagent tools",
        "The `Agent` tool": "Codex subagent tools",
        "Agent tool's": "subagent's",
        "Agent tool": "Codex subagent tools",
        "generic `Agent` (general-purpose)": "built-in `default` subagent",
        "`AskUserQuestion`": "a direct question to the user",
        "AskUserQuestion": "a direct question to the user",
        "`ToolSearch`": "the available tool catalog",
        "ToolSearch": "the available tool catalog",
        "`WebSearch`": "web search",
        "`WebFetch`": "web access",
        ".claude/plans/": "docs/plans/",
        ".claude/agent-memory/": ".codex/agent-memory/",
        "<REPO_ROOT>/.claude/": "<REPO_ROOT>/.codex/",
        "claude/issue-": "codex/issue-",
        "claude/plan-": "codex/plan-",
        "claude/fix-": "codex/fix-",
        "Claude Code": "Codex",
        "${CLAUDE_PLUGIN_ROOT}/templates/": "../../templates/",
        "${CLAUDE_PLUGIN_ROOT}/skills/<skill>/references/": "references/",
        "${CLAUDE_PLUGIN_ROOT}/skills/fx-go-nogo/references/scorecard.md": "references/scorecard.md",
        "${CLAUDE_PLUGIN_ROOT}/skills/fx-market-research/references/lanes.md": "references/lanes.md",
        "${CLAUDE_PLUGIN_ROOT}/templates/ledger-entry.md": "../../templates/ledger-entry.md",
        "${CLAUDE_PLUGIN_ROOT}/templates/constraints.md": "../../templates/constraints.md",
        "${CLAUDE_PLUGIN_ROOT}/templates/brief.md": "../../templates/brief.md",
        "user's auto-memory block in your system prompt (Codex)": "available Codex memory or Chronicle context",
        "(auto memory)": "(memory context)",
        "Co-Authored-By: Claude <noreply@anthropic.com>": "",
        "🤖 Generated with [Codex](https://claude.com/claude-code)": "Generated with Codex",
        "Runs on Sonnet;": "Designed for a Codex worker;",
        "Runs on sonnet;": "Designed for a Codex worker;",
        "Runs on opus by design.": "Use high reasoning for this risk-sensitive lane.",
        "run on opus deliberately": "use high reasoning deliberately",
        "sub-agent on Sonnet": "Codex worker subagent",
        "Agent(s)": "Subagent(s)",
        "anything in CLAUDE.md": "anything in AGENTS.md or CLAUDE.md",
        "Anything already documented in CLAUDE.md files": "Anything already documented in AGENTS.md or CLAUDE.md files",
        "CLAUDE.md, or current-task details": "AGENTS.md or CLAUDE.md, or current-task details",
        "or CLAUDE.md files": "or AGENTS.md/CLAUDE.md files",
        "search repo for: CLAUDE.md": "search repo for: AGENTS.md, CLAUDE.md",
        "read CLAUDE.md/README/config": "read AGENTS.md (or CLAUDE.md as a fallback), README, and config",
        "(especially under `docs/plans/` or `docs/plans/`)": "(especially under `docs/plans/`)",
        "#$ARGUMENTS": "<user-provided input>",
        "$ARGUMENTS": "the user-provided input",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\bfrxnls:([a-z0-9-]+)\b", r"$\1", text)
    text = re.sub(
        r" \(default: (?:sonnet|opus|haiku).*?\)",
        " (model selected by Codex session policy)",
        text,
    )
    text = re.sub(
        r"- Models: simplicity=sonnet.*?\n",
        "- Models: selected by Codex session policy\n",
        text,
    )
    text = text.replace(
        "`rolls/partition → 2` makes it 6 sonnet passes",
        "`rolls/partition → 2` makes it 6 passes",
    )
    text = text.replace(
        "The risk lane is tiered to `opus` by default while the other seven run `sonnet`.",
        "The risk lane should use high reasoning; let Codex select the concrete models.",
    )
    text = text.replace(
        "Grep `.claude/skills/**/SKILL.md` and hook files",
        "Grep `.agents/skills/**/SKILL.md`, `.codex/**`, `.claude/skills/**/SKILL.md`, and hook files",
    )
    text = re.sub(
        r"Spawn via `Agent\(fx-lane-researcher\)` and `Agent\(fx-risk-researcher\)`;.*?\n\n",
        "Spawn the lanes using the role mapping in `../../references/runtime.md`; "
        "the specialist skills carry the evidence rules.\n\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def render_skill(source_path: Path) -> str:
    frontmatter, body = codex_frontmatter(source_path.read_text())
    return rewrite_for_codex(frontmatter + "\n" + CODEX_NOTE + body)


def copy_skill(source_root: Path, destination_root: Path) -> None:
    destination_root.mkdir(parents=True, exist_ok=True)
    (destination_root / "SKILL.md").write_text(render_skill(source_root / "SKILL.md"))
    for directory_name in SUPPORT_DIRS:
        source_directory = source_root / directory_name
        if source_directory.is_dir():
            shutil.copytree(
                source_directory,
                destination_root / directory_name,
                dirs_exist_ok=True,
            )
            for copied_file in (destination_root / directory_name).rglob("*"):
                if copied_file.is_file() and copied_file.suffix in {".md", ".yaml", ".yml"}:
                    copied_file.write_text(rewrite_for_codex(copied_file.read_text()))


def build(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for source_root in sorted(path.parent for path in SOURCE_SKILLS.glob("*/SKILL.md")):
        copy_skill(source_root, destination / source_root.name)

    for agent_path in sorted(SOURCE_AGENTS.glob("*.md")):
        skill_root = destination / agent_path.stem
        skill_root.mkdir(parents=True, exist_ok=True)
        (skill_root / "SKILL.md").write_text(render_skill(agent_path))


def build_templates(destination: Path) -> None:
    shutil.copytree(SOURCE_TEMPLATES, destination, dirs_exist_ok=True)


def files_under(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def validate_generated(root: Path) -> None:
    skill_files = sorted(root.glob("*/SKILL.md"))
    if len(skill_files) != EXPECTED_SKILLS:
        raise ValueError(
            f"expected {EXPECTED_SKILLS} generated skills, found {len(skill_files)}"
        )

    for skill_file in skill_files:
        text = skill_file.read_text()
        frontmatter, _ = codex_frontmatter(text)
        top_level_fields = {
            match.group(1)
            for match in re.finditer(r"^([A-Za-z][A-Za-z0-9_-]*):", frontmatter, re.MULTILINE)
        }
        if top_level_fields != {"name", "description"}:
            raise ValueError(
                f"{skill_file.relative_to(root)} has unsupported frontmatter fields: "
                f"{sorted(top_level_fields - {'name', 'description'})}"
            )

    for generated_file in sorted(root.rglob("*")):
        if not generated_file.is_file() or generated_file.suffix not in {
            ".md",
            ".yaml",
            ".yml",
        }:
            continue
        text = generated_file.read_text()
        for forbidden in FORBIDDEN_GENERATED_TEXT:
            if forbidden in text:
                raise ValueError(
                    f"{generated_file.relative_to(root)} still contains {forbidden!r}"
                )


def check(expected_root: Path, actual_root: Path) -> int:
    expected = files_under(expected_root)
    actual = files_under(actual_root)
    if expected == actual:
        print(f"Codex skills are current ({len(actual)} files).")
        return 0

    for path in sorted(set(expected) | set(actual)):
        if path not in actual:
            print(f"missing generated file: {path}")
        elif path not in expected:
            print(f"stale generated file: {path}")
        elif expected[path] != actual[path]:
            try:
                before = actual[path].decode().splitlines(keepends=True)
                after = expected[path].decode().splitlines(keepends=True)
            except UnicodeDecodeError:
                print(f"changed generated binary: {path}")
            else:
                print("".join(difflib.unified_diff(before, after, path, path)))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when committed Codex skills differ from generated output.",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="frxnls-codex-build-") as temp_dir:
        generated = Path(temp_dir) / "skills"
        generated_templates = Path(temp_dir) / "templates"
        build(generated)
        build_templates(generated_templates)
        validate_generated(generated)
        if args.check:
            skills_result = check(generated, OUTPUT_SKILLS)
            templates_result = check(generated_templates, OUTPUT_TEMPLATES)
            return max(skills_result, templates_result)

        if OUTPUT_SKILLS.exists():
            shutil.rmtree(OUTPUT_SKILLS)
        shutil.copytree(generated, OUTPUT_SKILLS)
        if OUTPUT_TEMPLATES.exists():
            shutil.rmtree(OUTPUT_TEMPLATES)
        shutil.copytree(generated_templates, OUTPUT_TEMPLATES)
        print(
            f"Generated {len(files_under(OUTPUT_SKILLS))} Codex skill files "
            f"and {len(files_under(OUTPUT_TEMPLATES))} templates."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
