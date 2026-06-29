# Codex schema fixtures

The assumed Codex hook contract that the harness-neutral hooks are built and
tested against. These shapes are the spec. The contract tests in `hooks/` assert
the scripts behave correctly against them, and a real-`codex` manual smoke
confirms the shapes are faithful (HITL acceptance, recorded in the plan).

Source: https://developers.openai.com/codex/hooks and
https://developers.openai.com/codex/config-reference. Pending the smoke, treat
the apply_patch shape as assumed, not confirmed.

## PreToolUse stdin (command hook)

Codex pipes JSON on stdin. The fields the hooks read:

```json
{
  "turn_id": "t-1",
  "tool_name": "Bash",
  "tool_use_id": "tu-1",
  "tool_input": { "command": "git push origin main" }
}
```

For an edit, Codex uses the `apply_patch` tool. The assumed shape carries the
patch body in `tool_input.command`:

```json
{
  "tool_name": "apply_patch",
  "tool_input": {
    "command": "*** Begin Patch\n*** Add File: notes.md\n+content\n*** End Patch"
  }
}
```

## Deny output

The scripts emit the decision Codex accepts, identical to Claude Code:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}
```

Codex also accepts exit code 2 with a stderr reason, and the legacy
`{"decision": "block", "reason": "..."}`. The scripts use the `permissionDecision`
form.

## Matcher difference

Claude Code fires per family via `if: "Bash(git commit:*)"` and passes the family
as an argument. Codex fires `^Bash$` on every Bash call with no family. The
guardrail handles both: a named family is the Claude path, no family is the Codex
self-dispatch path that splits the command and judges each segment.
