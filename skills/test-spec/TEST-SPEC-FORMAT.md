# Test-spec - Kept-test schema and proof protocol

The reference `test-spec` writes against. A Kept test is one test authored to keep,
with a Fail-demonstration that shows it can fail for the right reason and an oracle
status that records who certified the behavior. The schema reuses the Finding field
vocabulary where it applies, drops the severity ladder for apply-or-skip, and replaces
a proof-of-defect with a Fail-demonstration plus an oracle gate.

## The two modes at a glance

| Mode | Entry | Reaches red via | Fail-demonstration tier | Test oracle | Green step |
| --- | --- | --- | --- | --- | --- |
| **Test-first** | the intended behavior was supplied (spec, feature, reported bug) | absent code (new) or the live defect (a bug) | weak then strong (new), strong (bug) | the supplied spec, no gate | the human writes it |
| **Test-after** | the code is the only witness of its behavior | an injected mutant or a removed line | strong (assertions discriminate) | the human confirms the pinned behavior | code already exists |

Both share the engine shell: rank by risk, write through the public interface, attach
the sharpest Fail-demonstration, gate correctness on the human, apply on per-test
approval. They differ only in the columns above.

## Kept-test schema

```
behavior        one line: the behavior under test, in glossary terms
form            boundary | equivalence | decision-table | state-transition |
                pairwise | property | characterization | example
target          file:line-range the test exercises, through the public interface
why             one paragraph: why this test, ranked by risk not coverage
test            the proposed test code, in the repo's existing idiom
proof           fail-demonstration | none
demonstration   the tier and its evidence: the killed mutant or removed line and the
                resulting red run (strong), or the red-against-absent-code run (weak)
oracle          specified (human spec up front) | pinned (awaiting human approval) |
                approved (human confirmed the pinned behavior is the intended spec)
policy_ref      which preference, glossary term, policy rule, or ADR shaped it, if any
```

A Kept test has no severity. It is apply, skip, or suggest-only, the human's call.
`proof: none` means the test could not be shown to fail at all, so it is downgraded to
a suggestion and never applied.

## Fail-demonstration, tiered

A Kept test must be shown to fail for the right reason. Coverage is a gap-finder, never
the gate. Build the demonstration in an isolated worktree. Take the sharpest tier the
code allows.

1. **Strong: killed mutant or removed line.** The code exists. Inject a small fault
   into the behavior under test (remove a line, flip a condition, or run a configured
   mutation tool) and confirm the test goes red, then restore. A test that survives the
   mutant asserts nothing, strengthen it. The killed mutant is the proof that the
   assertions discriminate. `confidence: high`.

2. **Weak: red against absent code.** The behavior does not exist yet (test-first). The
   test fails because the code is absent, which proves only that the test is
   non-vacuous, not that its assertions are strong. This is the most a greenfield spec
   can reach at red time. `confidence: medium`, labeled as the weak tier. The strong
   tier is applied later, when the code is green, through the test-after path.

3. **None: cannot be shown to fail.** The behavior cannot be exercised by a fast,
   deterministic test (untestable side effects, no reachable seam). The test cannot be
   proven, downgrade it to `proof: none`, present it as suggest-only, and report the
   missing seam. Never keep it silently.

## Test oracle gate

- A **characterization** test pins current behavior. Its passing proves consistency
  with what the code does, never that the behavior is correct. Present the pinned
  behavior plainly and set `oracle: pinned` until the human confirms it is the intended
  spec, then `oracle: approved`. Never keep a pinned test as correct without that
  confirmation, the program cannot be its own oracle.
- A **test-first** spec is written from the human's behavior list, the up-front spec,
  so `oracle: specified` by construction.

## Test-list, then one spec at a time

In test-first mode, list the behaviors to test up front, then write one failing spec at
a time and stop at red. Do not emit many failing tests at once, and do not author the
production code that turns them green, that is the human's step.

## Apply gate

- Applied to the working tree only, one approved Kept test at a time, never in bulk.
- A `proof: none` test is never applied by test-spec. The human may take it by hand.
- A characterization test with `oracle: pinned` is never applied until the human
  approves the pinned behavior.
- test-spec authors no production logic and never commits, pushes, or runs any other
  write command.

## Presentation

Lead with a one-line summary and counts (proposed, proven, suggest-only, awaiting
oracle). Rank Kept tests by risk, then confidence. Each entry shows the behavior, the
form and why, the test code, the Fail-demonstration and its tier, and the oracle
status. Offer `[Apply] [Skip] [Suggest only]` per test.
