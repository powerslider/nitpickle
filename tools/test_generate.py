"""Tests for the Codex generator. Stdlib only, run with:

    python3 -m unittest discover -s tools -p "test_*.py"

The golden cases are hand-authored, not snapshots of the generator output, so a
rewrite bug is caught rather than baked in.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestRefRewrite(unittest.TestCase):
    def test_single_ref(self):
        self.assertEqual(generate.to_codex_ref("/nitpickle:grill"), "$grill")

    def test_hyphenated_ref(self):
        self.assertEqual(generate.to_codex_ref("/nitpickle:review-pr"), "$review-pr")

    def test_golden_sentence(self):
        canonical = (
            "Run `/nitpickle:grill` on this, then implement, then "
            "`/nitpickle:preflight`. Promote via `/nitpickle:test-spec`."
        )
        expected = (
            "Run `$grill` on this, then implement, then "
            "`$preflight`. Promote via `$test-spec`."
        )
        self.assertEqual(generate.to_codex_ref(canonical), expected)

    def test_no_namespace_remains(self):
        out = generate.to_codex_ref("see /nitpickle:audit and /nitpickle:polish")
        self.assertNotIn("/nitpickle:", out)

    def test_non_ref_dollar_untouched(self):
        # Shell placeholders in code examples must not be disturbed.
        self.assertEqual(generate.to_codex_ref("echo $1 $ARGUMENTS"), "echo $1 $ARGUMENTS")


class TestGenerateLayout(unittest.TestCase):
    def test_generates_every_skill_clean(self):
        with tempfile.TemporaryDirectory() as dst:
            names = generate.generate_skills(ROOT, dst)
            self.assertEqual(names, generate.skill_names(ROOT))
            for name in names:
                skill = os.path.join(dst, name, "SKILL.md")
                self.assertTrue(os.path.isfile(skill), name)
                with open(skill, encoding="utf-8") as f:
                    body = f.read()
                self.assertNotIn("/nitpickle:", body)
                self.assertTrue(body.startswith("---"), name)


class TestManifestPrune(unittest.TestCase):
    def test_prunes_our_stale_skill_keeps_users_own(self):
        with tempfile.TemporaryDirectory() as dst:
            generate.generate_skills(ROOT, dst)
            # A skill a prior version shipped, recorded in our manifest.
            ghost = os.path.join(dst, "ghost-skill")
            os.makedirs(ghost)
            open(os.path.join(ghost, "SKILL.md"), "w").close()
            manifest = os.path.join(dst, generate.MANIFEST)
            with open(manifest, encoding="utf-8") as f:
                names = json.load(f)
            with open(manifest, "w", encoding="utf-8") as f:
                json.dump(names + ["ghost-skill"], f)
            # A skill the user authored themselves, not in our manifest.
            mine = os.path.join(dst, "user-own")
            os.makedirs(mine)
            open(os.path.join(mine, "SKILL.md"), "w").close()

            generate.generate_skills(ROOT, dst)  # reinstall

            self.assertFalse(os.path.isdir(ghost), "our stale skill must be pruned")
            self.assertTrue(os.path.isdir(mine), "the user's own skill must survive")
            self.assertTrue(os.path.isdir(os.path.join(dst, "audit")))


class TestInstallCodex(unittest.TestCase):
    def test_install_lays_down_full_layout(self):
        with tempfile.TemporaryDirectory() as home:
            skills_dst, hooks_dst = generate.install_codex(ROOT, home)
            # Every skill is present under ~/.agents/skills.
            for name in generate.skill_names(ROOT):
                self.assertTrue(os.path.isfile(os.path.join(skills_dst, name, "SKILL.md")))
            # Hook scripts were copied and the config points at them.
            for script in generate.HOOK_SCRIPTS:
                self.assertTrue(os.path.isfile(os.path.join(hooks_dst, script)))
            with open(os.path.join(home, ".codex", "hooks.json"), encoding="utf-8") as f:
                cfg = json.load(f)
            cmd = cfg["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
            self.assertIn(hooks_dst, cmd)
            # Global defaults seeded.
            self.assertTrue(os.path.isfile(os.path.join(home, ".config", "nitpickle", "policy.yaml")))

    def test_install_preserves_existing_codex_hooks(self):
        with tempfile.TemporaryDirectory() as home:
            codex = os.path.join(home, ".codex")
            os.makedirs(codex)
            user_cfg = {
                "hooks": {"PreToolUse": [
                    {"matcher": "^Bash$", "hooks": [{"type": "command", "command": "my-own-hook.sh"}]},
                ]},
                "otherUserSetting": True,
            }
            with open(os.path.join(codex, "hooks.json"), "w", encoding="utf-8") as f:
                json.dump(user_cfg, f)

            generate.install_codex(ROOT, home)
            generate.install_codex(ROOT, home)  # re-run: must stay idempotent

            with open(os.path.join(codex, "hooks.json"), encoding="utf-8") as f:
                merged = json.load(f)
            text = json.dumps(merged)
            # User content survives.
            self.assertTrue(merged.get("otherUserSetting"))
            self.assertIn("my-own-hook.sh", text)
            # Our entries are present exactly once after two installs.
            ours = [e for e in merged["hooks"]["PreToolUse"] if generate._entry_is_ours(e)]
            self.assertEqual(len(ours), 2)


class TestCodexHooksConfig(unittest.TestCase):
    def setUp(self):
        self.cfg = generate.codex_hooks_config("/opt/nitpickle/hooks")

    def test_pretooluse_present(self):
        self.assertIn("PreToolUse", self.cfg["hooks"])

    def test_bash_matcher_targets_guardrail(self):
        bash = [e for e in self.cfg["hooks"]["PreToolUse"] if e["matcher"] == "^Bash$"]
        self.assertEqual(len(bash), 1)
        cmd = bash[0]["hooks"][0]["command"]
        self.assertIn("no-agent-writes.py", cmd)
        # Self-dispatch: no family argument is passed on the Codex side.
        self.assertTrue(cmd.rstrip().endswith('no-agent-writes.py"'))

    def test_edit_matcher_targets_style_hook(self):
        edit = [e for e in self.cfg["hooks"]["PreToolUse"]
                if "apply_patch" in e["matcher"]]
        self.assertEqual(len(edit), 1)
        self.assertIn("no-emdash-semicolon.py", edit[0]["hooks"][0]["command"])

    def test_no_plugin_root_variable(self):
        text = json.dumps(self.cfg)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", text)

    def test_written_config_is_valid_json_referencing_real_scripts(self):
        with tempfile.TemporaryDirectory() as dst:
            generate.generate_hooks_config(ROOT, dst)
            with open(os.path.join(dst, "hooks.json"), encoding="utf-8") as f:
                cfg = json.load(f)
            for entry in cfg["hooks"]["PreToolUse"]:
                cmd = entry["hooks"][0]["command"]
                script = cmd.split('"')[1]
                self.assertTrue(os.path.isfile(script), script)


if __name__ == "__main__":
    unittest.main()
