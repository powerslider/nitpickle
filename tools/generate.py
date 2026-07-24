#!/usr/bin/env python3
"""Generate the Codex layout from the canonical Claude Code source.

NitPickle is authored once under skills/. This renders the Codex install:
.agents/skills/<name>/ with cross-references rewritten from the Claude
`/nitpickle:x` namespace to Codex `$x` invocation syntax. Artifacts are not
committed, they generate to a temp tree for tests and to the install target.

Usage: python3 tools/generate.py [dst_dir]
"""
import json
import os
import re
import shutil
import sys

HOOK_SCRIPTS = ("no-agent-writes.py", "no-emdash-semicolon.py")

# Records the skills a generation installed into a destination, so a re-install
# can prune the ones no longer shipped without touching a user's own skills that
# share the flat ~/.agents/skills directory. Lives in the destination, never the
# repo source.
MANIFEST = ".nitpickle-manifest"

# Claude cross-reference token. The Codex form is `$name`, its invocation syntax.
REF = re.compile(r"/nitpickle:([a-z0-9-]+)")


def to_codex_ref(text):
    """Rewrite every /nitpickle:x cross-reference to the Codex `$x` form."""
    return REF.sub(r"$\1", text)


def skill_names(root):
    skills_dir = os.path.join(root, "skills")
    return sorted(
        d for d in os.listdir(skills_dir)
        if os.path.isfile(os.path.join(skills_dir, d, "SKILL.md"))
    )


def _read_manifest(dst):
    """The skill names a prior generation recorded in `dst`, or [] if none."""
    try:
        with open(os.path.join(dst, MANIFEST), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def render_skill_tree(root, dst):
    """Copy every canonical skill into `dst`, rewriting markdown cross-references
    to Codex `$name`. No manifest, no prune, so it is safe for a committed
    distribution tree as well as an install. Returns the skill names rendered."""
    skills_dir = os.path.join(root, "skills")
    names = skill_names(root)
    os.makedirs(dst, exist_ok=True)
    for name in names:
        src_dir = os.path.join(skills_dir, name)
        out_dir = os.path.join(dst, name)
        os.makedirs(out_dir, exist_ok=True)
        for entry in sorted(os.listdir(src_dir)):
            src = os.path.join(src_dir, entry)
            if not os.path.isfile(src):
                continue
            with open(src, encoding="utf-8") as f:
                content = f.read()
            if entry.endswith(".md"):
                content = to_codex_ref(content)
            with open(os.path.join(out_dir, entry), "w", encoding="utf-8") as f:
                f.write(content)
    return names


def generate_skills(root, dst):
    """Render every canonical skill into `dst`, then prune skills a prior
    generation installed here that are no longer shipped, scoped to the manifest so
    a user's own skills in the same directory are untouched. The manifest is
    install-time pruning state, so this is the install path, not the committed
    distribution one. Returns the names rendered."""
    names = render_skill_tree(root, dst)
    for stale in set(_read_manifest(dst)) - set(names):
        stale_dir = os.path.join(dst, stale)
        if os.path.isdir(stale_dir):
            shutil.rmtree(stale_dir)
    with open(os.path.join(dst, MANIFEST), "w", encoding="utf-8") as f:
        json.dump(names, f, indent=2)
        f.write("\n")
    return names


# The Codex hook wiring. Codex matches on the tool name (a regex) and fires the
# whole Bash call with no per-family `if`, so the guardrail runs with no family
# argument (self-dispatch). Codex edits are the apply_patch tool. There is no
# ${CLAUDE_PLUGIN_ROOT}, so command paths are absolute to the installed hooks.
def codex_hooks_config(hooks_dir):
    def command(script):
        return 'python3 "%s"' % os.path.join(hooks_dir, script)

    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "^Bash$",
                    "hooks": [{
                        "type": "command",
                        "command": command("no-agent-writes.py"),
                        "statusMessage": "Guardrail: write commands are the human's (ADR-0004)",
                    }],
                },
                {
                    "matcher": "^apply_patch$",
                    "hooks": [{
                        "type": "command",
                        "command": command("no-emdash-semicolon.py"),
                        "statusMessage": "Checking house style (no em dashes or semicolons)",
                    }],
                },
            ],
        },
    }


