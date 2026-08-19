# Engineering principles (global defaults)

A portable set of heuristics for writing and reviewing code, distilled from
watching real, judgment-driven decisions play out on a real codebase rather
than from a style guide. Not rules to enforce mechanically, questions to run
through before writing or reviewing something.

Install at `~/.claude/nitpickle/principles.md` (or `~/.config/nitpickle/` on
Codex). The code-touching skills consult this file the way they consult the
glossary and your taste.

## 1. Complexity must earn its place

Any indirection, special case, or defensive branch needs either a test that
fails without it or a benchmark that shows it costs something real. If
neither exists, do the simpler thing. This applies symmetrically: the bar
doesn't move depending on who's proposing the complexity, including yourself.

A cheap, honest answer to "I don't know if this is worth it" is often just to
measure it. If the measurement doesn't clear the bar, apply the simpler
version anyway and say so, rather than defending the complexity in prose.

## 2. Reason about the dominant cost, not the step count

When comparing two designs, don't count total operations, weigh them. A
design with three cheap in-memory steps usually beats one with two steps if
one of those two is a disk read, a network call, or a lock under real
contention. Identify which resource is actually expensive in context, then
optimize for touching it less, treating everything else as close to free.

This also means a design that looks more "efficient" by having fewer lines or
fewer branches isn't automatically cheaper. Measure or reason about the
expensive resource specifically.

## 3. Distinguish verified risk from hypothetical risk

A risk that's actually been observed, reproduced, or shown to exist in real
data deserves a fix, or a clearly-stated reason it isn't getting one yet. A
risk that's only "this could happen in theory" deserves a comment naming it
precisely, not permanent code built to defend against it.

This cuts against sunk cost: if you've already built a fix for a risk and
then discover it has no verified trigger, revert the fix and leave the note.
Paying an ongoing complexity cost for an unconfirmed problem is worse than
naming the gap plainly and moving on. If the risk later becomes verified, the
note is exactly what makes it cheap to act on.

## 4. One component owns a piece of state end to end

When a lifecycle spans two components (opening something and closing it,
claiming something and releasing it, starting something and marking it
done), split ownership is where invariants quietly break. Either give one
component the entire lifecycle, or write down the exact sequence explicitly
enough that "who does step 3" is never a question two readers could answer
differently.

If a decision, a write, and a cleanup are conceptually one operation, keep
them in the same function or the same struct, even if that means folding two
smaller types into one. A type that only exists to hold half of a lifecycle
is a sign the split was premature.

## 5. Comments state the why or the contract, never the what

A comment earns its place by naming a constraint, an invariant, or a
consequence a future reader could get wrong, not by restating the line below
it in English. This matters most on anything exported or anything whose
correct behavior looks surprising out of context (a function that must never
block, a check that looks redundant but isn't, a field ordering that matters).

A useful test: if someone hits the exact bug this comment is protecting
against six months from now, does the comment tell them why it's wrong, or
just what the code does? If it's the latter, delete it or rewrite it.

A related trap: don't document where something is called from or how a
caller uses a return value. That information belongs to the caller, not the
callee, and it goes stale the moment a second caller appears. Document the
thing itself.

## 6. Prefer plain control flow over callback or closure indirection

An early return followed by a deferred cleanup is almost always easier to
read than a function that threads a callback through an API to be invoked
later, especially when the indirection exists only to make one code path
testable. If the real caller never needs the flexibility, don't add it for a
test's convenience, restructure the test instead.

This isn't a ban on closures. It's a preference for the version with fewer
layers between "what happens" and "where it's written," when both versions
are otherwise equivalent.

## 7. Tests must prove the behavior they claim, not just execute it

Before trusting a test, ask what happens if you delete the specific line it's
supposedly protecting. If the test still passes, it isn't testing what its
name says. This is worth checking explicitly, not just assuming a passing
test means the invariant holds.

Duplicated test setup across cases is a sign two tests are really one test
with a parameter. Merge them. And name tests so a failure is greppable
immediately, not so a human has to parse a sentence to find the right file.

A subtler version of this: don't let test-only logic silently reimplement
production logic to make a value easy to construct. If a test independently
recomputes something production also computes, that's a hidden coupling: a
change to the production formula can leave the test happily agreeing with
itself while asserting the wrong thing.

## 8. A decision explicitly settled stays settled

Once a question has been discussed and a call made, whether in a doc, a
thread, or a conversation, don't relitigate it in every place it resurfaces.
Apply it, and if you're recording the outcome somewhere (a reply, a commit,
a comment), say plainly that it's already settled and why, so the next
reader doesn't reopen it either.

