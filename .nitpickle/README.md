# .nitpickle/ - the convention layer

Per-repo configuration that every NitPickle skill reads. Versioned and
human-editable. Diff and commit these like code. Nothing here is invisible.

## Files in here

| File | Holds | Written by | Read by |
| --- | --- | --- | --- |
| `policy.yaml` | commands to run, judgment rules, generated files, diff budget, review defaults, proof gating | you | every skill |
| `preferences.md` | your personal engineering taste and house writing style | you (mined from past reviews in Phase 1) | every skill |
| `validation-log.md` | did pre-flight change your behavior (the Phase 0 metric) | preflight | you |
| `todo.md` | findings you deferred during a review run | preflight, review-pr | you |

`validation-log.md` and `todo.md` are per-developer working state: bootstrap
creates them and adds both to `.gitignore`. The rest is shared and tracked.

## Two more conventions live at the repo root

They are standard conventions, not NitPickle-specific, so they sit at the root
rather than in here.

| Path | Holds | Convention |
| --- | --- | --- |
| `CONTEXT.md` | domain glossary, terms only, no implementation | Matt Pocock |
| `docs/adr/` | recorded decisions, one per file (template: `0000-template.md`) | ADR |

## Four separate things, on purpose

- **policy.yaml** is per-repo rules.
- **preferences.md** is personal taste.
- **CONTEXT.md** is shared language.
- **docs/adr/** is decisions.

Do not merge them. A review speaks the glossary, respects the ADRs, applies your
taste, and runs the policy commands and rules.

## Global defaults and resolution

A repo does not need its own `.nitpickle/`. When a file is absent locally, skills
fall back to the global default at `~/.claude/nitpickle/`.

- **policy.yaml** and **preferences.md**: effective config = global overlaid by
  local. Local overrides the global per top-level key, and `rules` is the union
  of both. No local `.nitpickle/` at all means the global defaults apply
  unchanged.
- **CONTEXT.md**, **docs/adr/**, **validation-log.md**, **todo.md**: always
  per-repo, no global version.

The global defaults are language-agnostic (cross-project taste and universal
rules). Keep toolchain commands and language-specific rules in the local file.
The shipped copy of the defaults lives in `defaults/nitpickle/` (install it with
the commands in `defaults/README.md`).

## The one rule that ties it together

Severity is set by Proof, not by any policy rule (see ADR-0001). Policy names
what to look for. Proof decides whether a violation is blocking. A rule the agent
cannot prove is downgraded, never hidden.

## Editing tips

- `policy.yaml`: keep deterministic checks in `commands`, judgment in `rules`. If
  a rule could be a linter analyzer, move it to `commands.lint`.
- `preferences.md`: short bullets. Delete anything that no longer reflects how you
  work.
- New decision worth recording? Copy `docs/adr/0000-template.md` to the next
  number. Offer an ADR only when the decision is hard to reverse, surprising
  without context, and the result of a real trade-off.
