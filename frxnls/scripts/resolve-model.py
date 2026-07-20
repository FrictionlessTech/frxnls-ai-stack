#!/usr/bin/env python3
"""Resolve the effective Claude Code model alias for a frxnls spawn key.

Usage:
    resolve-model.py <key> [--repo-root PATH]   -> one alias on stdout, exit 0 always
    resolve-model.py --all [--repo-root PATH]   -> JSON map of every known key, exit 0 always
    resolve-model.py --check                    -> lint agent frontmatter vs the defaults
                                                    map; exit 1 on drift (the one mode
                                                    allowed to fail — it's a lint, not a
                                                    resolution)

Resolution: repo defaults live in `model-defaults.json` (a sibling of this script's
parent directory). A project may override individual keys via a config file at
`<repo-root>/.frxnls/model-tiers.json` — a flat JSON map of the same keys to a Claude
Code model alias (`haiku` / `sonnet` / `opus`). `--repo-root` defaults to the git root
of the current working directory (or the cwd itself, if that's not a git repo).

Never-fail contract: resolution modes (bare `<key>`, `--all`) always exit 0 and print
exactly the resolved value(s) to stdout — no trailing prose, so command substitution
in a caller's Bash step is safe. A missing/unreadable/malformed config file, an unknown
key in the config, or a config value that isn't a known alias all degrade silently to
the repo default; a warning is written to stderr but resolution never aborts. An
unknown key requested on the command line falls back to "sonnet" (never leaves a
spawner stranded with no model at all).

Pure-stdlib (no PyYAML/third-party deps) — the plugin has no guaranteed non-stdlib
python3 dependency at any install site. Adapted from the existing script precedent in
this repo: frxnls/skills/fx-compound/scripts/validate-frontmatter.py.
"""
import argparse
import json
import os
import re
import subprocess
import sys

KNOWN_ALIASES = {"haiku", "sonnet", "opus"}
DEFAULT_FALLBACK = "sonnet"
CONFIG_RELATIVE_PATH = os.path.join(".frxnls", "model-tiers.json")
FRONTMATTER_MODEL_RE = re.compile(r'^model:\s*"?([A-Za-z0-9_-]+)"?\s*(#.*)?$')


def _script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def load_defaults() -> dict:
    """Load the canonical defaults map. Never raises — an unreadable/missing map
    degrades to an empty map, so every key falls back to DEFAULT_FALLBACK."""
    defaults_path = os.path.join(_script_dir(), "..", "model-defaults.json")
    try:
        with open(defaults_path) as f:
            data = json.load(f)
    except Exception as e:
        sys.stderr.write(
            f"resolve-model: could not load defaults map at {defaults_path}: {e}\n"
        )
        return {}
    if not isinstance(data, dict):
        sys.stderr.write(f"resolve-model: defaults map at {defaults_path} is not a JSON object\n")
        return {}
    return data


