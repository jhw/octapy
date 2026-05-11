#!/usr/bin/env python3
"""Unified push / clean / status for octapy projects and sample packs.

Replaces the per-task scripts that used to live as
tools/list_projects.py / copy_project.py / copy_samples.py /
delete_project.py / clean_local.py.

Subcommands:

    sync.py                                       # default = status
    sync.py status
    sync.py push project [pattern] [-f]
    sync.py push samples [pattern] [-f]
    sync.py clean local   [pattern] [-f]
    sync.py clean remote  [pattern] [-f]
    sync.py clean samples [pattern] [-f]

Local sources:
  tmp/projects/<name>.zip   (project zip archives)
  tmp/samples/<pack>/       (sample pack directories)

Remote targets on /Volumes/OCTATRACK/Woldo:
  <PROJECT_NAME>/           — project folder (.work files)
  AUDIO/projects/<NAME>/    — bundled samples for that project
  AUDIO/samples/<PACK>/     — sample-pack directories

Per-item prompts (`y/N`) gate every destructive op when run on a TTY. On a
non-interactive stdin (piped, CI, agent-driven) the prompts auto-confirm —
the verb itself remains the deliberate choice. `-f` skips prompts entirely.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional


OCTATRACK_DEVICE = Path("/Volumes/OCTATRACK/Woldo")
LOCAL_PROJECTS = Path(__file__).parent.parent / "tmp" / "projects"
LOCAL_SAMPLES = Path(__file__).parent.parent / "tmp" / "samples"


# ----------------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------------

def _filter(items, pattern: Optional[str], key):
    if not pattern:
        return items
    pl = pattern.lower()
    return [i for i in items if pl in key(i).lower()]


def find_local_projects(pattern: Optional[str] = None) -> list[Path]:
    """tmp/projects/*.zip matching the pattern (case-insensitive on stem)."""
    if not LOCAL_PROJECTS.exists():
        return []
    zips = sorted(LOCAL_PROJECTS.glob("*.zip"), key=lambda p: p.name)
    return _filter(zips, pattern, lambda p: p.stem)


def find_local_samples(pattern: Optional[str] = None) -> list[Path]:
    """tmp/samples/<pack>/ directories matching the pattern."""
    if not LOCAL_SAMPLES.exists():
        return []
    packs = sorted((d for d in LOCAL_SAMPLES.iterdir() if d.is_dir()),
                   key=lambda d: d.name)
    return _filter(packs, pattern, lambda d: d.name)


def find_remote_projects(pattern: Optional[str] = None) -> list[Path]:
    """Project directories on the device (containing project.work)."""
    if not OCTATRACK_DEVICE.exists():
        return []
    projects = [d for d in OCTATRACK_DEVICE.iterdir()
                if d.is_dir() and (d / "project.work").exists()]
    return _filter(sorted(projects, key=lambda d: d.name), pattern, lambda d: d.name)


def find_remote_samples(pattern: Optional[str] = None) -> list[Path]:
    """Sample pack directories under AUDIO/samples/ on the device."""
    samples_root = OCTATRACK_DEVICE / "AUDIO" / "samples"
    if not samples_root.exists():
        return []
    packs = sorted((d for d in samples_root.iterdir() if d.is_dir()),
                   key=lambda d: d.name)
    return _filter(packs, pattern, lambda d: d.name)


# ----------------------------------------------------------------------------
# Confirm helper (matches pym8/tools/sync.py)
# ----------------------------------------------------------------------------

def confirm(prompt: str, force: bool) -> bool:
    if force:
        return True
    if not sys.stdin.isatty():
        print(f"{prompt}y  (auto-confirmed: non-interactive)")
        return True
    return input(prompt).strip().lower() in ("y", "yes")


def _require_device() -> None:
    if not OCTATRACK_DEVICE.exists():
        sys.exit(f"Octatrack not mounted at {OCTATRACK_DEVICE}")


# ----------------------------------------------------------------------------
# Push
# ----------------------------------------------------------------------------

def push_project(zip_path: Path, force: bool) -> bool:
    """Unpack one project zip onto the OT. Returns True if copied."""
    # Lazy import — only needed when actually pushing
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from octapy import Project

    project = Project.from_zip(zip_path)
    name = project.name
    dest = OCTATRACK_DEVICE / name
    audio = OCTATRACK_DEVICE / "AUDIO" / "projects" / name

    if dest.exists():
        if not confirm(f"    '{name}' exists on device. Overwrite? [y/N] ", force):
            print("    Skipped.")
            return False
        shutil.rmtree(dest)
    if audio.exists():
        shutil.rmtree(audio)

    project.to_directory(dest)

    pool = project.sample_pool
    if pool:
        audio.mkdir(parents=True, exist_ok=True)
        for filename, local_path in pool.items():
            shutil.copy2(local_path, audio / filename)
        print(f"    Copied '{name}' ({len(pool)} samples)")
    else:
        print(f"    Copied '{name}'")
    return True


def push_samples(pack: Path, force: bool) -> bool:
    """Copy one sample pack onto the OT. Returns True if copied."""
    dest = OCTATRACK_DEVICE / "AUDIO" / "samples" / pack.name
    if dest.exists():
        if not confirm(f"    '{pack.name}' exists on device. Overwrite? [y/N] ", force):
            print("    Skipped.")
            return False
        shutil.rmtree(dest)
    shutil.copytree(pack, dest)
    file_count = sum(1 for f in dest.rglob("*") if f.is_file())
    print(f"    Copied '{pack.name}' ({file_count} files)")
    return True


def cmd_push(kind: str, pattern: Optional[str], force: bool) -> None:
    _require_device()

    if kind == "project":
        items = find_local_projects(pattern)
        label = "project"
        push_one = push_project
        item_name = lambda p: p.stem
    elif kind == "samples":
        items = find_local_samples(pattern)
        label = "sample pack"
        push_one = push_samples
        item_name = lambda p: p.name
    else:
        sys.exit(f"unknown push target: {kind}")

    if not items:
        which = f" matching '{pattern}'" if pattern else ""
        print(f"no local {label}s{which}")
        return

    print(f"found {len(items)} {label}(s):")
    copied = 0
    for item in items:
        if confirm(f"  copy {item_name(item)}? [y/N] ", force):
            if push_one(item, force):
                copied += 1
        else:
            print("    Skipped.")
    print(f"\ncopied {copied} of {len(items)} {label}(s).")


# ----------------------------------------------------------------------------
# Clean
# ----------------------------------------------------------------------------

def _clean(items, item_name, label: str, remove_extras=None, force: bool = False) -> None:
    if not items:
        print(f"no {label}s found")
        return
    print(f"found {len(items)} {label}(s):")
    removed = 0
    for item in items:
        name = item_name(item)
        if not confirm(f"  remove {name}? [y/N] ", force):
            print("    Skipped.")
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        if remove_extras is not None:
            for extra in remove_extras(item):
                if extra.exists():
                    shutil.rmtree(extra)
        print(f"    Removed '{name}'")
        removed += 1
    print(f"\nremoved {removed} of {len(items)} {label}(s).")


def cmd_clean_local(pattern: Optional[str], force: bool) -> None:
    """Delete tmp/projects/<name>.zip files."""
    items = find_local_projects(pattern)
    _clean(items, lambda p: p.stem, "local project zip", force=force)


def cmd_clean_remote(pattern: Optional[str], force: bool) -> None:
    """Delete projects from the OT — including their AUDIO/projects/<NAME>/ folders."""
    _require_device()
    items = find_remote_projects(pattern)

    def project_extras(p: Path):
        return [OCTATRACK_DEVICE / "AUDIO" / "projects" / p.name]

    _clean(items, lambda p: p.name, "device project",
           remove_extras=project_extras, force=force)


def cmd_clean_samples(pattern: Optional[str], force: bool) -> None:
    """Delete sample packs from the OT (AUDIO/samples/<PACK>/)."""
    _require_device()
    items = find_remote_samples(pattern)
    _clean(items, lambda p: p.name, "device sample pack", force=force)


# ----------------------------------------------------------------------------
# Status
# ----------------------------------------------------------------------------

def cmd_status() -> None:
    local_projects = {p.stem for p in find_local_projects()}
    local_samples = {p.name for p in find_local_samples()}
    print(f"local projects ({len(local_projects):>2}): "
          + (", ".join(sorted(local_projects)) or "—"))
    print(f"local samples  ({len(local_samples):>2}): "
          + (", ".join(sorted(local_samples)) or "—"))

    if not OCTATRACK_DEVICE.exists():
        print(f"\nremote: Octatrack not mounted at {OCTATRACK_DEVICE}")
        return

    remote_projects = {p.name for p in find_remote_projects()}
    remote_samples = {p.name for p in find_remote_samples()}
    print(f"\nremote projects ({len(remote_projects):>2}): "
          + (", ".join(sorted(remote_projects)) or "—"))
    print(f"remote samples  ({len(remote_samples):>2}): "
          + (", ".join(sorted(remote_samples)) or "—"))


# ----------------------------------------------------------------------------
# Argparse
# ----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd")

    def add_pattern_and_force(p):
        p.add_argument("pattern", nargs="?", default=None,
                       help="case-insensitive substring filter")
        p.add_argument("-f", "--force", action="store_true",
                       help="skip per-item prompt")

    sub.add_parser("status", help="compare local and device sets")

    push_p = sub.add_parser("push", help="copy local items to the device")
    push_sub = push_p.add_subparsers(dest="push_what", required=True)
    add_pattern_and_force(push_sub.add_parser("project",
                                              help="push tmp/projects/*.zip"))
    add_pattern_and_force(push_sub.add_parser("samples",
                                              help="push tmp/samples/*/"))

    clean_p = sub.add_parser("clean", help="remove local or device items")
    clean_sub = clean_p.add_subparsers(dest="clean_what", required=True)
    add_pattern_and_force(clean_sub.add_parser("local",
                                               help="rm tmp/projects/<n>.zip"))
    add_pattern_and_force(clean_sub.add_parser("remote",
                                               help="rm device project + audio folder"))
    add_pattern_and_force(clean_sub.add_parser("samples",
                                               help="rm device sample pack"))
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    cmd = args.cmd or "status"

    if cmd == "status":
        cmd_status()
    elif cmd == "push":
        cmd_push(args.push_what, args.pattern, args.force)
    elif cmd == "clean":
        if args.clean_what == "local":
            cmd_clean_local(args.pattern, args.force)
        elif args.clean_what == "remote":
            cmd_clean_remote(args.pattern, args.force)
        elif args.clean_what == "samples":
            cmd_clean_samples(args.pattern, args.force)


if __name__ == "__main__":
    main()
