#!/usr/bin/env python3
"""Seed the NitPickle global default config into the harness config directory.

Copies every file in `defaults/nitpickle/` to the harness global location so any
repo with no local `.nitpickle/` inherits it. It globs the directory rather than
naming files, so a new default (like principles.md) is seeded with no change here.
Existing files are left untouched unless `--force`, so a customized global config
is never clobbered.

Usage: python3 tools/seed_defaults.py [--harness claude|codex] [--force] [--home DIR]
"""
import argparse
import os
import shutil

HARNESS_DIRS = {
    "claude": (".claude", "nitpickle"),
    "codex": (".config", "nitpickle"),
}


def seed_defaults(root, harness, home=None, force=False):
    """Copy `defaults/nitpickle/*` to the harness global config. `root` is the
    plugin or repo root that holds `defaults/`. Non-clobber unless force, so a
    customized global file survives. Returns (dst_dir, seeded, skipped)."""
    home = home or os.path.expanduser("~")
    src_dir = os.path.join(root, "defaults", "nitpickle")
    dst_dir = os.path.join(home, *HARNESS_DIRS[harness])
    os.makedirs(dst_dir, exist_ok=True)

    seeded, skipped = [], []
    for name in sorted(os.listdir(src_dir)):
        src = os.path.join(src_dir, name)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dst_dir, name)
        if os.path.exists(dst) and not force:
            skipped.append(name)
            continue
        shutil.copy2(src, dst)
        seeded.append(name)
    return dst_dir, seeded, skipped


def main():
    parser = argparse.ArgumentParser(description="Seed NitPickle global defaults.")
    parser.add_argument("--harness", choices=sorted(HARNESS_DIRS), default="claude")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing files (default leaves them untouched)")
    parser.add_argument("--home", default=None, help="home directory, for testing")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dst_dir, seeded, skipped = seed_defaults(root, args.harness, args.home, args.force)

    print("seeded %d file(s) to %s" % (len(seeded), dst_dir))
    if seeded:
        print("  seeded: %s" % ", ".join(seeded))
    if skipped:
        print("  skipped (already present, use --force to overwrite): %s" % ", ".join(skipped))


if __name__ == "__main__":
    main()
