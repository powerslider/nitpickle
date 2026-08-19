# defaults/nitpickle - global default config

The default `.nitpickle` config that applies to any repo with no local
`.nitpickle/`. Install it once to the global location and every repo inherits it.
The directory holds `policy.yaml`, `preferences.md`, and `principles.md`.

From a clone of this repo, seed all of them at once:

```sh
make seed-defaults              # Claude Code (~/.claude/nitpickle/)
make seed-defaults HARNESS=codex   # Codex (~/.config/nitpickle/)
```

The seeder globs the whole directory, so every default (including any added
later) is installed. It never overwrites a file you have customized, pass
`FORCE=1` to refresh.

When NitPickle is installed as a plugin, these same files ship inside the plugin
at `${CLAUDE_PLUGIN_ROOT}/defaults/nitpickle/`. Seed them with
`python3 ${CLAUDE_PLUGIN_ROOT}/tools/seed_defaults.py --harness claude` (or
`--harness codex`). On Codex, `tools/install-hooks.py` seeds them for you.

## Resolution (how skills pick config)

Effective config = global defaults overlaid by repo-local.

- **policy.yaml**, **preferences.md**, and **principles.md**: the repo-local
  `.nitpickle/<file>` overrides the global `~/.claude/nitpickle/<file>` per
  top-level key. The `rules` list is the union of global and local. A repo with no
  local `.nitpickle/` at all uses the global defaults unchanged.
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