def _entry_is_ours(entry):
    """True if a PreToolUse entry runs one of our hook scripts, so a re-install
    replaces it rather than duplicating, and a user's own entries are left alone."""
    for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
        command = hook.get("command", "")
        if any(script in command for script in HOOK_SCRIPTS):
            return True
    return False


def generate_hooks_config(root, dst, hooks_dir=None):
    """Merge the Codex hooks config into any existing `dst/hooks.json`, pointing
    at `hooks_dir` (the installed hook scripts, absolute). The user's own hooks
    and other keys are preserved, our entries are replaced not duplicated on a
    re-run. Returns the written config dict."""
    if hooks_dir is None:
        hooks_dir = os.path.join(root, "hooks")
    os.makedirs(dst, exist_ok=True)
    ours = codex_hooks_config(os.path.abspath(hooks_dir))
    path = os.path.join(dst, "hooks.json")

    config = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, ValueError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    hooks = config.setdefault("hooks", {})
    existing = hooks.get("PreToolUse")
    kept = [e for e in existing if not _entry_is_ours(e)] if isinstance(existing, list) else []
    hooks["PreToolUse"] = kept + ours["hooks"]["PreToolUse"]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    return config


def install_hooks(root, home=None):
    """Install just the write guardrail. Copy the hook scripts to
    ~/.config/nitpickle/hooks and merge ~/.codex/hooks.json to point at them. This
    is the path a Codex plugin user takes, a plugin cannot carry hooks, so they run
    this from the plugin cache and then trust the hooks once via `/hooks`. Returns
    the hooks destination."""
    home = home or os.path.expanduser("~")
    hooks_dst = os.path.join(home, ".config", "nitpickle", "hooks")
    os.makedirs(hooks_dst, exist_ok=True)
    for script in HOOK_SCRIPTS:
        shutil.copy2(os.path.join(root, "hooks", script), os.path.join(hooks_dst, script))
    generate_hooks_config(root, os.path.join(home, ".codex"), hooks_dir=hooks_dst)
    return hooks_dst


def install_codex(root, home=None):
    """Install the full Codex layout into the user's home: skills under
    ~/.agents/skills, the guardrail hooks via install_hooks, and the global
    defaults seeded if absent. Returns the skills and hooks destinations."""
    home = home or os.path.expanduser("~")
    skills_dst = os.path.join(home, ".agents", "skills")
    generate_skills(root, skills_dst)
    hooks_dst = install_hooks(root, home)

    config_dst = os.path.join(home, ".config", "nitpickle")
    for default in ("policy.yaml", "preferences.md"):
        src = os.path.join(root, "defaults", "nitpickle", default)
        dst = os.path.join(config_dst, default)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
    return skills_dst, hooks_dst


# The Codex marketplace distribution bundle, committed under .agents/plugins/. This
# is the one committed generated artifact (ADR-0010), so a remote `codex plugin add`
# can read it from a git commit. Its skills carry `$name` refs. The guardrail is not
# in the bundle, Codex does not run plugin-bundled hooks. The validator drift check
# holds it to the canonical source.
PLUGIN_NAME = "nitpickle"
PLUGIN_CATEGORY = "Development"


