# ADR-0002: Handoff artifacts are standalone and ephemeral

## Status

Accepted

## Context

The `handoff` and `resume` skills encapsulate the live progress of an in-flight
task so a different session or agent can finish it. That progress has to live
somewhere, and two placement questions have non-obvious answers.

First, standalone or folded into the plan. A `docs/plans/<slug>.md` already
records the contract for a planned change (phases, intent). A handoff records
where you currently are against that contract. Folding the second into the first
avoids a second file that can drift, but ties a handoff to having a plan at all.

Second, persistence. A handoff is a snapshot of a moment, useful until the work
is finished. The toolkit could insist it be committed (so it travels with the
repo) or gitignored (treated like the local validation log and todo). Either
choice prescribes how the author moves the snapshot to the other session.

## Decision

A handoff artifact is a standalone, ephemeral file at `docs/handoffs/<slug>.md`.

- **Standalone**, not a section of the plan doc. It links the plan and records
  only live state (done, in flight, blocked, next step, ruled-out dead-ends, and
  a git snapshot). It never copies the plan's phases. A handoff exists even for
  ad-hoc work with no plan.
- **Ephemeral**, and the toolkit takes no position on persistence. Getting the
  artifact to the other session or agent is the author's responsibility. They
  may commit it, push it, copy it, or paste it, whatever fits. The skills neither
  commit it nor require it to be committed, and `docs/handoffs/` is not
  gitignored, so the choice stays with the author each time.

A handoff is not a convention file. It is transient working state, outside the
convention set (glossary, decisions, policy, taste), so `review-pr` does not
treat a `docs/handoffs/` diff as a convention-file finding when one does appear
in a PR.

## Consequences

- A handoff works for any task, planned or not, without forcing a plan to exist.
- The author owns transfer. The toolkit does not assume the file is shared by
  any particular mechanism, so it makes no cross-machine promises it cannot keep.
- Progress state can drift from the plan doc, since the two are separate files.
  Mitigated by linking rather than copying, and by `resume` reconciling the
  artifact against the current plan and the real git and test state on pickup.
- Because the artifact embeds a diff of code we do not author, house style does
  not apply to it. The hook and the validator exempt `docs/handoffs/` paths.

## Alternatives considered

- **Fold the handoff into the plan doc** as a section. Rejected in favor of a
  standalone artifact, so a handoff exists even for ad-hoc work with no plan and
  the two concerns stay separable.
- **Prescribe committing, or prescribe gitignoring.** Rejected. A handoff is
  ephemeral and the right way to move it depends on the situation, so the toolkit
  stays neutral and leaves transfer to the author.
