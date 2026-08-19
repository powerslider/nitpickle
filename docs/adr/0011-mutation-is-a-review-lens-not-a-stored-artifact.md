# ADR-0011: mutation is a review lens and a proof criterion, not a stored artifact

## Status

Accepted

## Context

test-spec already injects a Mutant and discards it. The strong tier of a
Fail-demonstration is a killed mutant, which proves a Kept test's assertions
discriminate. That proof happens once and is never repeated, and nothing else in
NitPickle uses mutation at all.

The obvious way to extend this is to record the mutants in a persisted battery
file so a later session can replay them. That design was worked through and
rejected. It fails on four counts. A persisted battery is a second copy of source
snippets that goes stale as the code moves, with one study putting mutant
relevance decay at 52 percent across releases. A tracked battery produces churn
in every pull request that touches the code it covers. Some repositories will not
accept a tracked artifact of that kind at all. And a battery kept only to be
replayed is derived data whose one non-derivable property, the historical
verdict, buys cross-time erosion detection at the cost of a permanent second
source of truth.

Against that, the review use case needs no persistence whatsoever. Asking whether
a change under review is pinned by its tests is answered by injecting faults into
the change and observing whether anything fails, computed fresh and thrown away.
The same mechanic pointed forward answers whether a planned phase has landed
with tests that discriminate.

Two existing seams already carry this. Review mode is a lens both review surfaces
consume. Proof surface is a field every Feature plan phase already names.

## Decision

Mutation is a lens applied during review and a criterion named in a plan. It is
never a stored artifact.

- **A Mutation battery is ephemeral by construction.** It is a bounded set of
  Mutants computed for one target and discarded after, in the same category as
  the throwaway proof test Pre-flight and polish synthesize. Nothing is written
  to disk, nothing is tracked, nothing is cached.
- **Mutation augments a Review mode rather than being one.** Modes are
  attention-directing lenses and only one applies at a time. Mutation is an
  evidence-gathering mechanic that composes with any of them, so it is a separate
  toggle in Policy, defaulting to automatic. Automatic means it runs when a test
  command exists, the baseline is reproducibly green, and the projected cost fits
  the budget, and otherwise stands down with a stated reason.
- **A surviving Mutant is a gap in the tests, never a defect in the code.** It is
  a Finding carrying a runnable artifact, routed to test-spec, never asserted as
  a behavioral bug. Whether the unpinned behavior is correct is a Test oracle
  question.
- **A mutation score is never a gate.** Counts and specific survivors are
  reported. No ratio, no threshold, no target.
- **Mutation acceptance is stated behaviorally.** A Feature plan phase names the
  perturbation its tests must catch, not a file and line, because a plan is
  written before the code exists. A specific site may be pinned when it is
  already known and stable.
- **An existing mutation tool wins.** Where Policy configures one, NitPickle
  shells out and ingests its output as evidence. Where none exists, it hand
  injects the way test-spec already does. It never installs or configures one.

## Consequences

- No new artifact class, no tracked file, no diff churn, no second source of
  truth that can drift from the code. The persistence question disappears rather
  than being answered.
- Cross-time erosion detection is given up. A test whose assertions are hollowed
  out months after it was written is caught only if a review happens to touch
  that code. This is the real cost of the decision and it is accepted knowingly.
- Diff-scoped generation under-detects. Most mutants relevant to a commit sit
  outside its changed lines, so a review-time lens sees a fraction of what a
  whole-target pass would. Actionability is preferred to completeness.
- Nothing shippable here can be proven by this repository's CI. Dropping the
  persisted format removed the only machine-checkable surface the feature would
  have had, so `make lint` proves consistency and house style and nothing more.
  This is the same bound already recorded for test-spec and polish.
- Defaulting the toggle to automatic means the mechanic runs without being
  selected, which is what makes it capable of changing behavior. The risk
  accepted is that a slow or flaky suite produces cost or noise on first
  contact, which the automatic stand-down exists to contain.
- The decision bounds a future change from reintroducing a stored battery
  without revisiting this record.

## Alternatives considered

- **A persisted battery, tracked in git.** Rejected. Churn in every touching pull
  request, a second copy of source that decays, and repositories that forbid the
  artifact outright.
- **A persisted battery, gitignored.** Rejected. Keeps the staleness cost, loses
  the cross-person value that was the only reason to persist, and still needs a
  format, a schema, and an anchoring mechanic to maintain.
- **A dedicated mutation skill.** Rejected. The mechanic composes into two
  existing review surfaces and one existing plan field, so a fifteenth skill
  would add a consistency surface without adding a capability.
- **Encoding every mutant as a real test.** Rejected as infeasible, though it is
  the right instinct. A killed mutant is largely expressible as an ordinary test
  case, and a surviving one is a request to write one. What cannot be expressed
  is a test asserting its own strength, and building that means authoring a
  language-specific mutation harness, which is what the existing tools already
  are.
- **Gating on a mutation score.** Rejected. Coverage is already rejected as a
  gate because a target invites Goodhart, and a ratio here fails the same way.
- **Leaving the toggle off by default.** Rejected. An opt-in lens in a toolkit
  this size is selected rarely enough to be equivalent to not shipping it.
