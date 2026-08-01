# Contributing

Contributions are welcome. A few house rules keep the project coherent.

- **Develop against a local clone.** On Claude Code, `/plugin marketplace add
  /path/to/nitpickle` then `/plugin install nitpickle@nitpickle`. On Codex,
  `codex plugin marketplace add /path/to/nitpickle` then `codex plugin add
  nitpickle@nitpickle`. Dogfood it: run `preflight` on your branch before opening
  a PR.
- **House writing style is enforced.** No em dashes and no semicolons in prose or
  comments (a `PreToolUse` hook blocks edits that add them). Keep comments short,
  WHAT not HOW, no package comments unless asked.
- **Commits use Conventional Commits** with a `resolves <issue_id>` and a
  `Signed-off-by: First Last (email)` footer. No AI or tooling attribution. See
  [.nitpickle/preferences.md](.nitpickle/preferences.md).
- **Every release bumps the version** across the Claude and Codex plugin manifests
  (`make bump VERSION=x.y.z` keeps them in sync) and adds a
  [CHANGELOG.md](CHANGELOG.md) entry. The validator fails CI when the manifests
  disagree.
- **Know the layout.** Each harness has its own skill tree,
  `skills/claude-code/<name>/SKILL.md` and `skills/codex/<name>/SKILL.md` (plus
  optional reference files), edited as a pair. The shared hooks live in `hooks/`.
  Global config defaults live in `defaults/`. Keep the four conventions separate:
  glossary (`CONTEXT.md`), decisions (`docs/adr/`), policy, and taste.

## Development

```sh
make test    # hook test suite (stdlib unittest)
make lint    # repo consistency validator (tools/validate.py)
make check   # both
make bump VERSION=x.y.z
```

CI runs `make test` and `make lint` on every push and PR, with PyYAML installed
for strict frontmatter parsing (local runs without it degrade to regex checks).
The validator also keeps the shared blocks (trust zones, Finding schema)
byte-identical across both skill trees and their canonical homes, and keeps the
harness-specific resolution block consistent within each tree.
