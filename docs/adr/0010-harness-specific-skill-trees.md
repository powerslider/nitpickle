# ADR-0010: harness-specific skill trees with a native marketplace per harness

## Status

Accepted

## Context

NitPickle targets both Claude Code and Codex. The two harnesses share the proof
discipline and almost all skill prose, but they diverge in invocation syntax
(`/nitpickle:<name>` on Claude Code, `$<name>` on Codex), in their convention file
(`CLAUDE.md` versus `AGENTS.md`), and in native packaging. A `codex plugin add`
installs from committed git files, with no build step in the install path.

An earlier version of this decision kept one canonical source and generated the
Codex layout on demand, rewriting references. That forced a bad trade for
distribution: a remote `codex plugin add` cannot run a generator, so the rewritten
skills had to be either committed as a generated duplicate (vendoring, with a drift
check and a regenerate on every skill edit) or absent (shipping the wrong sigil).
The generation machinery cost more than the second edit it saved.

## Decision

Author skills per harness. `skills/claude-code/` and `skills/codex/` are each a
full skill tree, hand-optimized for its harness, and both are source, not
generated. `hooks/` and `docs/` are shared. One repo ships a native marketplace
for each harness:

- Claude Code: `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json`,
  the plugin `skills` field points at `./skills/claude-code`.
- Codex: `.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json`, the
  `skills` field points at `./skills/codex`.

No generation, no reference rewrite, no drift check. Installing is native on both,
`/plugin install nitpickle@nitpickle` and `codex plugin add nitpickle@nitpickle`.
The write guardrail cannot ride in the Codex plugin (Codex does not run
plugin-bundled hooks), so a Codex plugin user runs `tools/install-hooks.py` and
trusts the hooks once with `/hooks`.

The validator enforces two-tree consistency: the skill sets match across harnesses,
a claude-code reference resolves and a codex skill carries no `/nitpickle:` token,
and the shared convention blocks (resolution, trust, finding-schema) stay
byte-synced in both trees.

## Consequences

- Both harnesses install natively with no generated artifact in the repo.
- The two trees are hand-maintained. Adding or editing a skill means editing both.
  This is the accepted cost, taken deliberately for clean native installs and
  maximal per-harness optimization. The validator catches a tree that drifts out of
  parity.
- The guardrail is a separate install-and-trust step on Codex, `tools/install-hooks.py`
  then `/hooks`. `make install-hooks` is the local convenience.
- Shared convention blocks are still single-sourced in `.nitpickle/README.md` and
  `docs/ARCHITECTURE.md` and byte-synced into both trees.

## Alternatives considered

- **One canonical source plus per-harness generation.** The prior form of this
  ADR. Rejected. A remote `codex plugin add` cannot generate, so it forced a
  committed generated skill duplicate (a drift check plus a regenerate on every
  edit) or shipping the wrong invocation sigil. The tooling and the vendored
  duplicate outweighed the one saved edit.
- **One shared skill tree for both marketplaces (the wshobson pattern).** Rejected.
  The invocation sigil and some idiom differ per harness, so a shared tree ships the
  wrong sigil and cross-harness noise to each reader.
- **Ship the guardrail inside the Codex plugin.** Not possible, Codex does not run
  plugin-bundled hooks. Revisit if that changes upstream.
