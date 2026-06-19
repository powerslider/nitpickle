# Changelog

One entry per released version. Bump the version in both
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for every
release (`make bump VERSION=x.y.z`), and add the entry here.

## 0.7.0

- New `audit` skill: a holistic comprehend-and-improve pass for an existing, often
  unfamiliar, complex feature, `review-pr`'s inward sibling. It reconstructs the design
  of code you may not have written, ratifies intent with you, finds Proof-complete
  defects with the proof engine and an adversarial skeptic, and synthesizes a
  root-cause-ordered remediation roadmap. It applies nothing and writes a
  `docs/audits/<slug>.md` artifact.
- Correctness is bounded honestly (ADR-0008). A Proof-complete defect is provable from
  the code alone and is asserted, an intent-dependent concern is routed to a
  characterization task so the human ratifies a demonstration, never an artifact-free
  suspicion. The roadmap routes the quality, test, and design-spec work to the siblings
  and runs none of them live.
- Glossary gains Proof-complete defect. `docs/audits/` joins `docs/reviews/` as a local,
  gitignored, house-style-exempt artifact directory.

## 0.6.0

- New `test-spec` skill: proof-driven test authorship, the third proof-engine sibling
  alongside `preflight` and `polish`. It writes a failing spec test-first and
  characterizes or strengthens tests for existing code. The deliverable is a Kept test,
  it authors tests only and never production logic, so test-first it stops at red and
  hands green to the human.
- A Kept test is gated on a tiered Fail-demonstration, not coverage (ADR-0006). A killed
  mutant or removed line proves the assertions discriminate, absent-code red proves only
  non-vacuity. Correctness of pinned behavior stays a human Test oracle call, since a
  program cannot be its own oracle.
- It closes the missing-seam loop with `preflight` and `polish`, and turns a proven bug
  into a Kept regression test. Glossary gains Test oracle, Characterization test,
  Fail-demonstration, and Kept test.

## 0.5.0

- New `polish` skill: a convention-aware code-quality pass, the inverse of
  `preflight`. It refactors a target toward the repo's idioms and taste (glossary,
  preferences, ADRs, policy) that generic tools cannot see, proposes each change as
  a Refinement, and applies it only on per-change approval, never in bulk. Quality
  only, it does not hunt bugs.
- The preservation proof is tiered (ADR-0005): the policy commands when they cover
  the touched code, else a synthesized throwaway characterization test, else the
  Refinement is downgraded and the missing seam flagged. A green proof shows the
  change is safe, not better, so polish stays human-gated and never commits.
- Glossary gains **Refinement**, Run record broadened to cover transform runs.
  ADR-0005 records that polish proves preservation, not betterment, the ADR-0003
  parallel for quality transforms.

## 0.4.0

- New default-on write-command guardrail (`no-agent-writes.py`, ADR-0004). A
  PreToolUse hook denies the writes that land or go outward (git commit, push,
  reset `--hard`, merge/rebase/cherry-pick, and the destructive gh verbs), so
  the human-decides-what-lands posture is enforced, not just asserted. Read
  siblings and the skills' own worktree, checkout, and posting paths pass.
  `NITPICKLE_ALLOW_WRITES` overrides it and is not a self-grant vector. The
  matcher fires on a prefix, so an exact-subcommand check keeps `git merge-base`
  and friends allowed.
- The house-style hook now bans semicolons in code-comment prose, not only
  markdown, closing the gap behind the stated policy. Code examples stay exempt
  (fenced, inline, godoc-indented, `@example`), so Rust doctests pass. The
  em-dash ban stays global.

## 0.3.1

- `review-pr` adversarially verifies each proven-blocking finding before it
  enters the packet: a skeptic subagent tries to refute it (does the proof test
  the real defect or an artifact?), and a refuted finding is downgraded or
  dropped. Proof gates severity, this pass guards the proof, which matters more
  on someone else's PR where a wrong request-for-changes is costly. Mirrors
  feature-plan's critic.
- The review packet is now written to `docs/reviews/pr-<n>.md`, a local,
  gitignored, house-style-exempt file (it embeds proof evidence), in addition to
  being presented for interactive triage. The hook and validator exempt
  `docs/reviews/` the same way as `docs/handoffs/`.

## 0.3.0

