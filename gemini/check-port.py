#!/usr/bin/env python3
"""Drift check for the Gemini CLI port of the frxnls venture loop.

Usage:
    gemini/check-port.py            -> report; exit 1 on any failure

Checks, in order:
  1. gemini-extension.json parses and names itself correctly.
  2. Every commands/*.toml parses and carries a prompt with {{args}}.
  3. Every SKILL.md / agents/*.md has frontmatter whose `name` matches its path,
     and a non-empty `description`.
  4. Assets shared with the Claude Code plugin are byte-identical. This is the
     check that actually earns its keep: the templates, lane briefs, and
     scorecard are the substance, and silent divergence there means the two
     copies of the loop start scoring the same idea differently.
  5. No Claude-only tool name or path variable leaked into the Gemini tree.
  6. Skill and agent sets match between the two trees.

Pure stdlib, matching the precedent set by frxnls/scripts/resolve-model.py.
tomllib is 3.11+; on older interpreters the TOML check degrades to a warning
rather than a failure, since it isn't the check that catches real drift.
"""
import json
import os
import re
import sys

try:
    import tomllib
except ImportError:  # < 3.11
    tomllib = None

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEM = os.path.join(REPO_ROOT, "gemini", "frxnls-venture")
CLAUDE = os.path.join(REPO_ROOT, "frxnls")

# (path under gemini/frxnls-venture, path under frxnls) — must stay byte-identical.
SHARED_ASSETS = [
    ("skills/fx-idea-scout/templates/brief.md", "templates/brief.md"),
    ("skills/fx-idea-scout/templates/constraints.md", "templates/constraints.md"),
    ("skills/fx-idea-scout/templates/ledger-entry.md", "templates/ledger-entry.md"),
    (
        "skills/fx-market-research/references/lanes.md",
        "skills/fx-market-research/references/lanes.md",
    ),
    (
        "skills/fx-go-nogo/references/scorecard.md",
        "skills/fx-go-nogo/references/scorecard.md",
    ),
]

# Ported skills/agents. The Gemini tree is a subset of the plugin by design —
# only the venture loop is ported, not the delivery pipeline.
PORTED_SKILLS = ["fx-idea-scout", "fx-market-research", "fx-go-nogo"]
PORTED_AGENTS = ["fx-screen-scout", "fx-lane-researcher", "fx-risk-researcher"]

# Claude-only names that must never appear in the Gemini tree. Substring match;
# the values are distinctive enough not to collide with ordinary English.
FORBIDDEN = [
    "CLAUDE_PLUGIN_ROOT",
    "AskUserQuestion",
    "WebSearch",
    "WebFetch",
    "resolve-model",
    "allowed-tools",
    "argument-hint",
]
# Files exempt from the forbidden-name scan: the README documents the mapping and
# necessarily names both sides.
FORBIDDEN_EXEMPT = {"README.md"}

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)

failures = []
warnings = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL  {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"WARN  {msg}")


def ok(msg):
    print(f"ok    {msg}")


def check_manifest():
    path = os.path.join(GEM, "gemini-extension.json")
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        return fail(f"gemini-extension.json unreadable: {e}")
    if data.get("name") != "frxnls-venture":
        return fail(f"manifest name is {data.get('name')!r}, expected 'frxnls-venture'")
    if not data.get("version"):
        return fail("manifest has no version")
    ok(f"manifest: {data['name']} v{data['version']}")


def check_commands():
    cmd_dir = os.path.join(GEM, "commands")
    names = sorted(f for f in os.listdir(cmd_dir) if f.endswith(".toml"))
    if not names:
        return fail("no commands/*.toml found")
    for name in names:
        path = os.path.join(cmd_dir, name)
        raw = open(path, "rb").read()
        if tomllib is None:
            warn(f"commands/{name}: TOML not parsed (python < 3.11)")
            continue
        try:
            data = tomllib.loads(raw.decode())
        except Exception as e:
            fail(f"commands/{name} is not valid TOML: {e}")
            continue
        if "prompt" not in data:
            fail(f"commands/{name} has no `prompt`")
        elif "{{args}}" not in data["prompt"]:
            fail(f"commands/{name} prompt has no {{{{args}}}} placeholder")
        else:
            ok(f"command /{name[:-5]}")


