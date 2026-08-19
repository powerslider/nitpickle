#!/usr/bin/env python3
"""NitPickle repo consistency validator.

Run from the repo root (or pass the root as the first argument):

    python3 tools/validate.py [root]

Skills are authored per harness under skills/claude-code and skills/codex, each a
full tree hand-optimized for its harness. Checks:
  1. Every skills/<harness>/*/SKILL.md has frontmatter whose name matches its dir.
  2. The parsed description matches its raw line, catching silent YAML comment
     truncation from an unquoted hash (valid YAML, invisible to a parse check).
  3. References resolve per harness: a claude-code /nitpickle:<name> resolves to a
     shipped skill, and a codex skill carries no /nitpickle: token and every
     $nitpickle:<name> resolves.
  4. No bare $<skillname> in any markdown, the Codex invocation is the namespaced
     $nitpickle:<name>, so a doc example cannot ship a token that fails to resolve.
  5. The README's written-out skill count matches the skills directory.
  6. The Claude and Codex plugin manifest versions all match.
  7. No banned characters in tracked files: literal em or en dash anywhere,
     semicolons and HTML-entity dashes in markdown prose (code stripped with
     the hook's own semantics, unmatched fences fail open with a warning).
  8. Trigger collision phrases appear in at most one skill description.
  9. Every load-bearing glossary term has a CONTEXT.md entry.
  10. Verbatim canonical blocks match their canonical home byte for byte, in both
     harness trees, so a shared block cannot drift in one tree.
  11. The resolution block, which is harness-specific, is identical across every
     skill within a tree, so it cannot drift within a tree.
  12. Every shipped skill has a description section in docs/skills.md.
  13. Every code-touching skill references .nitpickle/principles.md in both trees,
     so the engineering principles cannot be silently dropped from a skill's load
     section.

PyYAML sharpens check 1 and 2 when installed (it is a CI dependency, not a
runtime one). Without it the checks degrade to regex on the raw lines.
"""
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    yaml = None

HARNESSES = ("claude-code", "codex")

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)
DASH_ENTITIES = (
    "&mdash;",
    "&ndash;",
    "&#8212;",
    "&#8211;",
    "&#x2014;",
    "&#x2013;",
)
NUMBER_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
    13: "thirteen", 14: "fourteen",
}

# Skills that carry the shared resolution and trust blocks. Their marker-delimited
# content must match the canonical home byte for byte, in every harness tree.
FULL_BLOCK_SKILLS = (
    "bootstrap", "design-spec", "feature-plan", "grill", "handoff",
    "preflight", "polish", "resolve-conflicts", "resume", "review-pr",
    "test-spec", "audit", "ui-proof",
)
# The trust block is harness-neutral and byte-synced to a shared home. The
# resolution block is harness-specific (its config path differs), so it is checked
# tree-internally instead (check_resolution_blocks), not synced here.
CANONICAL_BLOCKS = []
for _h in HARNESSES:
    for _name in FULL_BLOCK_SKILLS:
        CANONICAL_BLOCKS.append(
            (f"skills/{_h}/{_name}/SKILL.md", ".nitpickle/README.md", "<!-- nitpickle:trust -->")
        )
    CANONICAL_BLOCKS += [
        (
            f"skills/{_h}/commit-msg/SKILL.md",
            f"skills/{_h}/commit-msg/SKILL.md",
            "<!-- nitpickle:conventions-commit-msg -->",
        ),
    ]
    # Blocks homed in ARCHITECTURE.md, as (skill-relative path, marker name).
    for _target, _marker in (
        ("preflight/SKILL.md", "finding-schema"),
        ("review-pr/REVIEW-FORMAT.md", "finding-schema"),
        ("ui-proof/SKILL.md", "finding-schema"),
        ("preflight/SKILL.md", "mutation"),
        ("review-pr/REVIEW-FORMAT.md", "mutation"),
    ):
        CANONICAL_BLOCKS.append((
            f"skills/{_h}/{_target}",
            "docs/ARCHITECTURE.md",
            f"<!-- nitpickle:{_marker} -->",
        ))

