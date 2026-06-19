# ADR-0008: audit comprehends an existing feature before improving it, and routes the rest

## Status

Accepted

## Context

NitPickle is adding `audit`, a skill that holistically improves an existing, often
unfamiliar, complex feature. It needs a contract, and it sits close to several existing
skills. `preflight` reviews your own branch against its base. `review-pr` reviews
someone else's PR. `polish` and `test-spec` apply quality and test work. None
comprehends an existing feature whose intent the user does not own, and none produces a
whole-feature remediation roadmap that connects a duplicated block, a latent bug, and a
missing test seam to the one design decision behind all three.

`audit` also risks two failure modes. It could duplicate `preflight`'s per-finding
review, and on code of unknown intent it could emit unproven suspicions as findings, the
vibe-finding the toolkit exists to forbid.

## Decision

`audit` is `review-pr`'s inward sibling. It comprehends an existing feature,
reconstructing its design and ratifying intent with the human, then improves it, and
routes the apply work to the siblings.

- It reuses `preflight`'s isolated-worktree proof loop and `review-pr`'s adversarial
  refutation, pointed at a path rather than a diff, and dispatches the correctness work
  to a subagent. The comprehension and the whole-feature synthesis are its own, the
  novelty no sibling has.
- Correctness is bounded into two honest classes. A **Proof-complete defect**, wrong
  provably from the code alone with no assumption about intended behavior, is asserted
  and refuted by a skeptic. An **intent-dependent concern**, whose status as a bug needs
  the intended behavior, is routed to a characterization task that pins the actual
  behavior for the human to ratify, never asserted as a finding and never emitted as a
  bare question. When classifying a concern itself needs the intended behavior, it is
  treated as intent-dependent. This keeps `audit` honest on code whose intent the agent
  reconstructed rather than was told.
- The output is a `docs/audits/<slug>.md` remediation roadmap, a review-derived artifact
  gitignored and house-style-exempt like `docs/reviews/`, since it embeds proof
  evidence. It orders root causes before symptoms, and each step routes to the sibling
  that executes it (`design-spec`, `polish`, `test-spec`, or `preflight` for a fix's
  proof). `audit` applies nothing and posts nothing.

## Consequences

- `audit` is distinct from `preflight` (your branch versus base, your intent) and from
  `review-pr` (outward, approval-shaped). It is the inward review-and-improve pass for
  existing code.
- The roadmap is not a grill-gated plan. It is already proof-backed, so the human reads
  it and acts, and `preflight` reviews each fix branch the normal way when a step is
  implemented. This is a deliberate departure from `feature-plan`'s `docs/plans`
  artifact and the planning chain.
- `audit` never produces a vibe-finding. A correctness item is either a proven
  Proof-complete defect or a characterization task that pins a demonstration for the
  human, never an artifact-free suspicion.
- The cost is breadth. `audit` touches design, correctness, quality, and tests, but it
  deep-runs only comprehension, design, and correctness and routes the rest, which
  bounds the work and keeps the SKILL.md thin.

## Alternatives considered

- **A mode of `preflight` or `review-pr`.** Rejected. `preflight` is branch-versus-base
  and assumes your intent, `review-pr` is outward and approval-shaped. `audit` reuses
  their engines, it is not a mode of either.
- **Emit intent-dependent concerns as questions.** Rejected. On inherited code the
  intent is always unknown, so this is a pile of artifact-free suspicions, the
  vibe-finding the toolkit forbids. Routing them to characterization gives the human a
  demonstration instead.
- **A grill-gated `docs/plans` roadmap.** Rejected. The roadmap is already proof-backed
  and review-derived, so it belongs in `docs/audits` like a review packet, not in the
  planning chain.
