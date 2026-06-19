#!/usr/bin/env python3
"""NitPickle house-style guard.

Blocks Write/Edit/MultiEdit before they land when the incoming text contains an
em or en dash (literal anywhere, HTML entity in markdown prose) or a semicolon
(in markdown prose, or in code-comment prose; code examples are exempt in both:
fenced and inline code, godoc tab-indented blocks, and @example / @code blocks,
so a semicolon in a real example passes). Keeps generated comments, plans,
specs, and reviews free of the characters the house style forbids. See
.nitpickle/preferences.md.

Fail-open rules: malformed hook input exits 0 with a stderr diagnostic, and an
unmatched code-fence count skips the prose checks for that text (fence parity is
undecidable for edit fragments, a false block is worse than a missed character).
The semicolon-in-comment check covers a known extension set; unknown extensions
pass, since a false block is worse than a missed character.
"""
import sys
import os
import json
import re

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)
DASH_ENTITIES = (
    "&mdash;",
    "&ndash;",
    "&#8212;",
    "&#8211;",
    "&#x2014;",
    "&#x2013;",
)


def incoming_text(tool_input):
    parts = []
    if isinstance(tool_input.get("content"), str):
        parts.append(tool_input["content"])
    if isinstance(tool_input.get("new_string"), str):
        parts.append(tool_input["new_string"])
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            parts.append(edit["new_string"])
    return "\n".join(parts)


def strip_code_spans(text):
    """`text` with markdown-style code removed: fenced (```...```) then inline
    (`...`). None when fence parity is odd, since the code region is then
    undecidable and a false block is worse than a missed character. Used for
    both markdown prose and the prose of code comments."""
    if text.count("```") % 2 != 0:
        return None
    without_fences = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`]*`", "", without_fences)


# Comment syntax by file extension, the maintained surface for the
# semicolon-in-comment check. Each entry is (line-comment markers, has /* */
# block comments). Two families cover the set: C-like uses // and /* */; hash
# uses # with no block. `#` is listed only where it is a comment, so it is
# absent from C-like languages, where it is not.
_C_LIKE = (
    ".go", ".rs", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java",
    ".c", ".h", ".cpp", ".cc", ".hpp", ".cs", ".swift", ".kt", ".kts",
    ".scala", ".scss",
)
_HASH = (".py", ".rb", ".sh", ".bash", ".zsh", ".yaml", ".yml", ".toml")
COMMENT_SYNTAX = {ext: (("//",), True) for ext in _C_LIKE}
COMMENT_SYNTAX.update({ext: (("#",), False) for ext in _HASH})
COMMENT_SYNTAX[".css"] = ((), True)  # block comments only, no // line comments

# String-literal forms matched alongside comments in one left-to-right pass, so
# a comment marker inside a string is not a comment and a quote inside a comment
# does not open a string.
_STRING_ALTS = [
    r'"""[\s\S]*?"""', r"'''[\s\S]*?'''",
    r'"(?:\\.|[^"\\\n])*"', r"'(?:\\.|[^'\\\n])*'",
    r"`[^`]*`",
]
# Code-example regions inside a comment whose body is code, not prose: the godoc
# convention indents example lines with a tab, and the JSDoc / doxygen @example
# and @code tags open a block that runs to the next tag or the comment end.
DOC_EXAMPLE_TAG = re.compile(r"@(?:example|code)\b.*?(?=@\w|\Z)", re.S)
TAB_INDENTED_LINE = re.compile(r"(?m)^\t.*$")


def _comment_scanner(line_markers, has_block):
    """A regex matching string literals and comments in source order; comments
    capture in group 'c'. Strings are matched first so a marker inside one is
    consumed as a string rather than mistaken for a comment."""
    comment_alts = [r"/\*[\s\S]*?\*/"] if has_block else []
    comment_alts += [re.escape(m) + r"[^\n]*" for m in line_markers]
    alternatives = _STRING_ALTS + ["(?P<c>" + "|".join(comment_alts) + ")"]
    return re.compile("|".join(alternatives))


def _strip_comment_markers(comment):
    """A single matched comment reduced to its text. A block comment always ends
    in */ (the scanner requires it), so trim both fences and drop each line's
    leading * continuation; a line comment drops its leading marker run."""
    if comment.startswith("/*"):
        inner = comment[2:-2]
        return "\n".join(re.sub(r"^\s*\*", "", line) for line in inner.split("\n"))
    return re.sub(r"^\s*(?://+|#+)", "", comment)


def comment_prose(path, text):
    """The prose of a code file's comments, ready for the semicolon check:
    comment text with code examples removed. Returns "" for an unknown
    extension (nothing to check) and None when fence parity is undecidable
    (skip). Exempted as code, not prose: @example / @code blocks, godoc
    tab-indented lines, and (via strip_code_spans) fenced and inline code."""
    syntax = COMMENT_SYNTAX.get(os.path.splitext(path)[1].lower())
    if not syntax:
        return ""
    scanner = _comment_scanner(*syntax)
    comments = "\n".join(
        _strip_comment_markers(m.group("c"))
        for m in scanner.finditer(text)
        if m.group("c")
    )
    examples_removed = TAB_INDENTED_LINE.sub("", DOC_EXAMPLE_TAG.sub("", comments))
    return strip_code_spans(examples_removed)


def find_violations(path, text):
    violations = []
    if EM_DASH in text or EN_DASH in text:
        violations.append("em or en dash")

    # Semicolons are banned in prose only, so code (statement terminators,
    # examples) is stripped first. A None result means the code region was
    # undecidable, so the semicolon check is skipped rather than risk a false
    # block. Markdown also bans HTML-entity dashes in its prose.
    if path.endswith(".md"):
        prose = strip_code_spans(text)
        if prose is not None:
            if ";" in prose:
                violations.append("semicolon in markdown prose")
            if any(entity in prose for entity in DASH_ENTITIES):
                violations.append("HTML-entity dash in markdown prose")
    else:
        prose = comment_prose(path, text)
        if prose is not None and ";" in prose:
            violations.append("semicolon in code comment")
    return violations


# Transient artifacts that embed captured code (diffs, proof evidence) we do not
# author or maintain. House style does not apply. See .nitpickle/preferences.md.
EXEMPT_DIRS = ("docs/handoffs/", "docs/reviews/", "docs/audits/")


def is_exempt(path):
    norm = path.replace("\\", "/")
    return any(d in norm for d in EXEMPT_DIRS)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as exc:
        print(
            "nitpickle house-style hook: unreadable input (%s), allowing" % exc,
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    if is_exempt(path):
        sys.exit(0)
    text = incoming_text(tool_input)
    if not text:
        sys.exit(0)

    violations = find_violations(path, text)
    if violations:
        reason = (
            "Blocked by NitPickle house style: found "
            + " and ".join(violations)
            + ". Replace with periods, commas, or separate sentences. "
            + "No em dashes, no semicolons. See .nitpickle/preferences.md."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
