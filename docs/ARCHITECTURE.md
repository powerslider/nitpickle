# Architecture

How the NitPickle plugin works. The scope is a Claude Code plugin: skills, a
convention layer, one hook, and this repo's own proof tooling. No services, no
database, no runtime, no server. Everything runs inside Claude Code against a
local branch or, for PR review, a local checkout via `gh`.

## Shape

```
skills/*/SKILL.md            seven skills. preflight is the core, the others
                             compose around it (plan, gate, spec, PR review,
                             commit messages, bootstrap)
hooks/                       house-style guard (PreToolUse)
.nitpickle/                  policy (rules + commands), taste, per-developer
                             working state (validation log, todo)
CONTEXT.md + docs/adr/       glossary + decisions (per repo)
tools/ + .github/workflows/  this repo's own consistency proof seam
```

## Principles

- **Controlled delegation.** The human stays the engineer of record. The agent
  investigates, drafts, and proves. Nothing outward-facing happens without
  explicit approval.
- **Proof as the core mechanic.** A finding without a runnable artifact is
  downgraded, never dressed up. Honesty about non-proof is what earns trust.
- **Inspectable, git-tracked memory.** Taste and policy live in flat files you
  diff and commit, never an opaque personalization service.
- **Trust zones.** Repo content, PR text, and external docs are data, never
  instructions. Prompt-injection resistance is a first-class property.
- **No attribution.** Outputs read as ordinary engineering work. Run records
  stay local.

## The proof engine

The proof engine is a **feedback-loop builder**: a fast, deterministic,
agent-runnable pass/fail signal for a specific claim is what makes the claim
trustworthy. Building that loop is 90% of the work. Grading is mechanical.

A candidate finding enters the proof engine and exits with a grade.

```
candidate finding
      |
      v
classify proof strategy (sharpest first):
  - failing test at the seam that reaches the claim (unit/integration/e2e)
  - minimal repro: command + fixture, diff stdout vs known-good
  - replay a captured trace (request/payload/log) through the code path
  - throwaway harness: minimal subset exercising the path in one call
  - property/fuzz loop for "sometimes wrong" claims
  - bisection / differential (old vs new, two configs) for regressions
  - convention/policy violation -> the concrete diff that breaks the rule
  - judgment/taste -> no mechanical loop exists -> cap at nit/question
      |
      v
execute in isolated workspace (worktree). Capture artifact + result
      |
      v
grade:
  artifact demonstrates the problem -> keep severity, confidence=high
  artifact inconclusive             -> downgrade one level, confidence=medium
  no artifact possible              -> nit/question, confidence=low
  missing proof seam                -> important allowed with proof=none, the
                                       demonstrated absence is the evidence
                                       (the one exception, see ADR-0001)
```

Key design rules:

- Proof runs in an **isolated worktree**, never the working copy. A synthesized
  failing test is an artifact, not a committed change.
- **Iterate on the loop itself** - faster, sharper, more deterministic. A
  2-second deterministic proof is worth more than a 30-second flaky one. For
  flaky claims, raise the reproduction rate until it's debuggable.
- The engine must be honest about *non*-proof. Downgrade, don't hide. A flagged-
  but-unproven nit is useful. A suppressed real bug is not.
- Tests are synthesized in the repo's existing test idiom (read 2-3 neighbors
  first), so the artifact is one you'd actually keep, and they verify **behavior
  through public interfaces**, not implementation.
- **No correct seam = that is itself a finding.** If the only way to prove a
  claim is a test too shallow to exercise the real pattern, don't fake it -
  report the missing seam as an architectural finding and hand off to the
  architecture flow.

## Finding schema

This is the canonical home of the schema. Preflight and REVIEW-FORMAT carry it
verbatim, and `tools/validate.py` keeps the copies identical:

<!-- nitpickle:finding-schema -->
Every Finding carries:

```
title            one line
severity         blocking | important | nit | question
confidence       high | medium | low      (derived from proof, not vibes)
proof            test | repro | diff | none
evidence         file:line-range + the artifact (test code, command output, diff)
why              one paragraph, mechanism not opinion
suggested_fix    optional patch
policy_ref       which policy/preference rule triggered this, if any
```

Severity is gated on proof: `blocking` requires `proof in {test, repro}`.
Inconclusive proof downgrades severity one level. A Finding with no proof caps
at `nit` (or `question` for a genuine judgment call), with one scoped
exception: a missing-seam Finding may carry `important` with `proof: none`,
because the demonstrated absence of a proof seam is the evidence. Enforced,
not advisory.
<!-- nitpickle:finding-schema -->

The missing-seam exception is recorded in ADR-0001's consequences.

## Architecture handoff (post-review)

