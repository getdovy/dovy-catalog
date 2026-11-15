#!/usr/bin/env python3
"""Structural checks of the catalog before review (docs/recipe-format.md,
"Checks"). dovy's own checks, on every load, have the last word.

    tools/check.py [--debian-names FILE]

FILE lists Debian stable's package names, one per line (CI writes it with
apt-cache pkgnames): a recipe building a package of a name Debian uses must
list it in `replaces`. Without FILE that check is skipped, and said so.
Exit 1 when anything fails; every problem is printed."""

import argparse
import re
import sys
import tomllib
from pathlib import Path

NAME = re.compile(r"^[a-z0-9][a-z0-9.+-]*$")
PKG = re.compile(r"^[a-z0-9][a-z0-9.+-]*(:i386)?$")
HEX = re.compile(r"^[0-9a-f]{64}$")
FPR = re.compile(r"^([0-9A-F]{40}|[0-9A-F]{64})$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

RELEASES = {13}
CAPABILITIES = {"i386", "components", "backports"}
HARDWARE = {"nvidia-turing"}
SCRIPTS = {"preinst", "postinst", "prerm", "postrm", "config", "templates"}
COMMON = {"name", "description", "kind", "version", "revision", "maintainer", "debian", "requires",
          "depends", "conflicts", "replaces", "hardware", "secure-boot", "network", "successor", "user-notes"}
KINDS = {  # fields each kind may carry beyond COMMON
    "upstream-build": {"source", "build-depends", "packages", "scripts"},
    "upstream-binary": {"source", "install", "scripts", "file", "packages", "links"},
    "vendor-repository": {"repository", "packages", "scripts"},
    "testing-rebuild": {"source-package", "source", "packages"},
    "setup": {"packages", "backports", "file", "scripts"},
    "bundle": {"members"},
}
BUILDS = {"upstream-build", "testing-rebuild"}  # build.sh: required, allowed
OWN_NAME = {"upstream-build", "upstream-binary", "testing-rebuild"}  # package named after the recipe
REPO_FIELDS = {"name", "uri", "suite", "components", "key-url", "fingerprints", "maintainer", "file", "pin", "repack"}


def drop_in(p):
    """An absolute path under /etc inside a *.d folder, or tuned's profile override."""
    if not p.startswith("/etc/") or "/../" in p or p.endswith("/"):
        return False
    if re.fullmatch(r"/etc/tuned/profiles/[^/]+/tuned\.conf", p):
        return True
    return any(d.endswith(".d") for d in p.split("/")[2:-1])


def etc_default(p):
    d, _, name = p.rpartition("/")
    return d == "/etc/default" and bool(NAME.match(name))


def recipe(name, r, has_build, problems):
    def bad(msg):
        problems.append(f"recipe {name}: {msg}")

    if r.get("name") != name:
        bad(f"name {r.get('name')!r} differs from its folder")
    if not NAME.match(name):
        bad(f"name must match {NAME.pattern}")
    kind = r.get("kind")
    if kind not in KINDS:
        bad(f"kind: unknown {kind!r}")
        return
    for f in sorted(set(r) - COMMON - KINDS[kind]):
        bad(f"{f}: not a field of kind {kind}")
    d = r.get("description", "")
    if not isinstance(d, str) or not d or "\n" in d or d.endswith("."):
        bad("description: one line, no final period")
    v = r.get("version", "")
    if not isinstance(v, str) or not v or v.lower() == "latest":
        bad("version: an exact version")
    if not r.get("maintainer"):
        bad("maintainer missing")
    deb = r.get("debian", [])
    if not deb or any(x not in RELEASES for x in deb):
        bad(f"debian: releases from {sorted(RELEASES)}")
    for c in r.get("requires", []):
        if c not in CAPABILITIES:
            bad(f"requires: unknown capability {c!r}")
    if r.get("hardware", "") not in ("", *HARDWARE):
        bad(f"hardware: unknown check {r['hardware']!r}")
    if r.get("secure-boot", "") not in ("", "dkms", "unsigned-kernel"):
        bad("secure-boot: dkms or unsigned-kernel")
    if r.get("revision", 1) < 1:
        bad("revision: 1 or more")

    for s in r.get("source", []):
        url = s.get("url", "")
        if not url.startswith("https://"):
            bad(f"source {url}: https only")
        if not HEX.match(s.get("sha256", "")):
            bad(f"source {url}: sha256 must be 64 lowercase hex characters")
        for f in sorted(set(s) - {"url", "sha256"}):
            bad(f"source {url}: unknown field {f}")
    for n in r.get("packages", []) + r.get("build-depends", []) + r.get("replaces", []):
        if not PKG.match(n):
            bad(f"package {n!r}: an exact package name")
    for k, val in r.get("scripts", {}).items():
        if k not in SCRIPTS:
            bad(f"scripts: unknown script {k!r}")
        elif k in ("config", "templates") and val != "":
            bad(f'scripts: {k} can only be dropped ("")')
    for dst, src in r.get("install", {}).items():
        if not (dst.startswith("/usr/") or drop_in(dst)) or "/../" in dst:
            bad(f"install {dst}: an absolute path under /usr/, or a drop-in under /etc")
        if not src or src.startswith("/") or src.startswith("..") or "/../" in src:
            bad(f"install {dst}: source {src!r} must be relative, without ..")
    for link, target in r.get("links", {}).items():
        if not link.startswith("/usr/"):
            bad(f"links {link}: an absolute path under /usr/")
        if not any(target == d or target.startswith(d + "/") for d in r.get("install", {})):
            bad(f"links {link}: {target} is not installed by the recipe")
    for f in r.get("file", []):
        p = f.get("path", "")
        ok = etc_default(p) if kind == "upstream-binary" else drop_in(p)
        if not ok:
            bad(f"file {p}: only " + ("/etc/default/<name>" if kind == "upstream-binary" else "drop-ins under /etc/**/*.d/"))

    if kind in BUILDS and kind == "upstream-build" and not has_build:
        bad("upstream-build needs build.sh")
    if has_build and kind not in BUILDS:
        bad(f"build.sh: not used by kind {kind}")
    if kind in ("upstream-build", "upstream-binary") and not r.get("source"):
        bad(f"{kind} needs [[source]]")
    if kind == "vendor-repository" and not (r.get("repository") and r.get("packages")):
        bad("vendor-repository needs repository and packages")
    if kind == "testing-rebuild":
        src = r.get("source", [])
        if not r.get("source-package"):
            bad("testing-rebuild needs source-package")
        if len(src) != 1 or not src[0].get("url", "").endswith(".dsc"):
            bad("testing-rebuild needs one [[source]]: the .dsc")
    if kind == "setup" and not (r.get("packages") or r.get("file")):
        bad("setup needs packages or [[file]]")
    if kind == "bundle" and not r.get("members"):
        bad("bundle needs members")


def repository(name, q, problems):
    def bad(msg):
        problems.append(f"repository {name}: {msg}")

    if q.get("name") != name:
        bad(f"name {q.get('name')!r} differs from its file name")
    for f in sorted(set(q) - REPO_FIELDS):
        bad(f"{f}: unknown field")
    for f in ("uri", "key-url"):
        if not q.get(f, "").startswith("https://"):
            bad(f"{f}: https only")
    if not q.get("suite") or not q.get("maintainer"):
        bad("suite and maintainer required")
    if q.get("suite", "").endswith("/") != (not q.get("components")):
        bad("components: none for a flat suite (ending in /), else at least one")
    if not q.get("fingerprints"):
        bad("fingerprints required")
    for f in q.get("fingerprints", []):
        if not FPR.match(f):
            bad(f"fingerprint {f}: 40 or 64 uppercase hex characters")
    if q.get("pin") is True:
        bad("pin: only false; repositories are pinned by default")
    if q.get("pin") is False and q.get("repack"):
        bad("pin = false and repack: one or the other")
    for f in q.get("file", []):
        if not etc_default(f.get("path", "")):
            bad(f"file {f.get('path')}: only /etc/default/<name>")


def cross(rs, repos, debian, problems):
    for name, r in sorted(rs.items()):
        for field in ("depends", "conflicts", "members"):
            for n in r.get(field, []):
                if n not in rs:
                    problems.append(f"recipe {name}: {field} names {n}, which does not exist")
        if r.get("successor") and r["successor"] not in rs:
            problems.append(f"recipe {name}: successor {r['successor']} does not exist")
        for n in r.get("conflicts", []):
            if n in rs and name not in rs[n].get("conflicts", []):
                problems.append(f"recipe {name}: conflicts with {n}, but {n} does not list {name}")
        if r.get("repository") and r["repository"] not in repos:
            problems.append(f"recipe {name}: repository {r['repository']} does not exist")
        if debian is not None and r.get("kind") in OWN_NAME and name in debian and name not in r.get("replaces", []):
            problems.append(f"recipe {name}: Debian has a package {name}; list it in replaces")
    state = {}  # dependency cycles: 1 visiting, 2 done

    def visit(n, path):
        if state.get(n) == 1:
            problems.append("dependency cycle: " + " -> ".join(path[path.index(n):] + [n]))
            return
        if state.get(n) == 2 or n not in rs:
            return
        state[n] = 1
        for d in rs[n].get("depends", []):
            visit(d, path + [n])
        state[n] = 2

    for n in sorted(rs):
        visit(n, [])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--debian-names", type=Path, help="Debian stable's package names, one per line")
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    problems, rs, repos = [], {}, {}

    try:
        m = tomllib.loads((root / "catalog.toml").read_text())
        if not VERSION.match(str(m.get("dovy", ""))):
            problems.append('catalog.toml: dovy must be "X.Y.Z"')
    except (OSError, tomllib.TOMLDecodeError) as e:
        problems.append(f"catalog.toml: {e}")
    for f in sorted((root / "repositories").glob("*.toml")):
        try:
            repos[f.stem] = tomllib.loads(f.read_text())
            repository(f.stem, repos[f.stem], problems)
        except tomllib.TOMLDecodeError as e:
            problems.append(f"repository {f.stem}: {e}")
    for d in sorted((root / "recipes").iterdir()):
        f = d / "recipe.toml"
        if not f.exists():
            problems.append(f"recipes/{d.name}: no recipe.toml")
            continue
        try:
            rs[d.name] = tomllib.loads(f.read_text())
        except tomllib.TOMLDecodeError as e:
            problems.append(f"recipe {d.name}: {e}")
            continue
        recipe(d.name, rs[d.name], (d / "build.sh").exists(), problems)
    debian = None
    if args.debian_names:
        debian = set(args.debian_names.read_text().split())
    cross(rs, repos, debian, problems)

    for p in problems:
        print(p)
    print(f"{len(rs)} recipes, {len(repos)} repositories: "
          + (f"{len(problems)} problems" if problems else "no problems"))
    if debian is None:
        print("skipped: recipes against Debian's package names (no --debian-names)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
