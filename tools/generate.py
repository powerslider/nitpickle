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


def generate_skills(root, dst):
    """Render every canonical skill into `dst`, copying bundled files and
    rewriting cross-references in markdown. Returns the skill names rendered."""
    skills_dir = os.path.join(root, "skills")
    names = skill_names(root)
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
                    "matcher": "^(apply_patch|Write|Edit|MultiEdit)$",
                    "hooks": [{
                        "type": "command",
                        "command": command("no-emdash-semicolon.py"),
                        "statusMessage": "Checking house style (no em dashes or semicolons)",
                    }],
                },
            ],
        },
    }


def generate_hooks_config(root, dst, hooks_dir=None):
    """Write the Codex hooks.json into `dst`, pointing at `hooks_dir` (the
    installed hook scripts, absolute). Returns the config dict."""
    if hooks_dir is None:
        hooks_dir = os.path.join(root, "hooks")
    os.makedirs(dst, exist_ok=True)
    config = codex_hooks_config(os.path.abspath(hooks_dir))
    with open(os.path.join(dst, "hooks.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    return config


def install_codex(root, home=None):
    """Install the Codex layout into the user's home: skills under
    ~/.agents/skills, the hook scripts under ~/.config/nitpickle/hooks with a
    ~/.codex/hooks.json pointing at them, and the global defaults seeded if
    absent. Returns the skills and hooks destinations."""
    home = home or os.path.expanduser("~")
    skills_dst = os.path.join(home, ".agents", "skills")
    generate_skills(root, skills_dst)

    hooks_dst = os.path.join(home, ".config", "nitpickle", "hooks")
    os.makedirs(hooks_dst, exist_ok=True)
    for script in HOOK_SCRIPTS:
        shutil.copy2(os.path.join(root, "hooks", script), os.path.join(hooks_dst, script))
    generate_hooks_config(root, os.path.join(home, ".codex"), hooks_dir=hooks_dst)

    config_dst = os.path.join(home, ".config", "nitpickle")
    for default in ("policy.yaml", "preferences.md"):
        src = os.path.join(root, "defaults", "nitpickle", default)
        dst = os.path.join(config_dst, default)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
    return skills_dst, hooks_dst


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args = sys.argv[1:]
    if args and args[0] == "--install":
        home = args[1] if len(args) > 1 else None
        skills_dst, hooks_dst = install_codex(root, home)
        print("installed codex skills to %s, hooks to %s" % (skills_dst, hooks_dst))
        return
    dst = args[0] if args else os.path.join(root, ".agents", "skills")
    names = generate_skills(root, dst)
    print("generated %d codex skills to %s" % (len(names), dst))


if __name__ == "__main__":
    main()
