#!/usr/bin/env python3
"""NitPickle house-style guard.

Blocks Write/Edit/MultiEdit before they land when the incoming text contains an
em or en dash (anywhere) or a semicolon (in markdown prose, code blocks exempt).
Keeps generated comments, plans, specs, and reviews free of the two characters
the house style forbids. See .nitpickle/preferences.md.
"""
import sys
import json
import re


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


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    text = incoming_text(tool_input)
    if not text:
        sys.exit(0)

    violations = []
    if "—" in text or "–" in text:
        violations.append("em or en dash")

    if path.endswith(".md"):
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        prose = re.sub(r"`[^`]*`", "", prose)
        if ";" in prose:
            violations.append("semicolon in markdown prose")

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