def check_frontmatter():
    targets = [
        (os.path.join(GEM, "skills", s, "SKILL.md"), s) for s in PORTED_SKILLS
    ] + [(os.path.join(GEM, "agents", a + ".md"), a) for a in PORTED_AGENTS]
    for path, expected in targets:
        rel = os.path.relpath(path, GEM)
        if not os.path.exists(path):
            fail(f"{rel} is missing")
            continue
        text = open(path).read()
        m = FRONTMATTER_RE.match(text)
        if not m:
            fail(f"{rel} has no YAML frontmatter")
            continue
        fm = m.group(1)
        name_m = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
        if not name_m:
            fail(f"{rel} frontmatter has no `name`")
        elif name_m.group(1) != expected:
            fail(f"{rel} declares name {name_m.group(1)!r}, expected {expected!r}")
        desc_m = re.search(r"^description:\s*(\S.*)$", fm, re.M)
        if not desc_m:
            fail(f"{rel} frontmatter has no `description`")
        else:
            ok(f"frontmatter {rel}")


def check_pinned_models():
    """A pinned `model:` in agent frontmatter is a silent-failure risk.

    Antigravity dropped fx-screen-scout from its registry entirely when it
    pinned `gemini-3-flash-preview` — no error, the agent simply never appeared
    in /agents, and the skill that delegates to it would have failed at runtime.
    Neither runtime supports per-invocation overrides anyway, so a pin buys
    little and costs a whole agent when the id stops resolving.
    """
    for agent in PORTED_AGENTS:
        path = os.path.join(GEM, "agents", agent + ".md")
        if not os.path.exists(path):
            continue
        m = FRONTMATTER_RE.match(open(path).read())
        if not m:
            continue
        pin = re.search(r"^model:\s*(\S+)\s*$", m.group(1), re.M)
        if pin:
            fail(
                f"agents/{agent}.md pins model {pin.group(1)!r} — runtimes drop "
                f"agents with unresolvable model ids silently; verify it appears "
                f"in /agents or remove the key"
            )
    if not any("pins model" in f for f in failures):
        ok("no agent pins a model id (silent-drop risk)")


def check_shared_assets():
    for gem_rel, claude_rel in SHARED_ASSETS:
        gem_path = os.path.join(GEM, gem_rel)
        claude_path = os.path.join(CLAUDE, claude_rel)
        if not os.path.exists(gem_path):
            fail(f"shared asset missing from Gemini tree: {gem_rel}")
            continue
        if not os.path.exists(claude_path):
            fail(f"shared asset missing from Claude tree: {claude_rel}")
            continue
        a, b = open(gem_path, "rb").read(), open(claude_path, "rb").read()
        if a != b:
            fail(
                f"DRIFT: {gem_rel} differs from frxnls/{claude_rel} "
                f"— re-copy or reconcile intentionally"
            )
        else:
            ok(f"shared asset in sync: {gem_rel}")


def check_forbidden():
    hits = []
    for root, _dirs, files in os.walk(GEM):
        for name in files:
            if name in FORBIDDEN_EXEMPT or not name.endswith((".md", ".toml", ".json")):
                continue
            path = os.path.join(root, name)
            text = open(path, errors="replace").read()
            for pat in FORBIDDEN:
                if pat in text:
                    hits.append((os.path.relpath(path, GEM), pat))
    for rel, pat in hits:
        fail(f"Claude-only name {pat!r} leaked into {rel}")
    if not hits:
        ok("no Claude-only tool names or path variables in the Gemini tree")


def check_parity():
    for s in PORTED_SKILLS:
        src = os.path.join(CLAUDE, "skills", s, "SKILL.md")
        if not os.path.exists(src):
            fail(f"ported skill {s} no longer exists in frxnls/skills/ — port is stale")
    for a in PORTED_AGENTS:
        src = os.path.join(CLAUDE, "agents", a + ".md")
        if not os.path.exists(src):
            fail(f"ported agent {a} no longer exists in frxnls/agents/ — port is stale")
    if not failures:
        ok("every ported component still exists upstream")


def main():
    if not os.path.isdir(GEM):
        print(f"FAIL  no Gemini tree at {GEM}")
        return 1
    print(f"Checking {os.path.relpath(GEM, REPO_ROOT)} against frxnls/\n")
    check_manifest()
    check_commands()
    check_frontmatter()
    check_pinned_models()
    check_shared_assets()
    check_forbidden()
    check_parity()
    print()
    if failures:
        print(f"{len(failures)} failure(s), {len(warnings)} warning(s)")
        return 1
    print(f"all checks passed ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
