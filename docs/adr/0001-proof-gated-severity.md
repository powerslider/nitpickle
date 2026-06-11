# ADR-0001: Proof-gated severity

## Status

Accepted

## Context

The market is saturated with AI review tools that emit plausible-sounding
findings the reader cannot trust. Senior engineers distrust LLM output precisely
because it asserts without evidence. The original NitPickle ideation listed "ask
for proof" as one feature button among many. Matt Pocock's `diagnose` skill
makes a stronger claim from the debugging side: a fast, deterministic pass/fail
feedback loop *is* the skill - everything else is mechanical.

These converge on one decision.

## Decision

A Finding's severity is gated on Proof. Specifically:

- `severity: blocking` requires `proof in {test, repro}` - a runnable artifact
  that demonstrates the problem.
- A Finding the agent cannot prove is **downgraded** (to `nit` or `question`),
  never hidden.
- The agent must be honest about non-proof. A labeled low-confidence nit is
  useful. A vibe dressed as "blocking" is the thing we exist to eliminate.

Proof is produced by building a feedback loop, using the strategy palette from
`diagnose` (failing test, repro, snapshot, replay, harness, fuzz, bisect,
differential).

## Consequences

- Reviews are slower than emit-and-pray tools. This is the cost of trust and the
  moat - it is hard to copy because it is genuinely more work.
- When no correct seam exists to write a proof test, that absence is itself a
  Finding (an architectural one), per the `tdd` skill's rule. This is the one
  scoped exception to the no-proof cap: a missing-seam Finding may carry
  `important` with proof `none`, because the demonstrated absence of a proof
  seam is the evidence. No other category may exceed `nit` unproven.
- Severity counts become meaningful: "1 proven blocking" is a fact, not an
  opinion, so it can gate a pre-flight verdict.

## Alternatives considered

- **Confidence scores without proof** (what incumbents do). Rejected: a
  confidence number the model assigns to itself is still a vibe.
- **Proof as an optional on-demand button.** Rejected: optional proof means the
  default output is untrustworthy, which defeats the positioning.
