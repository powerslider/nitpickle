# System design spec - format, quality bar, and diagram patterns

The reference the `design-spec` skill writes against. A spec is an **architectural
guide**: it should let a reader predict *where in the implementation* a
responsibility lives and *why*, without ever quoting the implementation.

## The discipline (hard rules)

0. **House writing style.** Short, professional prose, minimal cognitive load,
   no overcomplication. No em dashes and no semicolons anywhere. See
   `.nitpickle/preferences.md`.
1. **No code references.** No file paths, function names, class names, or
   snippets. Describe roles and responsibilities, not symbols. (Exception: a
   single config/contract shape may be shown only if it *is* the architectural
   decision and prose is genuinely worse - trim to the decision, never a working
   example.)
2. **Roles and responsibilities, not implementation.** For every component say
   what it *owns*, what it *does*, what it *depends on*, and - critically - what
   it **explicitly does not do**. The "does not" line is what prevents scope
   drift in the code.
3. **Don't drill down.** Stop at the level where a competent engineer could open
   the code and orient. No data structures, no algorithms, no error-handling
   minutiae. Name invariants and failure modes. Don't implement them.
4. **Don't overcomplicate.** Fewer, sharper components beat an exhaustive box
   inventory. If a component's responsibility fits in one clause, it may not
   deserve its own box.
5. **Every diagram earns its place.** A diagram must show structure a paragraph
   can't. Decorative diagrams are noise. If a sentence says it better, delete the
   diagram.
6. **Speak the glossary, respect the decisions.** Use `CONTEXT.md` terms exactly.
   Where the design embodies an accepted ADR, reference it (`see ADR-0003`)
   rather than re-arguing it.

## Section set (default)

Adapt to the system - omit a section that has no content, don't pad it. Billing
and integration are first-class here because most serious systems have them. If
the subject genuinely has neither, drop them and say so once.

### 1. Overview

- What the system/component *is*, in two or three sentences, in glossary terms.
- The problem it solves and its place in the larger landscape.
- Key design principles / non-negotiable invariants (3-6 bullets).
- **System context diagram** - the subject as one box, its external actors and
  neighboring systems around it, labeled by *relationship* (what flows, which
  direction), not by protocol.

### 2. Components

For each component, a compact card:

| Field | Content |
| --- | --- |
| **Role** | one line - what it is responsible for |
| **Responsibilities** | 2-5 bullets, behavior not mechanism |
| **Owns** | the data / decisions / lifecycle it is the source of truth for |
| **Depends on** | which other components/externals, and for what |
| **Does not** | the tempting responsibilities it deliberately refuses |

Precede or follow the cards with a **container/component diagram** showing how
the components relate (dependency direction, not call stacks).

### 3. Integration primitives

The seams - how components and external systems talk, at the level of *intent
and contract*, not schema:

- Interaction style per seam: synchronous request/response, async event, batch,
  stream.
- The contract's *meaning* (what is promised), idempotency, ordering guarantees,
  and what happens on failure/retry/partial success.
- Trust boundary crossings (which inputs are untrusted - tie to the trust-zone
  model if the repo has one).

Use **sequence diagrams** for the handshakes that matter.

### 4. Key flows (incl. billing)

End-to-end narratives of the flows that define the system. Billing is the
canonical one - metering/usage capture → rating/pricing → invoicing →
payment/settlement → refunds/adjustments - described as a relay of
responsibilities across components, naming where authority and money-state live
at each hop. Include other defining flows (auth, provisioning, the core
job/request lifecycle).

Each flow: a one-paragraph narrative + a **sequence diagram**, and a note on its
failure modes and where idempotency/consistency is enforced.

### 5. Cross-cutting concerns (sparingly)

Only the architectural shape of: consistency model, security/trust,
observability, multi-tenancy. One or two paragraphs each, only if non-obvious.

### 6. Glossary & decisions

Link the `CONTEXT.md` terms the spec relies on and the ADRs it embodies. This is
the bridge from the guide to the recorded language and decisions.

## Mermaid patterns

Pick the diagram type to the question. Mix types across the doc.

- **System context / containers** → `flowchart LR` (or `TB`). Boxes = roles,
  edges labeled with the relationship.

  ```mermaid
  flowchart LR
    User([Customer]) -->|places order| API[Order Intake]
    API -->|emits OrderPlaced| Bus[(Event Bus)]
    Bus --> Billing[Billing]
    Billing -->|charges| PSP[[Payment Provider]]
  ```

- **Flows (billing, integration handshakes)** → `sequenceDiagram`. Show the relay
  of responsibility. Annotate failure/idempotency with notes.

  ```mermaid
  sequenceDiagram
    participant Meter as Usage Metering
    participant Rater as Rating
    participant Inv as Invoicing
    participant PSP as Payment Provider
    Meter->>Rater: usage records (idempotent by event id)
    Rater->>Inv: priced line items
    Inv->>PSP: charge request
    PSP-->>Inv: settled / declined
    Note over Inv,PSP: declines retried with backoff. Invoice stays open
  ```

- **Lifecycles / state machines** → `stateDiagram-v2` (an invoice, a job, a
  subscription).

- **Data relationships** → `erDiagram` *only* when a relationship is
  architecturally load-bearing - and even then, entities and cardinality only,
  never columns. Usually skip. This risks drilling into implementation.

Keep each diagram to what fits on a screen. Two clear diagrams beat one sprawling
one.

## Quality bar (expert level)

A reviewer should be able to say yes to all of these:

- Could a new engineer, after reading this, predict which part of the code owns a
  given responsibility? (the whole point)
- Is every component's *boundary* clear - what it refuses as well as what it
  does?
- Are failure modes and invariants named at the seams where they're enforced?
- Does each diagram reveal structure the prose didn't?
- Is it free of code symbols, schemas, and implementation mechanics?
- Could it be *shorter* without losing an architectural fact? If yes, cut.
