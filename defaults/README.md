# defaults/nitpickle - global default config

The default `.nitpickle` config that applies to any repo with no local
`.nitpickle/`. Install it once to the global location and every repo inherits it.

From a clone of this repo:

```sh
mkdir -p ~/.claude/nitpickle
cp defaults/nitpickle/policy.yaml      ~/.claude/nitpickle/policy.yaml
cp defaults/nitpickle/preferences.md   ~/.claude/nitpickle/preferences.md
```

When NitPickle is installed as a plugin, these same files ship inside the plugin
at `${CLAUDE_PLUGIN_ROOT}/defaults/nitpickle/`. Copy them to `~/.claude/nitpickle/`
the same way.

## Resolution (how skills pick config)

Effective config = global defaults overlaid by repo-local.

- **policy.yaml** and **preferences.md**: the repo-local `.nitpickle/<file>`
  overrides the global `~/.claude/nitpickle/<file>` per top-level key. The `rules`
  list is the union of global and local. A repo with no local `.nitpickle/` at all
  uses the global defaults unchanged.
- **CONTEXT.md**, **docs/adr/**, and **validation-log.md** are always per-repo.
  There is no global version. A repo without them simply has no glossary,
  decisions, or log yet.

## What is global vs local

- **Global** holds cross-project taste and universal judgment rules. It is
  language-agnostic.
- **Local** holds the toolchain commands (test, lint), generated-file globs, and
  language-specific or repo-specific rules.

Keep language-specific commands and rules out of the global default. They belong
in each repo's local `.nitpickle/policy.yaml`.
