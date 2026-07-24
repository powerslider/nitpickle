#!/usr/bin/env python3
"""NitPickle write-command guardrail.

A PreToolUse hook that blocks the agent from running the write commands that make
changes land or go outward, so only the human runs them. See ADR-0004.

The harness fires this hook only on a candidate command family (the `if:
"Bash(...)"` condition in hooks.json decomposes chains and strips wrappers). The
family is passed as the first argument. This script makes the allow or deny call
with an exact argv-token and subcommand check, robust to flag order, rather than
parsing the shell itself.

Escape hatch: NITPICKLE_ALLOW_WRITES in the environment allows everything. The
hook reads its own process environment, which a child Bash process cannot mutate,
so the agent cannot self-grant by inlining the variable. Only the human's shell
sets it. See ADR-0004.

Fail open: malformed input or an unknown family exits 0 with a stderr diagnostic.
"""
import sys
import json
import os
import re
import shlex

# gh subcommands that write or go outward, blocked. Read siblings (view, list,
# diff, checks, clone, download, status) are absent, so they pass.
GH_PR_WRITES = {
    "merge", "create", "close", "edit", "comment", "ready", "reopen", "lock",
    "delete",
}
GH_REPO_WRITES = {"create", "delete", "edit", "rename", "archive", "fork", "sync"}
GH_RELEASE_WRITES = {"create", "delete", "edit", "upload"}
GH_ISSUE_WRITES = {
    "create", "edit", "close", "comment", "delete", "reopen", "lock",
    "transfer", "pin", "unpin",
}
# gh resource families that deny on a write subcommand, keyed by family to its
# (subcommand group, write set). gh-pr is handled separately for its review
# --approve special case.
GH_RESOURCE_FAMILIES = {
    "gh-repo": ("repo", GH_REPO_WRITES),
    "gh-release": ("release", GH_RELEASE_WRITES),
    "gh-issue": ("issue", GH_ISSUE_WRITES),
}
# git merge/rebase/cherry-pick land or rewrite unless they are the safe escapes.
GIT_SEQUENCE_SAFE = {"--abort", "--quit", "--skip", "--edit-todo", "--show-current-patch"}
# Each git family maps to the exact subcommand token it guards. The harness `if`
# matcher fires on a string prefix, so `git merge:*` also matches read-only
# siblings like `git merge-base`; requiring the exact token lets those pass.
GIT_FAMILY_SUBCOMMAND = {
    "git-commit": "commit",
    "git-push": "push",
    "git-reset": "reset",
    "git-merge": "merge",
    "git-rebase": "rebase",
    "git-cherry-pick": "cherry-pick",
}
# git global options that consume the following token as their value, so the
# subcommand scan skips past them (e.g. `git -C path commit`).
GIT_GLOBAL_VALUE_OPTS = {"-C", "-c"}
# Families the hook knows how to judge. An arg outside this set means the
# hooks.json entry and this script disagree, so it fails open with a diagnostic.
KNOWN_FAMILIES = set(GIT_FAMILY_SUBCOMMAND) | {"gh-pr"} | set(GH_RESOURCE_FAMILIES)


def tokens(command):
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def git_subcommand(toks):
    """The git subcommand token, skipping global options. None if absent."""
    try:
        i = toks.index("git")
    except ValueError:
        return None
    j = i + 1
    while j < len(toks):
        t = toks[j]
        if t in GIT_GLOBAL_VALUE_OPTS:
            j += 2
            continue
        if t.startswith("-"):
            j += 1
            continue
        return t
    return None


# gh global flags that consume the following token as their value, so the
# subgroup scan skips past them (e.g. `gh -R owner/repo pr create`).
GH_GLOBAL_VALUE_OPTS = {"-R", "--repo"}


def gh_group_and_rest(toks):
    """The gh subgroup token (pr/repo/release/issue) and the tokens after it,
    skipping global flags and their values. (None, []) if absent."""
    try:
        i = toks.index("gh")
    except ValueError:
        return None, []
    j = i + 1
    while j < len(toks):
        t = toks[j]
        if t in GH_GLOBAL_VALUE_OPTS:
            j += 2
            continue
        if t.startswith("-"):
            j += 1
            continue
        return t, toks[j + 1:]
    return None, []


def gh_subcommand(toks, group):
    """The subcommand token after `gh <group>`, skipping flags. None if absent."""
    found, rest = gh_group_and_rest(toks)
    if found != group:
        return None
    for t in rest:
        if not t.startswith("-"):
            return t
    return None


