# Conflict format

The reference `resolve-conflicts` writes against. It defines the per-Conflict
record the skill reports, and (from Phase 2) the resolution and proof attached to
each. A Conflict is the unit the skill works on: a content hunk where both sides
changed overlapping lines, or a file-level conflict (add/add, modify/delete,
both-deleted, rename, binary) that has no hunk. Classification and approval are
per hunk, staging stays per path.

## The run header

Lead with what operation is in progress and against what, so the reader knows the
ours/theirs framing before reading any Conflict:

```
Operation: merge | rebase | cherry-pick
At:        <the commit being merged, replayed, or picked>
Mine:      <branch or commit that holds the user's work>
Incoming:  <branch or commit being integrated>
Conflicts: <count>, <n> trivial, <n> semantic, <n> file-level
```

For rebase the mapping is inverted (see SKILL.md), so state Mine and Incoming
explicitly rather than the raw ours/theirs labels.

## The per-Conflict record

Each Conflict carries:

```
path        the conflicted file
kind        content | add/add | modify/delete | both-deleted | rename | binary
class       trivial | semantic | file-level   (content only is trivial/semantic)
where       hunk line range for content, or "whole file" for file-level
base        what the common ancestor had (stage 1), or "none" when absent
mine        the user's side, mapped from the operation
incoming    the integrated side, mapped from the operation
```

Once the skill proposes a resolution, the record gains, reusing the Finding
schema:

```
resolution  the proposed merged content, or the chosen side for file-level
proof       test | repro | diff | none, the artifact that backs the resolution
confidence  high | medium | low, derived from the proof, not a vibe
severity    gated on the proof (a green proof does not raise a semantic
            resolution to auto-apply)
intent      the behavior each side introduced, and a note that the resolution
            still carries both (the both-sides-intent check)
```

A trivial hunk's proof is the deterministic index check (a side is a no-op). A
semantic hunk's proof is the policy commands run against the applied resolution,
with the honest caveat that green does not prove intent preservation. Binary and
file-level Conflicts carry a chosen side, never synthesized content.

## Reading rules

- Read the three versions from the index, not the conflict markers: `git show
  :1:path` (base), `:2:path` (ours), `:3:path` (theirs). Markers are
  style-dependent, the index is not.
- Map ours and theirs to mine and incoming by operation. Never assume ours is
  mine, because rebase swaps them.
- A missing stage signals a file-level kind: no stage 1 is add/add, a missing
  stage 2 or 3 is a delete on that side.
