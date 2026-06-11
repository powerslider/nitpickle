"""Tests for the house-style hook. Stdlib only, run with:

    python3 -m unittest discover -s hooks -p "test_*.py"

Banned characters are built with chr() so this file never contains one, which
keeps the live hook from blocking edits to the tests themselves.
"""
import json
import os
import subprocess
import sys
import unittest

HOOK = os.path.join(os.path.dirname(__file__), "no-emdash-semicolon.py")
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


def run_hook(stdin_text):
    return subprocess.run(
        [sys.executable, HOOK],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def hook_input(path, content):
    return json.dumps({"tool_input": {"file_path": path, "content": content}})


def denied(result):
    if not result.stdout.strip():
        return False
    decision = json.loads(result.stdout)
    return (
        decision["hookSpecificOutput"]["permissionDecision"] == "deny"
    )


class TestDashes(unittest.TestCase):
    def test_clean_text_passes(self):
        result = run_hook(hook_input("a.md", "Plain prose, no problems."))
        self.assertEqual(result.returncode, 0)
        self.assertFalse(denied(result))

    def test_literal_em_dash_blocked_any_file(self):
        result = run_hook(hook_input("a.py", "x = 1 " + EM_DASH + " note"))
        self.assertTrue(denied(result))

    def test_literal_en_dash_blocked_any_file(self):
        result = run_hook(hook_input("a.txt", "range 1" + EN_DASH + "2"))
        self.assertTrue(denied(result))

    def test_entity_dash_blocked_in_md_prose(self):
        result = run_hook(hook_input("a.md", "wrong &mdash" + "; punctuation"))
        self.assertTrue(denied(result))

    def test_entity_dash_in_code_span_allowed(self):
        result = run_hook(hook_input("a.md", "the `&mdash` + `;` entity"))
        self.assertFalse(denied(result))

    def test_entity_dash_in_non_md_allowed(self):
        result = run_hook(hook_input("a.py", 'E = "&mdash' + ';"'))
        self.assertFalse(denied(result))


class TestSemicolons(unittest.TestCase):
    def test_semicolon_in_md_prose_blocked(self):
        result = run_hook(hook_input("a.md", "first clause" + chr(0x3B) + " second"))
        self.assertTrue(denied(result))

    def test_semicolon_in_fenced_block_allowed(self):
        content = "prose\n```c\nint x = 1" + chr(0x3B) + "\n```\nmore prose"
        result = run_hook(hook_input("a.md", content))
        self.assertFalse(denied(result))

    def test_semicolon_in_inline_code_allowed(self):
        result = run_hook(hook_input("a.md", "run `x = 1" + chr(0x3B) + "` now"))
        self.assertFalse(denied(result))

    def test_semicolon_in_non_md_allowed(self):
        result = run_hook(hook_input("a.go", "x := 1" + chr(0x3B) + " y := 2"))
        self.assertFalse(denied(result))

    def test_unmatched_fence_fails_open(self):
        content = "prose\n```c\nint x = 1" + chr(0x3B) + "\nno closing fence"
        result = run_hook(hook_input("a.md", content))
        self.assertEqual(result.returncode, 0)
        self.assertFalse(denied(result))


class TestInputHandling(unittest.TestCase):
    def test_malformed_json_allows_with_diagnostic(self):
        result = run_hook("this is not json")
        self.assertEqual(result.returncode, 0)
        self.assertFalse(denied(result))
        self.assertIn("unreadable input", result.stderr)

    def test_empty_input_object_passes(self):
        result = run_hook(json.dumps({"tool_input": {}}))
        self.assertEqual(result.returncode, 0)
        self.assertFalse(denied(result))

    def test_multiedit_edits_array_checked(self):
        payload = json.dumps({
            "tool_input": {
                "file_path": "a.md",
                "edits": [
                    {"new_string": "clean text"},
                    {"new_string": "bad " + EM_DASH + " dash"},
                ],
            }
        })
        result = run_hook(payload)
        self.assertTrue(denied(result))


if __name__ == "__main__":
    unittest.main()