- New `resolve-conflicts` skill: proof-driven resolution of merge, rebase, and
  cherry-pick conflicts. It detects the in-progress operation, reads each
  conflict's base, mine, and incoming sides from the index, and maps ours and
  theirs correctly (rebase swaps them, the usual source of wrong-side
  resolutions). Each conflict is classified trivial, semantic, or file-level.
- A provably-trivial hunk (a side-choice where the other side is a no-op, all
  three stages present) is auto-resolved by a deterministic check, written
  unstaged and logged. Union, append, adjacent edits, and every file-level
  conflict (add/add, modify/delete, both-deleted, rename) are never trivial and
  stay gated, so a deletion is never auto-taken.
- A semantic resolution is proposed with whole-file context, proved by running
  the policy commands, graded like a Finding, and applied only on per-hunk
  approval. A green proof does not prove both sides' intent survived, so semantic
  resolutions stay human-gated even when proven (ADR-0003). Binary and file-level
  conflicts get a pick-a-side choice, never synthesized content.
- All writes are unstaged and the skill never runs `--continue` or commits, so
  the human finishes the operation. Single-file undo via `git checkout -m`.
- Glossary gains **Conflict**. ADR-0003 records that proven resolutions stay
  human-gated.

## 0.2.0

- New `handoff` and `resume` skills, a pair for encapsulating the progress of
  an in-flight task so a different session or agent can finish it. `handoff`
  writes a standalone, ephemeral `docs/handoffs/<slug>.md` capturing what is
  done, in flight, blocked, the next step, dead-ends, and a git snapshot with
  the uncommitted diff embedded (untracked files included), linking a matching
  plan rather than copying it. Getting the artifact to the other session is the
  author's call. `resume` loads the artifact and verifies it against
  reality (git snapshot, applies the embedded diff and re-runs the policy
  commands, reconciles against the plan) before continuing, stopping to ask on
  real divergence and offering to delete the artifact when the task is done.
  See ADR-0002.
- House style no longer polices captured code we do not author or maintain. The
  hook and the validator exempt `docs/handoffs/` paths, so an embedded diff is
  neither blocked on write nor failed in CI.
- Glossary gains **Handoff**. The README skill-count check is now
  case-insensitive and allows an adjective, so every count site is validated.

## 0.1.5

- The repo is scoped to what it is, a Claude Code plugin of skills. One
  plugin-scoped `docs/ARCHITECTURE.md` replaces the brainstorm-era product
  docs (PRODUCT_SPEC, VISION, ROADMAP, ideation), and product vocabulary is
  swept from the README, glossary, conventions, and skills.
- The Finding schema's canonical home moves to `docs/ARCHITECTURE.md`.
- bootstrap's description no longer breaks strict YAML (unquoted colon-space),
  which made CI drop the skill and cascade reference and count failures. The
  validator's no-pyyaml fallback now catches this class locally.
- Retired-phrase checking removed from the validator. Canonical blocks are the
  real drift guard, exact-sentence tripwires only fight past battles.

## 0.1.4

- One canonical resolution rule and trust-zone statement across all skills,
  validator enforced. Trust split by surface: pre-flight trusts the working
  tree, PR review reads conventions from the base branch.
- Finding schema single-sourced with the missing-seam severity exception
  (ADR-0001).
- The plan handoff loop is closed: grill reads and approves `docs/plans/`
  documents in place, preflight checks the branch against its approved plan.
- Proof seam: hook test suite, repo consistency validator, CI, Makefile.
- Glossary: Proof engine, Proof surface, Diff budget, AFK, HITL added.
  Convergence aligned to two consecutive clean critic passes. Billing
  generalized to an example flow in design-spec.

## 0.1.3

- review-pr's description no longer truncates in the skill registry (unquoted
  hash in YAML frontmatter).
- README and manifests match the seven shipped skills. commit-msg integrated
  into the docs.
- Dangling references removed: repo-map.yaml, roadmap leaks, vocabulary cited
  from docs a skill cannot read at runtime. todo.md scaffolded and gitignored.

## 0.1.2

- commit-msg skill added.
- bootstrap gains glossary-drift refresh guidance and the domain-bearing test
  for candidate terms.
- validation-log.md and todo.md treated as per-developer working state.

## 0.1.1

- Fix duplicate hooks load (manifest.hooks pointed at the auto-loaded
  hooks.json).

## 0.1.0

- Initial release: bootstrap (as init), preflight, review-pr, grill,
  feature-plan, design-spec skills, house-style hook, convention layer.