The flip side matters just as much: a settled decision isn't sacred if new
evidence shows up. Reverse it openly when that happens, rather than treating
"we already decided this" as immunity from being wrong.

## 9. A cheap safeguard against a real footgun doesn't need to justify itself the same way

Principle 1 says complexity needs proof. It doesn't mean every defensive
check is complexity. A small, clearly-scoped guard that turns a silent
correctness violation into a clear, immediate error (a run-once check, a
precondition assert, a sanity check on a value that must never repeat) is
usually worth its few lines even without a benchmark, because the thing
you're guarding against is a category of bug, not a performance number. The
question to ask is "is this a real footgun or just code bloat," not "can this
line be deleted."

## 10. Hold your own suggestions to the same bar you hold everyone else's

If you propose an optimization, a new abstraction, or a defensive check,
apply principle 1 to your own idea before anyone else has to. It's fine, and
common, to propose something and then talk yourself out of it once you
notice it doesn't clear your own bar. Say so out loud rather than quietly
keeping it in.

## 11. Defer to an existing, stated convention instead of re-deriving a decision from scratch

If a team, a style guide, or a prior decision has already settled a question
(naming, error-message phrasing, where constants live, which library to
use), treat that as an input, not a fresh design problem. Re-litigating a
settled team convention inside an unrelated piece of work wastes the
conversation's real budget on a question that isn't actually open. Follow
the convention, and if it's genuinely wrong, raise changing it as its own
conversation.

## A note on apparent contradictions

These principles can look like they conflict when applied to different
surfaces. A push toward looser, more readable prose in documentation can look
like it contradicts a preference for precise, individually-citable contracts
elsewhere. It usually isn't a contradiction, it's the same instinct
(principle 1: does this structure earn its keep given how the thing actually
works now) applied somewhere new. Before calling two decisions inconsistent,
check whether they're actually the same principle read against two different
costs. If they really do conflict, that's worth surfacing explicitly rather
than smoothing over, since it usually means the tradeoff itself needs a
decision, not a rationalization.

## Checklist before writing or opening something for review

- Can I point at a test that fails if this behavior breaks, or a measurement
  that shows this costs something real? If not, either write one or do the
  simpler thing instead of defending the special case in prose.
- Am I threading a callback or closure through an API just to make one code
  path testable? If the real call site never needs it, restructure the test
  instead of adding the indirection.
- If someone hits this exact bug months from now, will this comment tell them
  why, or just restate the code below it?
- Does this comment mention where the function is called from, or what the
  caller does with the result? Cut that, document the thing, not its callers.
- Does exactly one component own this piece of state for its whole lifecycle,
  or is ownership split across two? If split, either fold them together or
  write the exact sequence down explicitly.
- Is this risk verified in the system today, or is it a "could happen"
  concern? If unverified, name it plainly and move on. If verified, fix it or
  state precisely why not yet.
- Between two correct designs, which one touches the actually expensive
  resource fewer times, not which one has fewer total steps?
- Is there a stated convention that already answers this question, rather
  than a fresh decision to make from scratch?
- Have I merged this into an existing test if it exercises the same logic,
  and named it so a failure is greppable?
- Would deleting this test's core assertion still leave it passing? If so,
  it isn't proving what it claims to.
