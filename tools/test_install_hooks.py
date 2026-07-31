"""Tests for the Codex guardrail installer. Stdlib only, run with:

    python3 -m unittest discover -s tools -p "test_*.py"
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install-hooks.py")


def _ours(cfg):
    marks = ("no-agent-writes.py", "no-emdash-semicolon.py")
    return [
        e for e in cfg["hooks"]["PreToolUse"]
        if any(any(m in h.get("command", "") for m in marks) for h in e.get("hooks", []))
    ]


class TestInstallHooks(unittest.TestCase):
    def test_cli_wires_guardrail_without_skills(self):
        with tempfile.TemporaryDirectory() as home:
            r = subprocess.run([sys.executable, SCRIPT, home], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            for script in ("no-agent-writes.py", "no-emdash-semicolon.py"):
                self.assertTrue(os.path.isfile(
                    os.path.join(home, ".config", "nitpickle", "hooks", script)))
            with open(os.path.join(home, ".codex", "hooks.json"), encoding="utf-8") as f:
                cfg = json.load(f)
            matchers = [e["matcher"] for e in cfg["hooks"]["PreToolUse"]]
            self.assertIn("^Bash$", matchers)
            self.assertIn("^apply_patch$", matchers)
            self.assertFalse(os.path.isdir(os.path.join(home, ".agents", "skills")))

    def test_preserves_user_hooks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as home:
            codex = os.path.join(home, ".codex")
            os.makedirs(codex)
            with open(os.path.join(codex, "hooks.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "hooks": {"PreToolUse": [
                        {"matcher": "^Bash$", "hooks": [{"type": "command", "command": "mine.sh"}]},
                    ]},
                    "otherUserSetting": True,
                }, f)
            subprocess.run([sys.executable, SCRIPT, home], check=True)
            subprocess.run([sys.executable, SCRIPT, home], check=True)  # idempotent
            with open(os.path.join(codex, "hooks.json"), encoding="utf-8") as f:
                cfg = json.load(f)
            self.assertTrue(cfg.get("otherUserSetting"))
            self.assertIn("mine.sh", json.dumps(cfg))
            self.assertEqual(len(_ours(cfg)), 2)


if __name__ == "__main__":
    unittest.main()
