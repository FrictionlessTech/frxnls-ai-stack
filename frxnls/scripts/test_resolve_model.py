#!/usr/bin/env python3
"""Self-contained stdlib tests for resolve-model.py.

Run directly (no test runner / pytest dependency):
    python3 frxnls/scripts/test_resolve_model.py

Exercises the never-fail contract (AE2/AE3/AE4 from the plan): resolution modes
always exit 0 with exactly one alias (or a JSON map) on stdout, regardless of a
missing, malformed, unreadable, or partially-unknown project config. Shells out to
the real script via subprocess so the tests exercise the actual CLI contract
callers (Bash steps in skills/agents) depend on.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOLVER = os.path.join(SCRIPT_DIR, "resolve-model.py")
DEFAULTS_PATH = os.path.join(SCRIPT_DIR, "..", "model-defaults.json")

with open(DEFAULTS_PATH) as f:
    REAL_DEFAULTS = json.load(f)


def run_resolver(args, cwd=None):
    return subprocess.run(
        [sys.executable, RESOLVER] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
    )


def write_config(repo_root, content):
    frxnls_dir = os.path.join(repo_root, ".frxnls")
    os.makedirs(frxnls_dir, exist_ok=True)
    config_path = os.path.join(frxnls_dir, "model-tiers.json")
    with open(config_path, "w") as f:
        f.write(content)
    return config_path


class ResolveModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="resolve-model-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- No config file: defaults apply exactly (AE2) --------------------

    def test_no_config_all_matches_defaults(self):
        result = run_resolver(["--all", "--repo-root", self.tmp])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), REAL_DEFAULTS)

    def test_no_config_single_key_matches_default(self):
        result = run_resolver(["plan-implementer", "--repo-root", self.tmp])
        self.assertEqual(result.returncode, 0)
        # Exactly one alias, no trailing prose — safe for command substitution.
        self.assertEqual(result.stdout, "sonnet\n")
        self.assertEqual(result.stderr, "")

    # -- Config overrides one key ------------------------------------------

    def test_config_overrides_one_key_only(self):
        write_config(self.tmp, json.dumps({"rex-code-reviewer.security": "sonnet"}))
        result = run_resolver(["rex-code-reviewer.security", "--repo-root", self.tmp])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "sonnet")

        result_all = run_resolver(["--all", "--repo-root", self.tmp])
        self.assertEqual(result_all.returncode, 0)
        resolved = json.loads(result_all.stdout)
        expected = dict(REAL_DEFAULTS)
        expected["rex-code-reviewer.security"] = "sonnet"
        self.assertEqual(resolved, expected)

    # -- Malformed JSON config: defaults apply, warning on stderr (AE3) ----

    def test_malformed_config_falls_back_to_defaults(self):
        write_config(self.tmp, "{not valid json")
        result = run_resolver(["--all", "--repo-root", self.tmp])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), REAL_DEFAULTS)
        self.assertTrue(result.stderr.strip(), "expected a stderr warning")

    # -- Config with unknown key: ignored, known keys unaffected (AE4) -----

    def test_unknown_config_key_ignored(self):
        write_config(
            self.tmp,
            json.dumps({"rex-code-reviewer.styling": "haiku", "plan-implementer": "sonnet"}),
        )
        result = run_resolver(["--all", "--repo-root", self.tmp])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), REAL_DEFAULTS)
        self.assertIn("unknown key", result.stderr.lower())

    # -- Config value not a known alias: falls back to default -------------

    def test_config_value_not_known_alias_falls_back(self):
        write_config(self.tmp, json.dumps({"plan-implementer": "gpt5"}))
        result = run_resolver(["plan-implementer", "--repo-root", self.tmp])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), REAL_DEFAULTS["plan-implementer"])
        self.assertIn("not a known alias", result.stderr.lower())

    # -- Unknown key requested as an argument: falls back to sonnet ---------

    def test_unknown_key_argument_falls_back_to_sonnet(self):
        result = run_resolver(["totally-unknown-key", "--repo-root", self.tmp])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "sonnet")
        self.assertIn("unknown key", result.stderr.lower())

    # -- Config file unreadable (permissions): defaults, exit 0 ------------

    @unittest.skipIf(
        os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() == 0),
        "permission bits are meaningless for root / non-posix",
    )
    def test_unreadable_config_falls_back_to_defaults(self):
        config_path = write_config(self.tmp, json.dumps({"plan-implementer": "opus"}))
        os.chmod(config_path, 0)
        try:
            result = run_resolver(["--all", "--repo-root", self.tmp])
        finally:
            os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), REAL_DEFAULTS)

    # -- Resolver works from an arbitrary cwd (not the plugin dir) ----------

    def test_resolves_from_arbitrary_cwd(self):
        result = run_resolver(["--all", "--repo-root", self.tmp], cwd=self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), REAL_DEFAULTS)

    # -- --check ------------------------------------------------------------

    def test_check_passes_against_real_agent_frontmatter(self):
        result = run_resolver(["--check"])
        self.assertEqual(
            result.returncode, 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )

    def test_check_fails_on_drifted_frontmatter(self):
        fake_root = os.path.join(self.tmp, "plugin")
        scripts_dir = os.path.join(fake_root, "scripts")
        agents_dir = os.path.join(fake_root, "agents")
        os.makedirs(scripts_dir)
        os.makedirs(agents_dir)
        shutil.copy(RESOLVER, os.path.join(scripts_dir, "resolve-model.py"))
        shutil.copy(DEFAULTS_PATH, os.path.join(fake_root, "model-defaults.json"))

        drifted_path = os.path.join(agents_dir, "plan-implementer.md")
        with open(drifted_path, "w") as f:
            f.write('---\nname: "plan-implementer"\nmodel: opus\n---\n\nbody\n')

        result = subprocess.run(
            [sys.executable, os.path.join(scripts_dir, "resolve-model.py"), "--check"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("plan-implementer.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