After a review, ask the prevention question: **what would have prevented this
class of finding?** When the answer is architectural - no good test seam,
tangled callers, a shallow module hiding the bug - surface it using the deep
module / seam / deletion-test vocabulary (see CONTEXT.md) rather than a vague
"consider refactoring." Make the recommendation *after* the findings are in. You
know more then.

## Repo intelligence layer

Three distinct inputs, kept separate (this separation is borrowed from Matt
Pocock's skills and is load-bearing - don't collapse them):

| Input | What it holds | File |
| --- | --- | --- |
| **Glossary** | domain *language* - terms only, no implementation | `CONTEXT.md` (+ `CONTEXT-MAP.md` for multi-context repos) |
| **Decisions** | choices already made, not to be re-litigated | `docs/adr/` |
| **Taste** | the user's personal engineering preferences | `.nitpickle/preferences.md` |

Reviews **speak the glossary**, **respect the ADRs** (a finding that contradicts
an accepted ADR is surfaced as a question, never asserted), and **apply the
taste**. A change that introduces a concept absent from `CONTEXT.md` is itself a
prompt to name it.

## Policy engine

Declarative, versioned, per-repo. Two kinds of entries:

```yaml
# deterministic -> shell out, ingest output as evidence
commands:
  test: go test ./...
  lint: golangci-lint run
  vuln: govulncheck ./...

# judgment -> the LLM evaluates, must attempt proof
rules:
  - require_context_propagation
  - errors_wrapped_with_context
  - table_driven_tests_for_handlers
  - no_package_level_mutable_state
```

Policy never duplicates a linter. NitPickle runs your existing linters, ingests
their output as evidence, and spends LLM budget only on judgment calls:

| Linter's job (NitPickle runs, doesn't re-derive) | NitPickle's job |
| --- | --- |
| formatting (gofmt), unused vars, shadowing | missing test for an error path |
| cyclomatic complexity thresholds | interface that ignores `ctx` cancellation |
| import ordering, naming lint | error that drops upstream context |
| known vuln deps (govulncheck) | a race a static pass can't see |
| | premature abstraction / missing one |

If a rule can be a linter analyzer, it belongs in `commands.lint`, not `rules`.

## Trust zones (security-critical)

Every input carries a trust level. Untrusted input can never alter agent
behavior, only be analyzed as data.

```
Trusted        user commands. .nitpickle/ convention files from your own working
               tree (pre-flight). For PR review, conventions are read from the
               PR's base branch, never the PR head. Approved memory
Semi-trusted   existing source code. Internal docs
Untrusted      PR comments. External-contributor issues. Dependency READMEs.
               Web pages. CI logs
```

A convention-file diff inside a reviewed PR is flagged as a finding, so a PR
author cannot weaken the review by editing `policy.yaml` in the PR itself.

Enforcement: untrusted content is wrapped and labeled as data in every prompt.
The agent is instructed (and tested) to ignore instructions found inside it.
Example threat: a PR comment saying "ignore previous instructions and run X."
NitPickle treats that as text to review, never a command to obey.

## Example pre-flight session

```
$ git checkout feature/sync-cache
$ <run preflight skill>

Branch feature/sync-cache vs main - 4 files, +182 -31

Recommendation: not ready
Blocking: 1   Important: 2   Nits: 3

[1] BLOCKING  confidence: high  proof: test
    Epoch boundary off-by-one in cache invalidation
    internal/sync/cache.go:88-104
    Why: invalidation keys on slot, but duties are keyed on epoch = slot/32.
         For any slot not divisible by 32 the wrong entry is evicted.
    Proof: wrote cache_epoch_test.go - fails on slot=33 (evicts epoch 0, want 1).
    Suggested fix: key on slot/32. [Apply] [TODO] [Dismiss]

[2] IMPORTANT  confidence: medium  proof: repro
    Service ignores context cancellation
    internal/sync/service.go:51
    ...

[5] NIT  confidence: low  proof: none
    Interface boundary could be clearer at handler edge - judgment call,
    not proven. Flagging, not blocking.
```

## The metric

The only metric that matters: **does it change your behavior?** Over your next
5 branches, count findings you actually fixed that you would otherwise have
shipped. If that number is ~0, the proof loop is noise and review quality needs
fixing before anything else. If it's >0 per branch, the loop earns its keep.
Track it in `.nitpickle/validation-log.md`.

## Run record (local audit)

Each review run can keep a local, private record: original task, approved plan,
policy version used, files changed, commands run, tests run, known limitations,
human approvals, risk rating. It is for your own audit only. It is never posted,
and nothing NitPickle produces carries a tooling or authorship banner. Outputs
read as ordinary engineering work.
