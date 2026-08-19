"""Tests for the global-defaults seeder. Stdlib only, run with:

    python3 -m unittest discover -s tools -p "test_*.py"
"""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed_defaults import seed_defaults

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_defaults.py")


def _fake_root(root, files):
    src = os.path.join(root, "defaults", "nitpickle")
    os.makedirs(src)
    for name, body in files.items():
        with open(os.path.join(src, name), "w", encoding="utf-8") as f:
            f.write(body)


class TestSeedDefaults(unittest.TestCase):
    def test_globs_every_default_including_a_new_file(self):
        # A newly added default is seeded with no change to the seeder, because it
        # globs the directory rather than naming files.
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as home:
            _fake_root(root, {"policy.yaml": "a", "principles.md": "b", "new-default.md": "c"})
            dst_dir, seeded, skipped = seed_defaults(root, "claude", home)
            self.assertEqual(sorted(seeded), ["new-default.md", "policy.yaml", "principles.md"])
            self.assertEqual(skipped, [])
            self.assertTrue(os.path.isfile(os.path.join(dst_dir, "principles.md")))
            self.assertTrue(os.path.isfile(os.path.join(dst_dir, "new-default.md")))

    def test_non_clobber_preserves_a_customized_file(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as home:
            _fake_root(root, {"preferences.md": "shipped"})
            dst_dir, _, _ = seed_defaults(root, "claude", home)
            custom = os.path.join(dst_dir, "preferences.md")
            with open(custom, "w", encoding="utf-8") as f:
                f.write("my edits")

            _, seeded, skipped = seed_defaults(root, "claude", home)
            self.assertEqual(seeded, [])
            self.assertEqual(skipped, ["preferences.md"])
            with open(custom, encoding="utf-8") as f:
                self.assertEqual(f.read(), "my edits")

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as home:
            _fake_root(root, {"preferences.md": "shipped"})
            dst_dir, _, _ = seed_defaults(root, "claude", home)
            custom = os.path.join(dst_dir, "preferences.md")
            with open(custom, "w", encoding="utf-8") as f:
                f.write("my edits")

            _, seeded, skipped = seed_defaults(root, "claude", home, force=True)
            self.assertEqual(seeded, ["preferences.md"])
            self.assertEqual(skipped, [])
            with open(custom, encoding="utf-8") as f:
                self.assertEqual(f.read(), "shipped")

    def test_harness_target_dirs(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as home:
            _fake_root(root, {"policy.yaml": "a"})
            claude_dir, _, _ = seed_defaults(root, "claude", home)
            codex_dir, _, _ = seed_defaults(root, "codex", home)
            self.assertEqual(claude_dir, os.path.join(home, ".claude", "nitpickle"))
            self.assertEqual(codex_dir, os.path.join(home, ".config", "nitpickle"))

    def test_cli_seeds_the_real_defaults(self):
        # Smoke test against the repo's actual defaults/nitpickle, including principles.md.
        with tempfile.TemporaryDirectory() as home:
            r = subprocess.run(
                [sys.executable, SCRIPT, "--harness", "codex", "--home", home],
                capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            seeded = os.path.join(home, ".config", "nitpickle")
            self.assertTrue(os.path.isfile(os.path.join(seeded, "principles.md")))
            self.assertTrue(os.path.isfile(os.path.join(seeded, "policy.yaml")))


if __name__ == "__main__":
    unittest.main()
