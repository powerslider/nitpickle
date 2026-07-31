# Handoff format

The reference the `handoff` skill writes against and `resume` reads against. A
Handoff is a standalone, ephemeral artifact at `docs/handoffs/<slug>.md` that
captures the live progress of an in-flight task so a different session or agent
can finish it. Getting it to that session is the author's responsibility.

A Handoff is transient working state, not a convention file. House style does
not apply to it (the hook and validator exempt `docs/handoffs/`), so an embedded
diff of arbitrary code is allowed.

## Slug

Reuse the slug of a matching `docs/plans/<slug>.md` when one exists, so the plan
and its handoff are paired. Otherwise derive a short kebab-case slug from the
task.

## Structure

A `# Handoff - <task title>` heading, three header lines, then the sections
below. Headers:

- `Written:` an ISO 8601 timestamp.
- `Branch:` the branch the work lives on.
- `Plan:` a link to `docs/plans/<slug>.md`, omitted when there is no plan.

Sections, in order:

- **Task** - one or two sentences in glossary terms. What is being built and why.
- **Done** - what is finished, each with the commit that landed it.
- **In flight** - what is partway done, and where it stands.
- **Blocked** - anything waiting on a decision or an external answer, with who
  or what resolves it. Omit the section when nothing is blocked.
- **Next step** - the single concrete next action, specific enough to start
  without re-deriving it.
- **Working state** - a `Branch:` line, a `Head:` line (short hash plus
  subject), then uncommitted work captured as a fenced code block tagged `diff`.
  Build it with `git add -N` then `git diff HEAD`, so untracked files are
  included. Write "none" in the block when the tree is clean.
- **Gotchas and dead-ends** - approaches already ruled out and why, so the next
  agent does not re-explore them, plus facts non-obvious from the code.

## Field notes

- **Link the plan, do not copy it.** The plan holds the phases and the contract.
  The Handoff holds only where you are against it. Copying phase text invites
  drift.
- **Git snapshot is for divergence detection, not trust.** `resume` re-reads the
  real branch and head and compares. The recorded values are a checkpoint, not a
  source of truth.
- **The embedded diff goes stale.** It is a best-effort capture of in-flight
  work. `resume` attempts to apply it and stops to ask when it does not apply
  cleanly.
- **Claims are unverified.** A line like "tests pass" is what was true when
  written. `resume` re-runs the policy commands rather than trusting it.

## Lifecycle

A Handoff is short-lived. Once the task is finalized it has served its purpose,
and `resume` offers to delete it.
