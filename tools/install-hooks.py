#!/usr/bin/env python3
"""Install the NitPickle write guardrail for Codex.

A Codex plugin cannot carry hooks (Codex does not run plugin-bundled hooks), so a
plugin user runs this from the plugin directory. It copies the two hook scripts to
a stable location and merges ~/.codex/hooks.json to point at them, preserving the
user's own hooks. Then trust the hooks once with /hooks.

Usage: python3 tools/install-hooks.py [home]
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed_defaults import seed_defaults

HOOK_SCRIPTS = ("no-agent-writes.py", "no-emdash-semicolon.py")


def codex_hooks_config(hooks_dir):
    """The two PreToolUse entries wiring Codex to the guardrail scripts. Codex
    matches on the tool name and fires the whole Bash call with no per-family `if`,
    so the write guardrail self-dispatches. Edits are the apply_patch tool."""
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
    replaces it rather than duplicating and a user's own entries are left alone."""
    for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
        if any(script in hook.get("command", "") for script in HOOK_SCRIPTS):
            return True
    return False


def merge_hooks_config(dst_dir, hooks_dir):
    """Merge our PreToolUse entries into any existing `dst_dir/hooks.json`, pointing
    at the absolute `hooks_dir`. The user's own hooks and other keys are preserved,
    our entries replaced not duplicated on a re-run."""
    os.makedirs(dst_dir, exist_ok=True)
    ours = codex_hooks_config(os.path.abspath(hooks_dir))
    path = os.path.join(dst_dir, "hooks.json")

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
    """Copy the hook scripts to ~/.config/nitpickle/hooks and wire ~/.codex/hooks.json
    to them. `root` is the plugin or repo root that holds `hooks/`. Returns the
    hooks destination."""
    home = home or os.path.expanduser("~")
    hooks_dst = os.path.join(home, ".config", "nitpickle", "hooks")
    os.makedirs(hooks_dst, exist_ok=True)
    for script in HOOK_SCRIPTS:
        shutil.copy2(os.path.join(root, "hooks", script), os.path.join(hooks_dst, script))
    merge_hooks_config(os.path.join(home, ".codex"), hooks_dst)
    return hooks_dst


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    home = sys.argv[1] if len(sys.argv) > 1 else None
    hooks_dst = install_hooks(root, home)
    print("installed guardrail hooks to %s, trust them once with /hooks" % hooks_dst)

    dst_dir, seeded, skipped = seed_defaults(root, "codex", home)
    print("seeded %d default file(s) to %s" % (len(seeded), dst_dir))
    if skipped:
        print("  skipped (already present, use seed_defaults.py --force to overwrite): %s"
              % ", ".join(skipped))


if __name__ == "__main__":
    main()
