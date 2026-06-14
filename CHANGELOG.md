# Changelog

One entry per released version. Bump the version in both
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for every
release (`make bump VERSION=x.y.z`), and add the entry here.

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
