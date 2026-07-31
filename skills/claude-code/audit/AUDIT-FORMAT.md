# Audit - roadmap schema and the pass protocol

The reference `audit` writes against. A remediation roadmap is a review-derived artifact
at `docs/audits/<slug>.md` that comprehends an existing feature and lays out a
root-cause-ordered set of improvement steps, each routed to the sibling that executes
it. It reuses the Finding field vocabulary where it applies and adds the routing and the
root-cause link.

## Roadmap document structure

```
1. Summary       one-line state of the feature and the headline root causes.
2. Comprehension what the feature does, its seams and responsibilities, and the
                 intent the human ratified. Inferred, then confirmed.
3. Steps         the remediation steps, ordered cause before symptom (schema below).
4. Sampled       what was deep-examined and what was left, since a large feature is
                 not exhaustively proven. No silent truncation.
```

## Step schema

```
altitude     design | correctness | quality | test
type         proof-complete-defect | characterization | refinement | design
root_cause   the higher-altitude cause this step traces to, or "root" if it is one
routes_to    preflight | polish | test-spec | design-spec | direct
what         the concrete change, one line
why          one paragraph, mechanism not opinion, in glossary terms
evidence      for a proof-complete defect, the proof and the refutation. For a
              characterization step, the behavior to pin. For others, the target
proof_surface where the fix is proven once implemented, named not built here
```

A step has no severity ladder. It is ordered by its root-cause depth, causes first. A
step routes its execution to a sibling, `audit` does not perform it.

## Comprehension protocol (the gate)

1. Reconstruct the design from the code, its seams, responsibilities, and data flow.
2. Infer the intended behavior, and present it to the human to ratify. The agent
   reconstructed the intent, it was not told it.
3. An unconfirmed intent point becomes a characterization step, never an assumption.
4. Emit a routed `design-spec` step when the target is complex enough to warrant a
   reusable architecture doc. Otherwise the comprehension lives in the roadmap.

Nothing intent-dependent leaves comprehension as an open question.

## Correctness, two honest classes

Run the proof loop in an isolated worktree and refute each finding with a skeptic before
asserting it.

1. **Proof-complete defect.** Wrong provably from the code alone with no assumption about
   intended behavior: a crash, a nil or null deref, an unhandled error path, a resource
   leak, a deadlock, dead or unreachable code, or code whose own paths can reach a state
   it then assumes impossible. Proven, refuted, asserted as a finding.

2. **Intent-dependent concern.** Whether it is a bug needs the intended behavior. Do not
   assert it and do not emit it as a bare question. Route it to a characterization step
   that pins the actual behavior with a runnable test for the human to ratify. Emit only
   the highest-risk concerns, ranked by churn, coupling, and error and edge branches,
   capped, and record in Sampled what was left. When classifying a concern itself needs
   the intended behavior, treat it as intent-dependent, the gated default.

## Synthesis, cause before symptom

Cluster the asserted defects, characterization steps, and design and quality findings
across the whole feature by shared root cause. Connect each symptom to the
higher-altitude cause behind it, and order the roadmap so a cause is fixed before the
symptoms it produced. A cluster of low-level steps that all trace to one shallow module
or wrong seam is stated as one cause with its dependent steps under it.

## Posture

- `audit` writes only the roadmap and an optional routed design-spec. It applies nothing,
  commits nothing, posts nothing.
- The roadmap is gitignored and house-style-exempt like `docs/reviews/`, since it embeds
  proof evidence.
- Each step routes to a sibling for execution. The human reads the roadmap and acts.
