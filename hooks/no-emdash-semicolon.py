#!/usr/bin/env python3
"""NitPickle house-style guard.

Blocks Write/Edit/MultiEdit before they land when the incoming text contains an
em or en dash (literal anywhere, HTML entity in markdown prose) or a semicolon
(in markdown prose, code blocks exempt). Keeps generated comments, plans, specs,
and reviews free of the characters the house style forbids. See
.nitpickle/preferences.md.

Fail-open rules: malformed hook input exits 0 with a stderr diagnostic, and an
unmatched code-fence count skips the prose checks for that text (fence parity is
undecidable for edit fragments, a false block is worse than a missed character).
"""
import sys
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


def strip_code(text):
    """Markdown prose with code removed. None when fence parity is unmatched."""
    if text.count("```") % 2 != 0:
        return None
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    prose = re.sub(r"`[^`]*`", "", prose)
    return prose


def find_violations(path, text):
    violations = []
    if EM_DASH in text or EN_DASH in text:
        violations.append("em or en dash")

    if path.endswith(".md"):
        prose = strip_code(text)
        if prose is not None:
            if ";" in prose:
                violations.append("semicolon in markdown prose")
            if any(entity in prose for entity in DASH_ENTITIES):
                violations.append("HTML-entity dash in markdown prose")
    return violations


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
