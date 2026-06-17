# ADR-0005: Polish proves behavior preservation, not improvement

## Status

Accepted

## Context

NitPickle is adding a polish skill, a convention-aware pass that refactors code
toward the repo's idioms and taste. It needs a proof model, and the existing one
does not fit cleanly.

ADR-0001 gates severity on Proof and caps judgment or taste claims at nit or
question, because no mechanical Feedback loop can demonstrate them. "This refactor
is better" is exactly such a taste claim. Polish cannot prove it, so under
ADR-0001 alone every polish output would be a nit, which makes the skill inert.

ADR-0003 is the closer precedent. A conflict resolution can compile and pass
tests while dropping a side's intent, so a green Proof is necessary but not
sufficient and the human keeps authority. A refactor has the same shape. It can
preserve observable behavior, which is provable, without being an improvement,
which is not.

## Decision

A polish Refinement is gated on a behavior-preservation Proof, not on a proof of
improvement, and it stays human-gated.

- The Proof is a differential. Observable behavior is unchanged across the
  transform. It demonstrates the change is safe, never that it is better. Whether
  a safe change is an improvement is a taste call the human owns.
- The Proof is tiered, sharpest first. The Policy commands when they already cover
  the touched code. Otherwise a throwaway characterization test, synthesized in an
  isolated worktree to pin current behavior and run before and after the transform.
  That test proves this transform only, it does not hunt for defects, which stays
  Pre-flight's job. When no characterization Seam is possible, the Refinement
  cannot be proven safe, so it is downgraded to a suggestion and never applied
  silently, and the missing Seam is flagged.
- A Refinement is applied to the working tree only on per-change human approval,
  never in bulk, and polish never commits or pushes (ADR-0004).

## Consequences

- Polish is useful on untested code, because the characterization tier can build
  the missing signal rather than refuse. The cost is the throwaway test, an
  artifact that is shown, never committed.
- The Proof engine grades a Refinement as safe and informs the human, but does not
  get to apply it. This is the bound ADR-0003 placed on conflict resolution, now
  stated for quality transforms, so a future change does not auto-apply
  preservation-proven Refinements and reintroduce silent intent loss.
- Polish stays a quality skill. It does not assert correctness Findings, and a
  preservation Proof is never read as a betterment Proof.
- The contract is human-ratified by construction. This repo's own CI proves only
  the consistency and house style of the skill files. The runtime preservation
  Proof exists only when polish runs against a user's code.

## Alternatives considered

- **Auto-apply any Refinement with a green preservation Proof**, by analogy to
  ADR-0001. Rejected by ADR-0003's logic. Green proves safe, not better, and
  better is the human's call.
- **Cap every polish output at nit under ADR-0001.** Rejected. It is technically
  consistent but makes the skill inert, since a safe refactor would never rise
  above a nit even when its behavior preservation is proven.
- **Fold the proof reframe into ADR-0001.** Rejected. Accepted ADRs are not
  re-litigated or edited, and the reframe is a distinct decision scoped to polish.
