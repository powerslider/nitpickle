# ADR-0012: engineering principles are a separate consulted convention with an automated seeder, not folded into preferences

## Status

Accepted

## Context

A set of engineering principles (11 judgment heuristics plus a pre-review
checklist) needs to reach every skill that writes or reviews code, applied by
default the way the glossary, decisions, and taste already are. Several of the
principles overlap mechanics NitPickle already enforces, proof-gated severity
covers verified-vs-hypothetical risk and tests-prove-behavior, the ADR discipline
covers settled-decisions-stay-settled, house style covers comment-why-not-what. So
the task is to single-source the principles, not to paste 183 lines into roughly
28 SKILL.md files across the two per-harness trees.

Two homes were viable. Folding the principles into `preferences.md` is
the cheapest, preferences is already in the byte-synced resolution block and
already read by the code skills, so it needs no new resolution text and no
per-skill edits. Against that, folding conflates two different registers, taste
(house style, phrasing, where constants live) and craft (how to reason about a
design and prove a change), and it reaches every skill that reads preferences
rather than the code-touching subset the principles are written for.

A separate `.nitpickle/principles.md` keeps craft distinct from taste, the exact
register the source doc uses ("not rules to enforce mechanically, questions to run
through"). Its cost is a one-time, checked extension of the resolution block and a
load-point edit in each consuming skill, guarded so a skill cannot silently drop
the reference.

A second decision rode in with the first. The principles only apply "by default in
any repo" if the global default is actually seeded, and seeding was manual and
inconsistent, `README.md` used a glob while `defaults/README.md` enumerated files
by name and would silently miss any new default. There was no automated seeder,
the old one was deleted and the hook installer wires only the guardrail.

## Decision

Engineering principles are a dedicated convention input, `.nitpickle/principles.md`,
consulted by the code-touching skills and seeded to the global default by an
automated glob-based seeder. They are never folded into preferences.

- **A separate file, not a preferences section.** `.nitpickle/principles.md` holds
  the full set of engineering principles as a standalone, portable document. Craft
  is kept separate from taste.
- **The whole doc, not a NitPickle-specific reconcile.** An earlier draft stated
  only the heuristics absent from existing mechanics and mapped the rest to the
  mechanic that owns them. That was reversed. The complete principles read better
  and travel better than a commentary on what NitPickle already enforces, so the
  file carries all of them. The overlap with proof-gated severity, the ADR
  discipline, and the house-style comment rule is accepted deliberately, the small
  redundancy is worth a principles doc that stands on its own.
- **Resolved through the existing byte-synced block.** `principles.md` is named in
  the resolution block carried by the full-block skills in both trees, inheriting
  local-plus-global resolution, "when only one exists it applies unchanged." No
  per-skill resolution note, that is the unchecked drift the byte-sync prevents.
- **Consulted by the code-touching skills only.** The eight skills that write or
  review code reference it at their own load points. A completeness check in the
  validator fails if any of them drops the reference. The utility skills do not
  consult it, the principles self-gate to code work.
- **Seeded by an automated, glob-based, non-clobber seeder.** `seed-defaults`
  copies all of `defaults/nitpickle/*` (so a new default needs no seeder change) to
  the harness global config, seeding only absent files so a customized policy or
  preferences is never overwritten, with an explicit refresh flag. The hook
  installer invokes it so a Codex plugin user seeds config and wires the guardrail
  in one command.
- **Judgment, not a rule.** No mechanical enforcement of the principles is added.
  The only new check is the completeness guard on the consuming skills.

## Consequences

- Craft and taste stay separable, a repo can override its principles without
  touching its house-style preferences and vice versa.
- One source, no per-skill duplication, and the resolution byte-sync
  keeps the local-plus-global rule identical across both trees.
- The resolution block and each consuming skill's load section grow by one entry.
  This is a one-time edit across the full-block skills, guarded by the existing
  byte-sync check and a new completeness check.
- The `CODE_SKILLS` list the completeness check reads must be updated if the
  code-skill set changes. This is a small maintenance surface, documented next to
  the check.
- The principles apply by default in any repo only after the global default is
  seeded. The automated glob seeder makes that one command and future-proof, but a
  user who never seeds gets nothing, the same dependency `policy.yaml` and
  `preferences.md` already carry, now load-bearing for principles too.
- Non-clobber seeding means a user with an older customized default does not
  receive an updated one silently. The refresh flag and a skipped-files summary
  exist to surface that.
- Nothing in the principles themselves is machine-checked, consistent with the doc
  and with proof-gated severity owning the enforceable parts. `make check` proves
  house style, resolution byte-sync, parity, and that the eight skills keep
  consulting the file, and nothing more.

## Alternatives considered

- **Fold the principles into `preferences.md`.** Rejected. Cheapest (no new
  resolution text, no per-skill edits), but it conflates craft with taste and
  reaches every skill that reads preferences rather than the code-touching subset.
  The craft-vs-taste separation is worth the one-time checked resolution-block
  edit.
- **A byte-synced canonical block in every skill.** Rejected. 183 lines times
  roughly 28 files is bloat, irrelevant to the utility skills, and fragile to keep
  identical.
- **A separate file resolved by a per-skill resolution note.** Rejected. It
  recreates unchecked copies of the resolution text, the exact drift the byte-sync
  was built to stop. The approved path resolves through the checked block.
- **An enumerated seeder (copy each default by name).** Rejected. That is the
  current gap, it silently misses any new default including `principles.md`. The
  seeder globs the directory instead.
- **Leaving `engineering-principles.md` at the repo root and linking it.**
  Rejected. A root file no skill reads is the current non-solution.
