#!/usr/bin/env python3
"""Build Checkmk extension packages (.mkp) from the plugin folders in this repo.

Every top-level directory containing a ``package.json`` is a package. Its
subdirectories are Checkmk package parts (``agent_based``, ``agents``,
``checks``, ``web``, ...) and are packed exactly like ``mkp package`` does:

    <name>-<version>.mkp  (tar.gz)
    ├── info              pprint'ed Python dict
    ├── info.json         same data as JSON
    └── <part>.tar        one uncompressed tar per part

Only the Python standard library is used, so no Checkmk site is required.

Usage:
    tools/build_mkp.py                 # build all packages into dist/
    tools/build_mkp.py ssh_keys        # build selected packages
    tools/build_mkp.py --check-tag ssh_keys-v1.0.0
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import pprint
import sys
import tarfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Package parts known to Checkmk 2.3 / 2.4 (see cmk.utils.packaging.PackagePart).
KNOWN_PARTS = (
    "agent_based",
    "agents",
    "alert_handlers",
    "bin",
    "checkman",
    "checks",
    "cmk_addons_plugins",
    "cmk_plugins",
    "doc",
    "ec_rule_packs",
    "gui",
    "inventory",
    "lib",
    "locales",
    "mibs",
    "notifications",
    "pnp-templates",
    "web",
)

REQUIRED_KEYS = ("name", "title", "version", "version.min_required")
IGNORED_NAMES = {"__pycache__", ".DS_Store"}
IGNORED_SUFFIXES = (".pyc", ".pyo", ".swp")


def find_packages() -> dict[str, Path]:
    return {
        p.parent.name: p.parent
        for p in sorted(REPO_ROOT.glob("*/package.json"))
        if not p.parent.name.startswith(".")
    }


def load_manifest(pkg_dir: Path) -> dict:
    manifest = json.loads((pkg_dir / "package.json").read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_KEYS if not manifest.get(k)]
    if missing:
        raise SystemExit(f"{pkg_dir.name}/package.json: missing keys {missing}")
    if manifest["name"] != pkg_dir.name:
        raise SystemExit(
            f"{pkg_dir.name}/package.json: name {manifest['name']!r} must match folder name"
        )
    manifest.setdefault("description", "")
    manifest.setdefault("author", "")
    manifest.setdefault("download_url", "")
    manifest.setdefault("version.packaged", manifest["version.min_required"])
    manifest.setdefault("version.usable_until", None)
    return manifest


def collect_files(pkg_dir: Path) -> dict[str, list[str]]:
    files: dict[str, list[str]] = {}
    for part_dir in sorted(p for p in pkg_dir.iterdir() if p.is_dir()):
        if part_dir.name.startswith("."):
            continue
        if part_dir.name not in KNOWN_PARTS:
            raise SystemExit(
                f"{pkg_dir.name}/{part_dir.name}: unknown package part "
                f"(expected one of {', '.join(KNOWN_PARTS)})"
            )
        rel_files = sorted(
            f.relative_to(part_dir).as_posix()
            for f in part_dir.rglob("*")
            if f.is_file()
            and not IGNORED_NAMES.intersection(f.relative_to(part_dir).parts)
            and not f.name.endswith(IGNORED_SUFFIXES)
        )
        if rel_files:
            files[part_dir.name] = rel_files
    if not files:
        raise SystemExit(f"{pkg_dir.name}: package contains no files")
    return files


def _add_bytes(tar: tarfile.TarFile, name: str, data: bytes, mtime: int, mode: int = 0o644) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mtime = mtime
    info.mode = mode
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    tar.addfile(info, io.BytesIO(data))


def _part_tar(part_dir: Path, rel_files: list[str], mtime: int) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.GNU_FORMAT) as tar:
        for rel in rel_files:
            src = part_dir / rel
            mode = 0o755 if os.access(src, os.X_OK) else 0o644
            _add_bytes(tar, rel, src.read_bytes(), mtime, mode)
    return buf.getvalue()


def build(pkg_dir: Path, out_dir: Path, mtime: int) -> Path:
    manifest = load_manifest(pkg_dir)
    manifest["files"] = collect_files(pkg_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{manifest['name']}-{manifest['version']}.mkp"

    with open(target, "wb") as raw, gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, mtime=mtime, compresslevel=9
    ) as gz, tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as tar:
        _add_bytes(tar, "info", (pprint.pformat(manifest) + "\n").encode(), mtime)
        _add_bytes(tar, "info.json", json.dumps(manifest, separators=(",", ":")).encode(), mtime)
        for part, rel_files in manifest["files"].items():
            _add_bytes(tar, f"{part}.tar", _part_tar(pkg_dir / part, rel_files, mtime), mtime)

    return target


def check_tag(tag: str, packages: dict[str, Path]) -> str:
    """Validate a release tag of the form ``<name>-v<version>`` and return the package name."""
    name, sep, version = tag.rpartition("-v")
    if not sep or name not in packages:
        raise SystemExit(f"tag {tag!r} does not match '<package>-v<version>' for a known package")
    expected = load_manifest(packages[name])["version"]
    if version != expected:
        raise SystemExit(f"tag {tag!r} does not match {name}/package.json version {expected!r}")
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("packages", nargs="*", help="package folder names (default: all)")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "dist", help="output directory")
    parser.add_argument("--check-tag", metavar="TAG", help="validate TAG and build only that package")
    parser.add_argument("--list", action="store_true", help="list packages and exit")
    args = parser.parse_args()

    packages = find_packages()
    if args.list:
        for name, path in packages.items():
            print(f"{name} {load_manifest(path)['version']}")
        return 0

    selected = args.packages or list(packages)
    if args.check_tag:
        selected = [check_tag(args.check_tag, packages)]
    unknown = [n for n in selected if n not in packages]
    if unknown:
        raise SystemExit(f"unknown package(s): {', '.join(unknown)}")

    mtime = int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))
    for name in selected:
        print(build(packages[name], args.out, mtime))
    return 0


if __name__ == "__main__":
    sys.exit(main())
