# ADR-0004: A default-on guardrail blocks the agent's write commands

## Status

Accepted

## Context

NitPickle's posture is that the human decides what lands. ADR-0001 gates severity
on proof so the agent cannot assert without evidence, and ADR-0003 keeps even a
proven conflict resolution human-gated. Every skill states it never commits,
pushes, or runs `--continue`. But that is prose. Nothing stops the model from
running `git push` anyway, by mistake or by following a stray instruction in
untrusted content. The strongest part of the thesis was unenforced.

A plugin cannot ship permission deny rules (a plugin's settings.json honors only
`agent` and `subagentStatusLine`), so enforcement has to be a PreToolUse hook.
That hook fires globally for every Bash call in the session, including the
plugin's own skills and their subagents.

## Decision

NitPickle ships a default-on PreToolUse hook that blocks the agent from running
the write commands that make changes land or go outward: git commit, push, the
per-operation `--continue`, reset `--hard`, and the destructive gh verbs (pr
merge, create, close, edit, comment, ready, reopen, lock, review `--approve`,
repo and release writes, issue writes). The human runs these.

- The `if: "Bash(...)"` matcher fires the hook on a candidate subcommand, the
  script makes the allow or deny call with an exact argv-token check.
- The allow set is everything else, including the skills' own worktree, checkout,
  apply, fetch, and reads, and review-pr's approved posting (`gh api` comments
  and `gh pr review --comment/--request-changes`), which deny only on `--approve`.
- A single env var, `NITPICKLE_ALLOW_WRITES`, both overrides the guardrail for a
  deliberate use and disables it when set in the environment.

## Consequences

- The controlled-delegation posture is enforced, not merely asserted. An
  accidental or injected `git push` is denied with a reason.
- The agent's git behavior changes in every repo where the plugin is enabled,
  not only during skill runs. Users who want the agent to commit in normal work
  set the env var. This friction is the accepted cost of a safe default.
- The guardrail is a safety net, not an airtight boundary. The harness does not
  decompose `git -C <dir>` or `bash -c "..."`, so a deliberate wrapper evades.
  The honest framing is documented, like the house-style hook.
- The block list is the maintained surface. A new write verb needs a one-line
  hooks.json entry and a rule branch, or it slips through.
- The override is not a self-grant vector. The hook reads
  `NITPICKLE_ALLOW_WRITES` from its own process environment, inherited from the
  Claude Code process the human launched. A child Bash process cannot mutate the
  parent's environment, and the harness strips a leading inline assignment for
  matching, so an injected `NITPICKLE_ALLOW_WRITES=1 git push` still fires the
  hook and is denied. Only the human's shell can set the override.

## Alternatives considered

- **Native permission deny rules.** Rejected: a plugin cannot ship them.
- **Opt-in rather than default-on.** Rejected: the posture is the point of the
  toolkit, so it is the default, with a documented disable for those who want
  the agent to write.
- **A permission ask prompt instead of a hard deny.** Rejected for the default:
  the goal is the human runs the command, not approves the agent running it. The
  env var is the deliberate-agent-use path.
- **A broad `Bash(git *)` block.** Rejected: it would block the skills' own
  worktree, checkout, and read commands.
