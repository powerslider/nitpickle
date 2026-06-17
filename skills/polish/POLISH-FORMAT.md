# Polish - Refinement schema and preservation-proof protocol

The reference `polish` writes against. A Refinement is one proposed quality
transform with a proof that it preserves behavior. The schema reuses the Finding
field vocabulary where it applies, drops the severity ladder for apply-or-skip,
and replaces a proof-of-defect with a proof-of-preservation.

## Refinement schema

```
dimension       reuse | simplification | altitude | dead-code | naming
target          file:line-range
why             one paragraph, mechanism not opinion, in glossary terms
confidence      high | medium | low      (derived from the proof, not vibes)
proof           preservation | none
evidence        the differential: commands run + their result, or the
                characterization test + its green run across the transform
transform       the proposed diff
policy_ref      which preference, glossary term, or ADR shaped it, if any
```

A Refinement has no severity. It is apply, skip, or suggest-only, the human's
call. `proof: none` means preservation could not be shown, so the Refinement is a
suggestion and is never applied silently.

## Behavior-preservation proof, tiered

The proof is a differential that shows observable behavior is unchanged across the
transform. It demonstrates the change is safe, never that it is better. Build it in
an isolated worktree. Take the sharpest tier the code allows.

1. **Covered by policy commands.** The `policy.yaml` commands (test, lint) already
   exercise the touched code. Run them before and after the transform. Green on
   both sides is the proof. `confidence: high`.

2. **Synthesized characterization test.** No existing test covers the touched code.
   Write a throwaway test that pins the current observable behavior through the
   public interface, in the repo's existing test idiom (read two or three
   neighboring tests first). Run it before the transform to confirm it passes
   against current behavior, then after. Green across both is the proof. The test
   is an artifact, shown not committed, and it exists to prove this transform, not
   to hunt for defects, which stays preflight's job. `confidence: high` to
   `medium`, honest about how much the test pins.

3. **No characterization seam.** The behavior cannot be pinned by a fast,
   deterministic test (untestable side effects, no reachable seam). The Refinement
   cannot be proven safe. Downgrade it to `proof: none`, present it as a
   suggest-only Refinement, and report the missing seam, mirroring preflight's
   missing-seam rule. Never apply it silently.

## Apply gate

- Applied to the working tree only, one approved Refinement at a time, never in
  bulk.
- A `proof: none` Refinement is never applied by polish. The human may take it by
  hand.
- Polish never commits, pushes, or runs any other write command (ADR-0004).

## Presentation

Lead with a one-line summary and counts (proposed, proven, suggest-only). Rank
Refinements by confidence, then by dimension. Each entry shows the dimension, the
target, the why, the transform, and the evidence. Offer `[Apply] [Skip]
[Suggest only]` per Refinement.