# Load-bearing vocabulary the skills use. Each must have a glossary entry in
# CONTEXT.md (a "- **Term**" bullet). Curated by hand.
LOAD_BEARING_TERMS = (
    "Finding", "Refinement", "Proof", "Proof-gated severity", "Feedback loop",
    "Proof engine", "Proof surface", "Kept test", "Fail-demonstration",
    "Characterization test", "Test oracle", "Proof-complete defect",
    "Pre-flight", "PR review", "UI proof",
    "Mutant", "Mutation battery", "Mutation acceptance",
    "Review packet", "Policy", "Preference", "Diff budget", "Trust zone",
    "Seam", "Deep module", "Deletion test", "Design spec", "Feature plan",
    "Convergence", "Plan gate", "AFK", "HITL", "Handoff", "Conflict",
)

# Trigger phrases that must appear in at most one skill description.
COLLISION_PHRASES = (
    '"plan this"',
    "stress-test",
)

# Skills that write or review code, so they consult the engineering principles.
# Each must reference .nitpickle/principles.md in its load section, in both trees.
# Update this list if the code-touching set changes (see ADR-0012).
CODE_SKILLS = (
    "preflight", "review-pr", "polish", "test-spec",
    "audit", "grill", "feature-plan", "design-spec",
)

failures = []
warnings = []


def fail(msg):
    failures.append(msg)


def warn(msg):
    warnings.append(msg)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    return m.group(1) if m else None


def raw_scalar(fm, key):
    for line in fm.split("\n"):
        if line.startswith(key + ":"):
            return line[len(key) + 1:].strip()
    return None


def tracked_files(root):
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True,
    )
    if out.returncode != 0:
        warn("not a git repo, scanning the working tree instead")
        result = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for name in filenames:
                result.append(os.path.relpath(os.path.join(dirpath, name), root))
        return result
    return [line for line in out.stdout.splitlines() if line]


def strip_code(text):
    if text.count("```") % 2 != 0:
        return None
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    prose = re.sub(r"`[^`]*`", "", prose)
    return prose


def check_skills(root, harness):
    skills_dir = os.path.join(root, "skills", harness)
    names = []
    for d in sorted(os.listdir(skills_dir)):
        sdir = os.path.join(skills_dir, d)
        if not os.path.isdir(sdir):
            continue
        prefix = f"skills/{harness}/{d}"
        skill_md = os.path.join(sdir, "SKILL.md")
        if not os.path.isfile(skill_md):
            fail(f"{prefix}/ has no SKILL.md")
            continue
        fm = frontmatter(read(skill_md))
        if fm is None:
            fail(f"{prefix}/SKILL.md has no frontmatter")
            continue
        raw_desc = raw_scalar(fm, "description")
        if yaml:
            try:
                data = yaml.safe_load(fm)
            except yaml.YAMLError as exc:
                fail(f"{prefix}/SKILL.md frontmatter does not parse: {exc}")
                continue
            name = data.get("name")
            desc = data.get("description")
            if name != d:
                fail(f"{prefix}/SKILL.md name '{name}' does not match its directory")
            if not desc:
                fail(f"{prefix}/SKILL.md has no description")
            elif raw_desc and desc.strip() != raw_desc:
                fail(
                    f"{prefix}/SKILL.md description is truncated by YAML "
                    f"(unquoted hash?): parsed text differs from the raw line"
                )
        else:
            name = raw_scalar(fm, "name")
            if name != d:
                fail(f"{prefix}/SKILL.md name '{name}' does not match its directory")
            if raw_desc and " #" in raw_desc:
                fail(
                    f"{prefix}/SKILL.md description contains an unquoted hash, "
                    f"YAML will truncate it (install pyyaml for the exact check)"
                )
            if raw_desc and not raw_desc.startswith(('"', "'")) and ": " in raw_desc:
                fail(
                    f"{prefix}/SKILL.md description contains a colon-space in an "
                    f"unquoted scalar, strict YAML rejects it (install pyyaml for "
                    f"the exact check)"
                )
        names.append(d)
    return names


