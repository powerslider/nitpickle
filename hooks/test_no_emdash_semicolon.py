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

    def test_semicolon_in_code_not_comment_allowed(self):
        # Statement terminator in real code stays legal.
        result = run_hook(hook_input("a.go", "x := 1" + chr(0x3B) + " y := 2"))
        self.assertFalse(denied(result))


SEMI = chr(0x3B)


class TestSemicolonInComments(unittest.TestCase):
    def test_slash_line_comment_blocked(self):
        result = run_hook(hook_input("a.go", "x := 1\n// first" + SEMI + " second"))
        self.assertTrue(denied(result))

    def test_hash_line_comment_blocked(self):
        result = run_hook(hook_input("a.py", "x = 1  # first" + SEMI + " second"))
        self.assertTrue(denied(result))

    def test_block_comment_blocked(self):
        result = run_hook(hook_input("a.rs", "/* note" + SEMI + " here */\nfn main() {}"))
        self.assertTrue(denied(result))

    def test_clean_comment_allowed(self):
        result = run_hook(hook_input("a.go", "// a clean comment\nx := 1"))
        self.assertFalse(denied(result))

    def test_semicolon_in_string_not_flagged(self):
        # Quote consumes the marker-free string; no comment, so no violation.
        result = run_hook(hook_input("a.go", 'sep := "a' + SEMI + ' b"'))
        self.assertFalse(denied(result))

    def test_url_in_string_not_mistaken_for_comment(self):
        # The // lives inside the string, so the trailing ; is code, not comment.
        result = run_hook(hook_input("a.go", 'u := "https://x.com/a' + SEMI + 'b"'))
        self.assertFalse(denied(result))

    def test_comment_marker_for_other_language_ignored(self):
        # # is not a comment in Go, so the ; is code and passes.
        result = run_hook(hook_input("a.go", "arr := x  # not a comment" + SEMI + " ok"))
        self.assertFalse(denied(result))

    def test_quote_inside_comment_does_not_break_detection(self):
        result = run_hook(hook_input("a.go", '// he said "hi"' + SEMI + " bye"))
        self.assertTrue(denied(result))

    def test_unknown_extension_passes(self):
        result = run_hook(hook_input("a.bin", "raw" + SEMI + " data"))
        self.assertFalse(denied(result))

    def test_em_dash_in_line_comment_blocked(self):
        result = run_hook(hook_input("a.go", "// note " + EM_DASH + " here"))
        self.assertTrue(denied(result))

    def test_em_dash_in_block_comment_blocked(self):
        result = run_hook(hook_input("a.rs", "/* note " + EM_DASH + " here */"))
        self.assertTrue(denied(result))

    def test_en_dash_in_hash_comment_blocked(self):
        result = run_hook(hook_input("a.py", "x = 1  # range 1" + EN_DASH + "9"))
        self.assertTrue(denied(result))


class TestEmbeddedCodeInComments(unittest.TestCase):
    """Comment text is treated like markdown prose: fenced and inline code is
    exempt, so doctests and example snippets pass while prose stays strict."""

    def test_rust_doctest_semicolon_allowed(self):
        content = (
            "/// Adds.\n/// ```\n/// let r = add(1, 2)" + SEMI
            + "\n/// ```\nfn add(a: i32, b: i32) -> i32 { a + b }"
        )
        result = run_hook(hook_input("a.rs", content))
        self.assertFalse(denied(result))

    def test_inline_code_span_in_comment_allowed(self):
        result = run_hook(hook_input("a.go", "// call `x := 1" + SEMI + " y := 2` here"))
        self.assertFalse(denied(result))

    def test_prose_semicolon_still_blocked_with_code_present(self):
        # Fenced example is exempt, but the prose semicolon outside it is caught.
        content = "/// First do X" + SEMI + " then:\n/// ```\n/// ok()\n/// ```"
        result = run_hook(hook_input("a.rs", content))
        self.assertTrue(denied(result))

    def test_unmatched_fence_in_comment_fails_open(self):
        content = "/// ```\n/// let r = add(1, 2)" + SEMI
        result = run_hook(hook_input("a.rs", content))
        self.assertEqual(result.returncode, 0)
        self.assertFalse(denied(result))

    def test_go_tab_indented_example_allowed(self):
        content = "// Example:\n//\n//\tx := 1" + SEMI + " y := 2\nfunc Run() {}"
        result = run_hook(hook_input("a.go", content))
        self.assertFalse(denied(result))

    def test_jsdoc_example_block_allowed(self):
        content = "/**\n * @example\n * const x = 1" + SEMI + " const y = 2" + SEMI + "\n */"
        result = run_hook(hook_input("a.js", content))
        self.assertFalse(denied(result))

    def test_jsdoc_prose_after_example_still_checked(self):
        # @example body is exempt, but a tag after it returns to checked prose.
        content = (
            "/**\n * @example\n * foo()" + SEMI
            + "\n * @remarks first" + SEMI + " second\n */"
        )
        result = run_hook(hook_input("a.js", content))
        self.assertTrue(denied(result))

    def test_go_prose_outside_indented_block_still_checked(self):
        content = "// Note; here.\n//\tcode := 1" + SEMI + "\nfunc Run() {}"
        result = run_hook(hook_input("a.go", content))
        self.assertTrue(denied(result))

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


class TestHandoffExemption(unittest.TestCase):
    def test_handoff_artifact_allows_banned_characters(self):
        content = "Captured diff with " + EM_DASH + " and a; semicolon"
        result = run_hook(hook_input("docs/handoffs/sync-cache.md", content))
        self.assertEqual(result.returncode, 0)
        self.assertFalse(denied(result))

    def test_handoff_exemption_holds_for_absolute_path(self):
        content = "x = 1 " + EM_DASH + " note"
        result = run_hook(hook_input("/repo/docs/handoffs/x.md", content))
        self.assertFalse(denied(result))

    def test_exemption_does_not_leak_to_sibling_paths(self):
        content = "authored prose with " + EM_DASH + " dash"
        result = run_hook(hook_input("docs/plans/x.md", content))
        self.assertTrue(denied(result))

    def test_review_packet_is_also_exempt(self):
        content = "Evidence diff with " + EM_DASH + " and a; semicolon"
        result = run_hook(hook_input("docs/reviews/pr-42.md", content))
        self.assertEqual(result.returncode, 0)
        self.assertFalse(denied(result))


if __name__ == "__main__":
    unittest.main()
