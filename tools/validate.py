#!/usr/bin/env python3
"""NitPickle repo consistency validator.

Run from the repo root (or pass the root as the first argument):

    python3 tools/validate.py [root]

Checks:
  1. Every skills/*/SKILL.md has frontmatter whose name matches its directory.
  2. The parsed description matches its raw line, catching silent YAML comment
     truncation from an unquoted hash (valid YAML, invisible to a parse check).
  3. Every /nitpickle:<name> reference resolves to a shipped skill.
  4. The README's written-out skill count matches the skills directory.
  5. plugin.json and marketplace.json versions match.
  6. No banned characters in tracked files: literal em or en dash anywhere,
     semicolons and HTML-entity dashes in markdown prose (code stripped with
     the hook's own semantics, unmatched fences fail open with a warning).
  7. Verbatim canonical blocks match their canonical home (registry is filled
     by later phases, an empty registry passes).

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
}

# Filled by later phases: (block_file, canonical_file, marker) triples whose
# marker-delimited content must match byte for byte.
CANONICAL_BLOCKS = []

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


def check_skills(root):
    skills_dir = os.path.join(root, "skills")
    names = []
    for d in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, d, "SKILL.md")
        if not os.path.isfile(skill_md):
            fail(f"skills/{d}/ has no SKILL.md")
            continue
        fm = frontmatter(read(skill_md))
        if fm is None:
            fail(f"skills/{d}/SKILL.md has no frontmatter")
            continue
        raw_desc = raw_scalar(fm, "description")
        if yaml:
            try:
                data = yaml.safe_load(fm)
            except yaml.YAMLError as exc:
                fail(f"skills/{d}/SKILL.md frontmatter does not parse: {exc}")
                continue
            name = data.get("name")
            desc = data.get("description")
            if name != d:
                fail(f"skills/{d}/SKILL.md name '{name}' does not match its directory")
            if not desc:
                fail(f"skills/{d}/SKILL.md has no description")
            elif raw_desc and desc.strip() != raw_desc:
                fail(
                    f"skills/{d}/SKILL.md description is truncated by YAML "
                    f"(unquoted hash?): parsed text differs from the raw line"
                )
        else:
            name = raw_scalar(fm, "name")
            if name != d:
                fail(f"skills/{d}/SKILL.md name '{name}' does not match its directory")
            if raw_desc and " #" in raw_desc:
                fail(
                    f"skills/{d}/SKILL.md description contains an unquoted hash, "
                    f"YAML will truncate it (install pyyaml for the exact check)"
                )
        names.append(d)
    return names


def check_references(root, skill_names, files):
    pattern = re.compile(r"/nitpickle:([a-z0-9-]+)")
    for rel in files:
        if not rel.endswith(".md"):
            continue
        for ref in pattern.findall(read(os.path.join(root, rel))):
            if ref not in skill_names:
                fail(f"{rel} references /nitpickle:{ref}, which does not exist")


def check_readme_count(root, skill_names):
    readme = read(os.path.join(root, "README.md"))
    expected = NUMBER_WORDS.get(len(skill_names), str(len(skill_names)))
    found = re.findall(r"\b(" + "|".join(NUMBER_WORDS.values()) + r") skills\b", readme)
    for word in found:
        if word != expected:
            fail(
                f"README says '{word} skills' but skills/ ships "
                f"{len(skill_names)} ({expected})"
            )
    if not found:
        warn("README never states the skill count in words")


def check_versions(root):
    plugin = json.loads(read(os.path.join(root, ".claude-plugin", "plugin.json")))
    marketplace = json.loads(
        read(os.path.join(root, ".claude-plugin", "marketplace.json"))
    )
    pv = plugin.get("version")
    mv = marketplace["plugins"][0].get("version")
    if pv != mv:
        fail(f"version mismatch: plugin.json {pv} vs marketplace.json {mv}")


def check_banned_characters(root, files):
    for rel in files:
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


def check_canonical_blocks(root):
    for block_file, canonical_file, marker in CANONICAL_BLOCKS:
        pattern = re.compile(
            re.escape(marker) + r"\n(.*?)\n" + re.escape(marker), re.S
        )
        copy = pattern.search(read(os.path.join(root, block_file)))
        home = pattern.search(read(os.path.join(root, canonical_file)))
        if not home:
            fail(f"{canonical_file} is missing the canonical block '{marker}'")
            continue
        if not copy:
            fail(f"{block_file} is missing its copy of the block '{marker}'")
            continue
        if copy.group(1) != home.group(1):
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
    skill_names = check_skills(root)
    check_references(root, skill_names, files)
    check_readme_count(root, skill_names)
    check_versions(root)
    check_banned_characters(root, files)
    check_canonical_blocks(root)

    for w in warnings:
        print(f"warning: {w}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"\n{len(failures)} failure(s)")
        sys.exit(1)
    print(f"ok: {len(skill_names)} skills, {len(files)} tracked files checked")


if __name__ == "__main__":
    main()