# Shell tokens that separate or terminate one command from the next. A
# punctuation-aware lexer detects these as their own tokens, so an operator
# inside quotes stays part of its argument. Codex fires the hook on the whole
# Bash call with no per-family decomposition, so self-dispatch finds the write
# itself. Best effort: command substitution can still hide a write. See ADR-0004.
SEGMENT_TOKENS = {"&&", "||", ";", "|", "&", "(", ")", "<", ">"}
# Wrappers that precede the real command and should be skipped to find it.
COMMAND_WRAPPERS = {
    "sudo", "command", "nohup", "time", "env", "nice", "stdbuf", "xargs",
}
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# git subcommand to the family that guards it.
GIT_SUBCOMMAND_FAMILY = {sub: fam for fam, sub in GIT_FAMILY_SUBCOMMAND.items()}
GH_GROUP_FAMILY = {
    "pr": "gh-pr", "repo": "gh-repo", "release": "gh-release", "issue": "gh-issue",
}


def operator_tokens(text):
    """Tokens for one command line with shell operators kept as their own tokens,
    quote-aware. Falls back to a plain split on a lexer error."""
    lex = shlex.shlex(text, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    try:
        return list(lex)
    except ValueError:
        return text.split()


def command_segments(command):
    """Yield each command segment as a token list. Lines split first (a newline is
    a separator the lexer treats as whitespace), then operators within a line, so
    a `;` or `&` inside quotes never separates. A backslash-newline is a shell line
    continuation, joined back so a write split across it is still one command."""
    command = command.replace("\\\n", "")
    for line in command.split("\n"):
        segment = []
        for tok in operator_tokens(line):
            if tok in SEGMENT_TOKENS:
                if segment:
                    yield segment
                segment = []
            else:
                segment.append(tok)
        if segment:
            yield segment


def leading_token(toks):
    """The command's real leading token, past env-assignments and wrappers."""
    for t in toks:
        if ENV_ASSIGN.match(t) or t in COMMAND_WRAPPERS:
            continue
        return t
    return None


def self_dispatch_deny(command):
    """Deny reason for any write segment in a full command, anchoring family
    detection to each segment's leading token. The path for a harness (Codex)
    that fires on the whole Bash call without the per-family `if` matcher."""
    for seg in command_segments(command):
        lead = leading_token(seg)
        if lead == "git":
            family = GIT_SUBCOMMAND_FAMILY.get(git_subcommand(seg))
        elif lead == "gh":
            group, _ = gh_group_and_rest(seg)
            family = GH_GROUP_FAMILY.get(group)
        else:
            continue
        if family:
            reason = deny_reason(family, seg)
            if reason:
                return reason
    return None


def deny_reason(family, toks):
    """The deny reason for a write command in a known family, or None to allow.
    `toks` is the command's shell tokens."""
    if family in GIT_FAMILY_SUBCOMMAND:
        # The harness matcher fires on a string prefix, so confirm the exact
        # subcommand: a read-only sibling (e.g. git merge-base) shares it but
        # must pass.
        if git_subcommand(toks) != GIT_FAMILY_SUBCOMMAND[family]:
            return None
        if family in ("git-commit", "git-push"):
            return family.replace("-", " ")
        if family == "git-reset":
            return "git reset --hard" if "--hard" in toks else None
        # merge / rebase / cherry-pick: deny unless a safe escape is present.
        if GIT_SEQUENCE_SAFE & set(toks):
            return None
        return family.replace("-", " ")

    if family == "gh-pr":
        sub = gh_subcommand(toks, "pr")
        if sub in GH_PR_WRITES:
            return "gh pr %s" % sub
        if sub == "review" and "--approve" in toks:
            return "gh pr review --approve"
        return None

    group, writes = GH_RESOURCE_FAMILIES[family]
    sub = gh_subcommand(toks, group)
    return "gh %s %s" % (group, sub) if sub in writes else None


def main():
    if os.environ.get("NITPICKLE_ALLOW_WRITES"):
        sys.exit(0)

    # No family argument means self-dispatch: the harness (Codex) fired on the
    # whole Bash call and the script finds the write itself. A named family is
    # the Claude path, where the hooks.json `if` matcher pre-selected it.
    family = sys.argv[1] if len(sys.argv) > 1 else "auto"
    if family != "auto" and family not in KNOWN_FAMILIES:
        print(
            "nitpickle guardrail: unknown family %r, allowing" % family,
            file=sys.stderr,
        )
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except Exception as exc:
        print(
            "nitpickle guardrail: unreadable input (%s), allowing" % exc,
            file=sys.stderr,
        )
        sys.exit(0)

    command = (data.get("tool_input") or {}).get("command") or ""
    reason = self_dispatch_deny(command) if family == "auto" else deny_reason(family, tokens(command))

    if reason:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Blocked by NitPickle: `%s` is a write command only the "
                    "human runs after approval (ADR-0004). Run it yourself, or "
                    "set NITPICKLE_ALLOW_WRITES=1 to allow the agent." % reason
                ),
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
