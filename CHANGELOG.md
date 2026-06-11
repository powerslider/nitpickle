# Changelog

One entry per released version. Bump the version in both
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for every
release (`make bump VERSION=x.y.z`), and add the entry here.

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
