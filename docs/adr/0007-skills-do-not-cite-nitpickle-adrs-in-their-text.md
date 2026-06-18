# ADR-0007: Shipped skills state their rules without citing NitPickle's own ADRs

## Status

Accepted

## Context

The skills ship as a Claude Code plugin into other repositories. Each skill
instructs the agent to read the consuming repo's `docs/adr/` as the decisions in
force there. Several skills also cited NitPickle's own design ADRs (ADR-0001 and up)
by the same `ADR-NNNN` notation, as a provenance breadcrumb for a rule.

Those are two ADR namespaces under one notation. In any repo but this one, a bare
`ADR-0006` in skill text points at a document that is not present, and it can be
mistaken for the consuming repo's own ADR of that number. The citation is inert for
the runtime agent, since the rule is stated inline anyway, and serves only
NitPickle's maintainers, so it does not belong in the shipped instruction.

## Decision

Shipped skill text (`skills/*/SKILL.md` and the `*-FORMAT.md` references) states each
rule self-containedly and does not cite NitPickle's own ADR numbers. The rule is the
instruction. The ADR is the rationale, which lives in `docs/adr/` and
`docs/ARCHITECTURE.md` for maintainers.

- Where a skill instructs the agent to cite the *consuming* repo's ADRs (design-spec),
  it uses a generic placeholder `ADR-NNNN`, never a sample number that collides with
  NitPickle's own.
- Project documents that describe NitPickle itself (README, CHANGELOG, ARCHITECTURE,
  and the ADRs) reference NitPickle's ADRs freely. They are unambiguously about this
  repo, not instructions running in another.

## Consequences

- A shipped skill reads correctly in any repo, with no dangling or colliding ADR
  reference.
- The breadcrumb from a skill rule back to its ADR is gone from the skill text, so
  each rule must stand on its own. Maintainers trace a rule to its decision through
  `docs/ARCHITECTURE.md` and the ADRs.
- A new skill states its rules without ADR citations, and review checks for a stray
  `ADR-NNNN` in skill text. A validator rule could enforce this later, it is not added
  now.

## Alternatives considered

- **Qualify the cites as "NitPickle ADR-0006".** Rejected. It still leaks
  NitPickle-internal provenance into another repo's runtime context, and it is clunky
  repeated across every skill.
- **Keep the bare cites.** Rejected. A dangling or colliding reference across the
  distribution boundary is exactly the kind of untrustworthy detail the toolkit exists
  to avoid.
- **Add a validator rule banning `ADR-NNNN` in skill text now.** Deferred. A
  reasonable future enforcement, but out of scope for recording the convention.