def check_references(root, skills, files):
    """Check 3. A claude-code /nitpickle:<name> resolves to a shipped skill. A codex
    skill invokes as the plugin-namespaced $nitpickle:<name>, so it carries no bare
    /nitpickle: token and every $nitpickle:<name> must resolve."""
    claude_pat = re.compile(r"/nitpickle:([a-z0-9-]+)")
    codex_pat = re.compile(r"\$nitpickle:([a-z0-9-]+)")
    for rel in files:
        if not rel.endswith(".md"):
            continue
        norm = rel.replace("\\", "/")
        text = read(os.path.join(root, rel))
        if norm.startswith("skills/codex/"):
            if "/nitpickle:" in text:
                fail(f"{rel} carries a /nitpickle: reference, codex skills use $nitpickle:name")
            for ref in codex_pat.findall(text):
                if ref not in skills["codex"]:
                    fail(f"{rel} references $nitpickle:{ref}, which does not exist")
            continue
        for ref in claude_pat.findall(text):
            if ref not in skills["claude-code"]:
                fail(f"{rel} references /nitpickle:{ref}, which does not exist")


def check_bare_skill_tokens(root, skills, files):
    """Check 4. A bare $<skillname> is a wrong Codex reference, the invocation is
    the plugin-namespaced $nitpickle:<name>. Catch it in any tracked markdown so a
    doc example cannot ship a token that silently fails to resolve."""
    names = sorted(set(skills["codex"]) | set(skills["claude-code"]))
    pattern = re.compile(r"\$(" + "|".join(re.escape(n) for n in names) + r")\b")
    for rel in files:
        if not rel.endswith(".md"):
            continue
        for m in pattern.finditer(read(os.path.join(root, rel))):
            fail(f"{rel} uses a bare ${m.group(1)}, the Codex invocation is $nitpickle:{m.group(1)}")


def check_skills_doc(root, skill_names):
    """Check 12. Every shipped skill has a `## <name>` description section in
    docs/skills.md, so the catalog cannot silently omit one."""
    text = read(os.path.join(root, "docs", "skills.md"))
    for name in skill_names:
        if not re.search(rf"(?m)^## {re.escape(name)} ", text):
            fail(f"docs/skills.md has no description section for '{name}'")


def check_readme_count(root, count):
    readme = read(os.path.join(root, "README.md"))
    expected = NUMBER_WORDS.get(count, str(count))
    pattern = r"\b(" + "|".join(NUMBER_WORDS.values()) + r")(?: \w+)? skills\b"
    found = re.findall(pattern, readme, re.IGNORECASE)
    for word in found:
        if word.lower() != expected:
            fail(f"README says '{word} skills' but skills ship {count} ({expected})")
    if not found:
        warn("README never states the skill count in words")


def check_versions(root):
    versions = {
        ".claude-plugin/plugin.json":
            json.loads(read(os.path.join(root, ".claude-plugin", "plugin.json"))).get("version"),
        ".claude-plugin/marketplace.json":
            json.loads(read(os.path.join(root, ".claude-plugin", "marketplace.json")))["plugins"][0].get("version"),
        ".codex-plugin/plugin.json":
            json.loads(read(os.path.join(root, ".codex-plugin", "plugin.json"))).get("version"),
    }
    if len(set(versions.values())) > 1:
        fail(f"version mismatch across plugin manifests: {versions}")


def check_banned_characters(root, files):
    for rel in files:
        norm = rel.replace("\\", "/")
        if norm.startswith(("docs/handoffs/", "docs/reviews/", "docs/audits/")):
            continue
        path = os.path.join(root, rel)
        try:
            text = read(path)
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        if EM_DASH in text or EN_DASH in text:
            fail(f"{rel} contains a literal em or en dash")
        if rel.endswith(".md"):
            prose = strip_code(text)
            if prose is None:
                warn(f"{rel} has an unmatched code fence, prose checks skipped")
                continue
            if ";" in prose:
                fail(f"{rel} contains a semicolon in markdown prose")
            for entity in DASH_ENTITIES:
                if entity in prose:
                    fail(f"{rel} contains {entity} in markdown prose")