def _claude_manifest(root):
    """The Claude plugin manifest, the single source of version and description."""
    with open(os.path.join(root, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        return json.load(f)


def _ensure_parent(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def _write_json(path, data):
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def codex_plugin_manifest(meta):
    """The `.codex-plugin/plugin.json`. Version and description derive from the
    Claude manifest so the two never diverge."""
    return {
        "name": PLUGIN_NAME,
        "version": meta["version"],
        "description": meta["description"],
        "author": meta.get("author", {}),
        "repository": meta.get("repository", ""),
        "license": meta.get("license", ""),
        "keywords": meta.get("keywords", []),
        "skills": "./skills/",
        "interface": {
            "displayName": meta.get("displayName", "NitPickle"),
            "category": PLUGIN_CATEGORY,
            "shortDescription": "Proof-driven engineering skills.",
            "longDescription": (
                "Proof-driven engineering skills for Codex. The write guardrail is "
                "not part of the plugin, Codex does not run plugin-bundled hooks. To "
                "enable it, run `python3 tools/generate.py --install-hooks` from this "
                "plugin's cache directory, then trust the hooks with /hooks."
            ),
        },
    }


def codex_marketplace_manifest():
    """The `.agents/plugins/marketplace.json`. Codex resolves a plugin `source.path`
    relative to the marketplace root, which is the repo root, not the directory
    holding marketplace.json, so the path is repo-root-relative to the bundle."""
    return {
        "name": PLUGIN_NAME,
        "interface": {"displayName": "NitPickle"},
        "plugins": [{
            "name": PLUGIN_NAME,
            "source": {"source": "local", "path": "./.agents/plugins/%s" % PLUGIN_NAME},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
            "category": PLUGIN_CATEGORY,
        }],
    }


def emit_codex_marketplace(root, dst_root):
    """Emit the committed Codex marketplace bundle under `dst_root/.agents/plugins`,
    the marketplace manifest plus a `nitpickle` plugin. The plugin directory is
    cleared and rebuilt so the output is an exact mirror of the canonical source. It
    carries the `$name`-rewritten skills, its `.codex-plugin` manifest, and the
    installer plus hook scripts, since a plugin user runs
    `generate.py --install-hooks` from the plugin cache and Codex ships every file
    in the plugin dir. The guardrail is not a plugin hook, this is how a plugin-only
    user wires it up. `dst_root` is the repo root for the committed tree, or a temp
    root for the drift check. Returns the `.agents/plugins` directory."""
    meta = _claude_manifest(root)
    plugins_dir = os.path.join(dst_root, ".agents", "plugins")
    plugin_dir = os.path.join(plugins_dir, PLUGIN_NAME)
    if os.path.isdir(plugin_dir):
        shutil.rmtree(plugin_dir)
    render_skill_tree(root, os.path.join(plugin_dir, "skills"))
    _write_json(os.path.join(plugin_dir, ".codex-plugin", "plugin.json"), codex_plugin_manifest(meta))
    shutil.copy2(
        os.path.join(root, "tools", "generate.py"),
        _ensure_parent(os.path.join(plugin_dir, "tools", "generate.py")),
    )
    for script in HOOK_SCRIPTS:
        shutil.copy2(
            os.path.join(root, "hooks", script),
            _ensure_parent(os.path.join(plugin_dir, "hooks", script)),
        )
    _write_json(os.path.join(plugins_dir, "marketplace.json"), codex_marketplace_manifest())
    return plugins_dir


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args = sys.argv[1:]
    if args and args[0] == "--install":
        home = args[1] if len(args) > 1 else None
        skills_dst, hooks_dst = install_codex(root, home)
        print("installed codex skills to %s, hooks to %s" % (skills_dst, hooks_dst))
        return
    if args and args[0] == "--codex-dist":
        plugins = emit_codex_marketplace(root, root)
        print("regenerated codex marketplace bundle at %s" % plugins)
        return
    if args and args[0] == "--install-hooks":
        home = args[1] if len(args) > 1 else None
        hooks_dst = install_hooks(root, home)
        print("installed guardrail hooks to %s, trust them once with /hooks" % hooks_dst)
        return
    dst = args[0] if args else os.path.join(root, ".agents", "skills")
    names = generate_skills(root, dst)
    print("generated %d codex skills to %s" % (len(names), dst))


if __name__ == "__main__":
    main()