def find_git_root(start: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", start, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return start


def load_config(repo_root: str) -> dict:
    """Load the project override file. Never raises — missing, unreadable, or
    malformed all degrade to an empty override map (repo defaults apply)."""
    config_path = os.path.join(repo_root, CONFIG_RELATIVE_PATH)
    if not os.path.isfile(config_path):
        return {}
    try:
        with open(config_path) as f:
            data = json.load(f)
    except Exception:
        # Fixed-vocabulary message only — never echo the exception text, which could
        # embed a fragment of the (potentially attacker-authored) config content.
        sys.stderr.write(
            f"resolve-model: warning: {CONFIG_RELATIVE_PATH} is unreadable or not "
            "valid JSON; using repo defaults.\n"
        )
        return {}
    if not isinstance(data, dict):
        sys.stderr.write(
            f"resolve-model: warning: {CONFIG_RELATIVE_PATH} does not contain a "
            "JSON object; using repo defaults.\n"
        )
        return {}
    return data


def _resolve_known(key: str, default_value: str, config: dict) -> str:
    """`key` here is always a name drawn from `model-defaults.json` (fixed,
    plugin-controlled vocabulary) — safe to echo. `value` comes straight from the
    project's `.frxnls/model-tiers.json` and may be attacker-controlled (a PR can
    ship its own config file); it is NEVER echoed to stderr, and its type is never
    trusted — `value in KNOWN_ALIASES` alone would raise TypeError for an
    unhashable override (a list/dict), which the `isinstance` guard prevents."""
    if key in config:
        value = config[key]
        if isinstance(value, str) and value in KNOWN_ALIASES:
            return value
        sys.stderr.write(
            f"resolve-model: warning: ignored invalid value for key '{key}' in "
            f"{CONFIG_RELATIVE_PATH} (not a known alias: haiku/sonnet/opus); "
            "using default.\n"
        )
    return default_value


def resolve_key(key: str, defaults: dict, config: dict) -> str:
    if key not in defaults:
        sys.stderr.write(
            f"resolve-model: unknown key '{key}' requested; falling back to "
            f"'{DEFAULT_FALLBACK}'.\n"
        )
        return DEFAULT_FALLBACK
    return _resolve_known(key, defaults[key], config)


def resolve_all(defaults: dict, config: dict) -> dict:
    resolved = {key: _resolve_known(key, value, config) for key, value in defaults.items()}
    # Count only — never echo the unknown key names themselves. They come straight
    # from the project's .frxnls/model-tiers.json, which a PR could author, so an
    # arbitrary/attacker-chosen key string must never be surfaced verbatim.
    unknown_count = sum(1 for key in config if key not in defaults)
    if unknown_count:
        sys.stderr.write(
            f"resolve-model: warning: ignored {unknown_count} unknown key(s) in "
            f"{CONFIG_RELATIVE_PATH}.\n"
        )
    return resolved


def parse_frontmatter_model(path: str):
    with open(path) as f:
        lines = f.read().split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = FRONTMATTER_MODEL_RE.match(line)
        if m:
            return m.group(1)
    return None


def run_check() -> int:
    """Lint each frxnls/agents/*.md frontmatter `model:` value against the defaults
    map. This is the one mode allowed to fail — it's a lint, not a resolution."""
    defaults = load_defaults()
    agents_dir = os.path.join(_script_dir(), "..", "agents")
    if not os.path.isdir(agents_dir):
        sys.stderr.write(f"resolve-model --check: agents dir not found at {agents_dir}\n")
        return 1

    drift = []
    for filename in sorted(os.listdir(agents_dir)):
        if not filename.endswith(".md"):
            continue
        agent_key = filename[: -len(".md")]
        path = os.path.join(agents_dir, filename)
        model = parse_frontmatter_model(path)
        if agent_key not in defaults:
            if model is not None:
                drift.append(
                    f"{path}: has frontmatter 'model: {model}' but no corresponding "
                    f"key '{agent_key}' in model-defaults.json"
                )
            continue
        if model is None:
            drift.append(f"{path}: no 'model:' frontmatter field found")
        elif model != defaults[agent_key]:
            drift.append(
                f"{path}: frontmatter model '{model}' != defaults map "
                f"'{defaults[agent_key]}' for key '{agent_key}'"
            )

    if drift:
        sys.stderr.write("resolve-model --check: frontmatter drift detected:\n")
        for line in drift:
            sys.stderr.write(f"  {line}\n")
        return 1

    print("resolve-model --check: OK — agent frontmatter agrees with the defaults map.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resolve-model.py",
        description="Resolve the effective Claude Code model alias for a frxnls spawn key.",
    )
    parser.add_argument("key", nargs="?", help="model key to resolve, e.g. plan-implementer")
    parser.add_argument(
        "--all", action="store_true", help="print the full resolved key->model map as JSON"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="lint frxnls/agents/*.md frontmatter model: values against the defaults map",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="repo root for locating .frxnls/model-tiers.json (default: git root of cwd)",
    )
    return parser


def main(argv: list) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    if args.check:
        return run_check()

    defaults = load_defaults()
    repo_root = args.repo_root or find_git_root(os.getcwd())
    config = load_config(repo_root)

    if args.all:
        resolved = resolve_all(defaults, config)
        print(json.dumps(resolved, sort_keys=True))
        return 0

    if not args.key:
        sys.stderr.write("resolve-model: missing <key> argument (or use --all / --check)\n")
        print(DEFAULT_FALLBACK)
        return 0

    print(resolve_key(args.key, defaults, config))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
