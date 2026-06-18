# ADR-0006: test-spec proves a test can fail, not that behavior is correct

## Status

Accepted

## Context

NitPickle is adding `test-spec`, a skill whose deliverable is the test itself. It
writes a failing executable spec test-first when no code exists yet, and it
identifies, strengthens, and characterizes the highest-value tests for code that
already exists. It needs a proof model, and neither ADR-0001 nor ADR-0005 covers it
cleanly.

ADR-0001 gates a Finding's severity on Proof and treats a test as the evidence for a
defect. `test-spec` inverts that. The test is the product, not the proof of something
else. ADR-0005 proves a refactor preserves behavior. `test-spec` proves a different
thing, that a test can fail for the right reason.

Two failure modes the research documents shape the contract. First, coverage is a
poor measure of a test's worth. A test that runs a line without asserting on its
behavior catches nothing (Inozemtseva and Holmes 2014, and mutation testing). Second,
a test generated from a program's current output cannot certify that output is
correct, because the program would be its own oracle (the oracle problem, Barr et al.
2015, Weyuker 1982). This is exactly how AI-generated tests fail, encoding current,
possibly buggy, behavior as if it were expected.

## Decision

A Kept test that `test-spec` proposes is gated on a Fail-demonstration, and the
correctness of any behavior it pins stays a human judgment.

- **Gated on a tiered Fail-demonstration, not on coverage.** The test must be shown to
  fail for the right reason. The strong tier is a killed mutant or a removed line,
  which shows the assertions discriminate. The weak tier is a red run against absent
  code, which shows only that the test is non-vacuous, not that its assertions are
  strong. A greenfield test-first spec reaches only the weak tier at red time. The
  strong tier is applied later, when the code exists, which is the test-after path. A
  test that cannot be shown to fail at all is downgraded and not kept.
- **Correctness is human-oracle-gated, scoped to characterization.** A test generated
  from existing behavior (test-after, a Characterization test) pins actual, not
  correct, behavior. The human Test oracle must confirm the pinned behavior is the
  intended spec before the test is kept. In test-first the human specifies the behavior
  up front, so the oracle is the human by construction, a different and weaker gate.
- **`test-spec` authors tests only, never production logic.** In test-first it writes
  the failing spec and stops at red, handing the green step to the human. It applies a
  Kept test to the working tree on per-change approval, never in bulk, and never
  commits or pushes (ADR-0004).

## Consequences

- `test-spec` is useful on untested and on greenfield code, because the tiered
  Fail-demonstration degrades honestly rather than refusing. The cost is that a
  greenfield spec carries only the weak tier until the code exists.
- The contract bounds a future change from auto-keeping a green test as correct. Green
  proves a test can fail, never that the pinned behavior is right. This is the ADR-0003
  and ADR-0005 logic applied to test authorship.
- `test-spec` stays a test skill. It does not assert defect Findings (Pre-flight) and
  does not refactor production code for quality (polish). The boundary against
  authoring production logic is the strongest form of controlled delegation, no sibling
  writes net-new production code.
- As with polish, this repo's CI proves only the consistency and house style of the
  skill files. The runtime Fail-demonstration and the Test oracle gate exist only when
  `test-spec` runs against a user's code.

## Alternatives considered

- **Gate a Kept test on coverage.** Rejected. Coverage finds untested code but is a
  poor measure of a test's worth, and a coverage target invites Goodhart.
- **Auto-keep any test with a green Fail-demonstration.** Rejected by ADR-0003's logic.
  Green proves the test can fail, not that the behavior it pins is correct, and
  correctness is the human oracle's call.
- **Let `test-spec` author the green-step production code on approval.** Rejected. No
  sibling authors net-new production logic, and even an approved diff makes `test-spec`
  the one code-writing skill and blurs the boundary forever. The test is the
  deliverable, the green step is the human's.
- **Fold the reframe into ADR-0001 or ADR-0005.** Rejected. Accepted ADRs are not
  re-litigated, and this is a distinct decision scoped to test authorship.