def check_collision_phrases(root, claude_skills):
    for phrase in COLLISION_PHRASES:
        owners = []
        for name in claude_skills:
            fm = frontmatter(read(os.path.join(root, "skills", "claude-code", name, "SKILL.md")))
            desc = raw_scalar(fm, "description") if fm else None
            if desc and phrase in desc:
                owners.append(name)
        if len(owners) > 1:
            fail(
                f"trigger phrase {phrase!r} is claimed by more than one skill "
                f"description: {', '.join(owners)}"
            )


def check_glossary_terms(root):
    glossary = read(os.path.join(root, "CONTEXT.md"))
    for term in LOAD_BEARING_TERMS:
        if f"- **{term}**" not in glossary:
            fail(f"CONTEXT.md has no glossary entry for the load-bearing term '{term}'")


def _block(text, marker):
    """The content between a matched pair of `marker`, or None if absent."""
    m = re.compile(re.escape(marker) + r"\n(.*?)\n" + re.escape(marker), re.S).search(text)
    return m.group(1) if m else None


def check_resolution_blocks(root):
    """Check 11. The resolution block is harness-specific (the global config path
    differs), so it is not synced to a shared home. Instead every skill in a tree
    must carry the same resolution block, so it cannot drift within a tree."""
    marker = "<!-- nitpickle:resolution -->"
    for h in HARNESSES:
        ref_name = ref_block = None
        for name in FULL_BLOCK_SKILLS:
            path = os.path.join(root, "skills", h, name, "SKILL.md")
            block = _block(read(path), marker)
            if block is None:
                fail(f"skills/{h}/{name}/SKILL.md is missing the resolution block")
                continue
            if ref_block is None:
                ref_name, ref_block = name, block
            elif block != ref_block:
                fail(
                    f"skills/{h}/{name}/SKILL.md resolution block differs from "
                    f"skills/{h}/{ref_name}/SKILL.md"
                )


def check_code_skills_principles(root):
    """Check 13. Each code-touching skill must consult .nitpickle/principles.md in
    both trees, so the engineering principles cannot be silently dropped. Anchored
    on the `.nitpickle/`-prefixed form the load sections use, since the resolution
    block already names a bare `principles.md` and would pass this vacuously."""
    for h in HARNESSES:
        for name in CODE_SKILLS:
            path = os.path.join(root, "skills", h, name, "SKILL.md")
            if ".nitpickle/principles.md" not in read(path):
                fail(f"skills/{h}/{name}/SKILL.md does not reference .nitpickle/principles.md")


def check_canonical_blocks(root):
    for block_file, canonical_file, marker in CANONICAL_BLOCKS:
        copy = _block(read(os.path.join(root, block_file)), marker)
        home = _block(read(os.path.join(root, canonical_file)), marker)
        if home is None:
            fail(f"{canonical_file} is missing the canonical block '{marker}'")
            continue
        if copy is None:
            fail(f"{block_file} is missing its copy of the block '{marker}'")
            continue
        if copy != home:
            fail(
                f"{block_file} block '{marker}' differs from the canonical "
                f"home {canonical_file}"
            )


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    root = os.path.abspath(root)

    if yaml is None:
        warn("pyyaml not installed, frontmatter checks degraded to regex")

    files = tracked_files(root)
    skills = {h: check_skills(root, h) for h in HARNESSES}
    claude_skills = skills["claude-code"]

    if set(skills["claude-code"]) != set(skills["codex"]):
        only_cc = set(skills["claude-code"]) - set(skills["codex"])
        only_cx = set(skills["codex"]) - set(skills["claude-code"])
        fail(f"skill sets differ between harnesses: claude-only {only_cc}, codex-only {only_cx}")

    check_references(root, skills, files)
    check_bare_skill_tokens(root, skills, files)
    check_skills_doc(root, claude_skills)
    check_readme_count(root, len(claude_skills))
    check_versions(root)
    check_banned_characters(root, files)
    check_collision_phrases(root, claude_skills)
    check_glossary_terms(root)
    check_canonical_blocks(root)
    check_resolution_blocks(root)
    check_code_skills_principles(root)

    for w in warnings:
        print(f"warning: {w}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"\n{len(failures)} failure(s)")
        sys.exit(1)
    print(f"ok: {len(claude_skills)} skills per harness, {len(files)} tracked files checked")


if __name__ == "__main__":
    main()
