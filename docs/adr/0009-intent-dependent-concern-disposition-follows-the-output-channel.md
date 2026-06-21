# ADR-0009: an intent-dependent concern's disposition follows the output channel

## Status

Accepted

## Context

ADR-0008 gave `audit` a correctness bounding. Assert only a Proof-complete defect (wrong
provably from the code alone, no assumption about intended behavior), and route an
intent-dependent concern (whose status as a bug needs the intended behavior) to a
characterization task. It explicitly rejected emitting intent-dependent concerns as bare
questions, because `audit`'s output is a one-shot roadmap where a question dead-ends, an
artifact-free suspicion handed to no one.

`review-pr` faces the same correctness situation on someone else's PR, where the intended
behavior is often not settled by the stated intent. Its output is different. A review
posts comments on the PR, and a clarifying comment ("the code does X, is that intended?")
is a normal review artifact the author resolves in the PR thread. So the disposition that
is a vibe-finding in a roadmap is a legitimate, resolvable comment in a review.

## Decision

The Proof-complete bounding is a cross-skill principle. Wherever the agent judges code
whose intent it does not own, it asserts only Proof-complete defects and routes
intent-dependent concerns by **output channel**.

- A **dialogue channel** (a PR review) admits a clarifying question, raised with
  `severity: question`, that the author resolves in the thread. `review-pr` uses this.
- A **one-shot artifact** (audit's roadmap) has no resolution slot for a bare question, so
  the concern is pinned with a characterization test for the human to ratify. `audit` uses
  this.

This refines proof-gated severity in one way worth stating. A test that proves the code's
behavior is not a proof of a defect when calling that behavior a defect needs an intended
behavior the agent assumed. Such a test does not make an intent-dependent concern blocking.

A tie-break protects against under-flagging. A concern wrong regardless of intent (a crash,
an out-of-bounds, a race, an always-true condition) stays on the Proof-complete track and
is proven. Only a concern whose sole basis is an assumption about the intended output
becomes a question. The test is whether refuting the concern requires knowing the intended
output.

## Consequences

- `review-pr` and `audit` handle the same correctness situation oppositely, by design, and
  this records why, so neither is reconciled to the other in error.
- `review-pr` produces fewer wrong request-changes, an intent-dependent concern can no
  longer force a change demand. The cost is a false negative if the agent mis-classifies a
  real bug as an assumed-output judgment, which the tie-break narrows and the human catches
  at triage.
- The disposition is consistent with proof-gated severity. An intent-dependent concern with
  no proof of a defect is a question, which the Finding schema already expresses. No
  canonical schema change.

## Alternatives considered

- **Route `review-pr`'s intent-dependent concerns to characterization like `audit`.**
  Rejected. A PR review is a dialogue, so a clarifying comment is cheaper and more accurate
  than the reviewer pinning behavior the author can confirm.
- **Assert intent-dependent concerns as blocking and let the human downgrade.** Rejected.
  That is the wrong request-changes this decision exists to prevent, and it puts the oracle
  judgment on the reviewer rather than the author.
- **Record nothing and treat it as applying ADR-0008.** Rejected. The disposition is the
  alternative ADR-0008 rejected, so without recording the channel distinction a future
  reader reads `review-pr` as contradicting it.
