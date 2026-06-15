# ADR-0003: Proven conflict resolutions stay human-gated

## Status

Accepted

## Context

ADR-0001 makes proof the arbiter: a Finding's severity is gated on a runnable
artifact, and an unproven claim is downgraded. Across the toolkit, a green proof
is what licenses confidence. The `resolve-conflicts` skill builds a proof per
proposed resolution (it applies, compiles, and the policy commands pass), so the
natural extension of ADR-0001 would be to auto-apply any resolution whose proof
is green.

That extension is unsafe for semantic conflicts. A conflict arises because both
sides changed overlapping logic. A resolution can compile and pass the existing
tests while silently dropping one side's intent, because the tests that would
have caught the loss may not exist, and the surviving behavior still passes. The
research behind the plan is blunt about this: the dominant failure of assisted
resolution is compiles-and-passes-but-intent-lost. Here a green proof is
necessary but not sufficient.

This is the one place the proof engine's authority must be bounded.

## Decision

A semantic conflict resolution stays human-gated even when its proof is green.
`resolve-conflicts` proposes, proves, and applies on per-hunk approval, and never
treats a passing proof as license to apply without the human.

The only resolutions applied without approval are the provably-trivial ones: a
side-choice where the other side is a no-op, with all three index stages present,
verified by a deterministic index check rather than a build-and-test proof. Those
are lossless by construction, not by passing tests. Everything that requires
synthesizing new content stays gated.

## Consequences

- The proof engine grades and informs a semantic resolution, but does not get to
  apply it. This is a deliberate limit on ADR-0001's proof-gates-severity model,
  scoped to conflict resolution, recorded so a future change does not auto-apply
  proven resolutions and reintroduce silent intent loss.
- Conflict resolution is slower than a green-means-go tool would be. That is the
  cost of not dropping a side's intent.
- The honest caveat lives in the skill: a green build is evidence, not proof of
  intent preservation. Reviewers and the resuming human keep authority.

## Alternatives considered

- **Auto-apply any resolution with a green proof**, consistent with ADR-0001.
  Rejected: a green proof does not prove intent preservation for a semantic
  conflict, so this trades silent data loss for throughput.
- **Gate everything, including the trivial side-choices.** Rejected: the trivial
  set is provably lossless by a deterministic index check, not by a build, so
  human approval there adds friction without adding safety.
