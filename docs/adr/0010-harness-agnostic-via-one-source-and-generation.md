# ADR-0010: harness-agnostic via one canonical source and per-harness generation

## Status

Accepted

## Context

NitPickle was a Claude Code plugin. The skills are portable markdown, but the
packaging, the hook wiring, and the `/nitpickle:` invocation namespace were
Claude-specific. Codex has since converged on the same model (SKILL.md skills
discovered from `.agents/skills`, PreToolUse command hooks that deny via
`permissionDecision`), so a second harness is reachable without forking content.
The forces: keep one source of truth, do not weaken the proof discipline or the
Write guardrail (ADR-0004), and add no per-harness config the agent must manage.

Two harness differences are load-bearing. Codex fires `^Bash$` on every Bash call
with no per-family `if` matcher and no chain decomposition, unlike Claude Code,
which pre-selects the command family. Codex edits go through `apply_patch`, not
Write or Edit.

## Decision

Author once under `skills/` and `hooks/`, and generate the Codex layout on
demand. `tools/generate.py` renders `.agents/skills/` and a `.codex/hooks.json`,
rewriting `/nitpickle:<name>` cross-references to Codex `$name` invocation syntax.
Generated install artifacts are never committed, they generate to a temp tree for
tests and to `~/.agents/skills` at install. The one committed exception is the
Codex marketplace distribution bundle under `.agents/plugins/`, which a remote
`codex plugin add` can only read from a git commit, so it is committed and held to
the canonical source by a regenerate-and-diff drift check (see the marketplace
distribution plan). The validator gains check 3b (every Codex `$name` resolves, no
namespace token survives) and check 10 (no Claude-only token in a canonical skill
body).

The two Python hooks stay the single guardrail logic. On Codex the write
guardrail self-dispatches: it splits the command on shell operators and anchors
family detection to each segment's leading token. The house-style hook parses a
Codex apply_patch body per file in addition to the Write and Edit shapes.

## Consequences

- One source, two installs. Codex and Claude Code share every skill and hook.
- The Write guardrail is best-effort on Codex. Without the harness pre-filter and
  chain decomposition, exotic quoting or command substitution can still hide a
  write. The segment-split restores the common cases (a chained
  `git add && git commit` denies, a `grep "git push"` passes), but the airtight
  boundary on Codex is the harness approval policy, recommended as defense in
  depth, not depended on. This is consistent with ADR-0004 calling the guardrail
  a safety net, not an airtight boundary.
- House-style enforcement is materially weaker on a Codex apply_patch edit. An
  added-line fragment rarely has balanced code fences, so the prose check fails
  open more often than for a Write or Edit. The character checks still hold.
- The apply_patch `tool_input` shape is captured as a fixture under
  `tests/fixtures/codex/`, confirmed by a manual smoke, not by CI.
- The Codex marketplace distribution bundle (`.agents/plugins/`) is the sole
  committed generated artifact, guarded by a regenerate-and-diff drift check plus
  check 3b for rewrite correctness. Install artifacts (`~/.agents/skills`,
  `~/.codex/hooks.json`) stay generate-on-demand. The write guardrail is never part
  of the bundle, Codex does not run plugin-bundled hooks, so it installs separately
  via `generate.py --install-hooks` and is trusted through `/hooks`.

## Alternatives considered

- **Vendor the generated Codex install artifacts.** Rejected. Committed generated
  files drift, bloat diffs, and need a regenerate-and-recommit on every skill edit.
  A diff-against-committed check proves equality, not correctness. This rejection
  is scoped to the install artifacts. The marketplace distribution bundle is the
  bounded exception, it must be committed for a remote `codex plugin add` to read
  it, its drift is caught by the regenerate-and-diff check, and check 3b proves
  rewrite correctness independently, answering the equality-not-correctness concern
  for that case. A dedicated dist branch or sibling repo was considered instead and
  rejected, committed default-branch registries are the ecosystem norm (wshobson).
- **Shared in-place layout via symlinks.** Rejected. The harnesses scan different
  paths and hook configs, and the cross-reference, tool-name, and wiring
  differences need transformation regardless, which symlinks do not provide.
- **Parallel maintained copies per harness.** Rejected. Double maintenance and
  guaranteed drift.
- **Lean on Codex approval policy instead of the script guardrail.** Rejected as
  the default. It depends on Codex config the user must set and diverges from the
  Claude guardrail. Kept as a recommended defense-in-depth note.
