"""Tests for the repo consistency validator. Stdlib only, run with:

    python3 -m unittest discover -s tools -p "test_*.py"

The validator is what keeps 38 marker-delimited block copies identical across
both harness trees, so these pin that it actually rejects drift rather than
passing vacuously.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IGNORE = shutil.ignore_patterns(".git", "__pycache__", "node_modules", "*.pyc")


def run_validator(root):
    return subprocess.run(
        [sys.executable, os.path.join(root, "tools", "validate.py"), root],
        capture_output=True, text=True,
    )


class ValidatorRejectsDrift(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "repo")
        shutil.copytree(REPO, self.root, ignore=IGNORE)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def edit(self, rel, old, new):
        path = os.path.join(self.root, rel)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn(old, text, f"{rel} no longer contains the anchor text")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new, 1))

    def test_unmodified_copy_passes(self):
        result = run_validator(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_block_copy_drifting_from_its_home_is_caught(self):
        self.edit(
            os.path.join("skills", "codex", "review-pr", "REVIEW-FORMAT.md"),
            "Cap at `review.mutation_max`, default 12.",
            "Cap at `review.mutation_max`, default 20.",
        )
        result = run_validator(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nitpickle:mutation", result.stdout)

    def test_load_bearing_term_without_a_glossary_entry_is_caught(self):
        self.edit("CONTEXT.md", "- **Mutation battery**", "- **Mutation batteries**")
        result = run_validator(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Mutation battery", result.stdout)


if __name__ == "__main__":
    unittest.main()
