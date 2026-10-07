"""Generate platform structures from design files.

    uv run python -m tools.generate blueprints/b2b-saas-sales-led
    uv run python -m tools.generate --all
    uv run python -m tools.generate --all --check

Output goes next to the design: blueprints/<name>/<platform>/ for a blueprint, clients/<client>/<platform>/ for a
client design. --check writes nothing and exits 1 if any committed
file differs from a fresh generation. A platform with no generator module yet is reported and skipped.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import tempfile
from pathlib import Path
from types import ModuleType

if __name__ == "__main__":  # pragma: no cover - allow `python tools/generate.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.design import PLATFORMS, REPO_ROOT, DesignError, load_design
from tools.validate import find_all_designs, validate_design

# Platform name -> module path. Modules are imported lazily so a missing one is not an error.
GENERATOR_MODULES: dict[str, str] = {p: f"tools.generators.{p}" for p in PLATFORMS}


def get_generator(platform: str) -> ModuleType | None:
    """Return the generator module for a platform, or None if it does not exist yet.

    Only a missing generator module counts as "none yet". An ImportError raised inside an
    existing module is a bug and is allowed to propagate.
    """
    name = GENERATOR_MODULES[platform]
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            return None
        raise


def _blueprint_dir(arg: str) -> Path:
    p = Path(arg)
    return p.parent if p.is_file() else p


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {
        str(f.relative_to(directory)): f.read_bytes()
        for f in sorted(directory.rglob("*"))
        if f.is_file()
    }


def generate_blueprint(blueprint: Path, platforms: list[str], *, check: bool) -> tuple[bool, list[str]]:
    """Generate (or check) one blueprint. Returns (ok, messages)."""
    messages: list[str] = []
    try:
        design = load_design(blueprint)
    except DesignError as exc:
        return False, [f"{blueprint.name}: cannot load design: {exc}"]
    errors = [i for i in validate_design(design) if i.severity == "error"]
    if errors:
        return False, [f"{blueprint.name}: design has {len(errors)} error(s); run tools.validate"]
    ok = True
    for platform in platforms:
        module = get_generator(platform)
        if module is None:
            messages.append(f"{blueprint.name}: no generator yet for {platform}")
            continue
        committed = blueprint / platform
        if not check:
            written = module.generate(design, committed)
            messages.append(f"{blueprint.name}: {platform}: wrote {len(written)} file(s)")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            module.generate(design, Path(tmp))
            fresh = _snapshot(Path(tmp))
        current = _snapshot(committed) if committed.is_dir() else {}
        stale = sorted(
            [f"changed: {n}" for n in fresh if n in current and current[n] != fresh[n]]
            + [f"missing: {n}" for n in fresh if n not in current]
            + [f"unexpected: {n}" for n in current if n not in fresh]
        )
        if stale:
            ok = False
            messages.append(f"{blueprint.name}: {platform}: STALE")
            messages.extend(f"    {s}" for s in stale)
        else:
            messages.append(f"{blueprint.name}: {platform}: up to date")
    return ok, messages


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(prog="generate", description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", help="blueprint directories or design.yaml files")
    parser.add_argument("--all", action="store_true", help="every blueprints/*/design.yaml")
    parser.add_argument("--check", action="store_true", help="fail if committed output is stale")
    parser.add_argument("--platform", choices=PLATFORMS, action="append", help="limit to a platform")
    args = parser.parse_args(argv)

    blueprints = [_blueprint_dir(p) for p in args.paths]
    if args.all:
        blueprints += [f.parent for f in find_all_designs(REPO_ROOT)]
    if not blueprints:
        parser.error("give a blueprint path or --all")
    platforms = args.platform or list(PLATFORMS)

    all_ok = True
    for bp in blueprints:
        ok, messages = generate_blueprint(bp, platforms, check=args.check)
        all_ok = all_ok and ok
        for m in messages:
            print(m)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
