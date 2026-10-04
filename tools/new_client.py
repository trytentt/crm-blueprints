"""Start a client workspace from a blueprint.

    uv run python -m tools.new_client b2b-saas-sales-led acme --name "Acme Ltd"

Creates clients/<client>/ with design.yaml, notes.md, CHANGELOG.md and build/. Refuses to
overwrite an existing client folder.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

if __name__ == "__main__":  # pragma: no cover - allow `python tools/new_client.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from tools.design import REPO_ROOT

CLIENT_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_NAME_LINE = re.compile(r"^name:.*$", re.M)


def set_design_name(text: str, name: str) -> str:
    """Replace the top-level `name:` line (or add one after the comments at the top)."""
    line = "name: " + yaml.safe_dump(name, allow_unicode=True, width=1000).splitlines()[0]
    if _NAME_LINE.search(text):
        return _NAME_LINE.sub(lambda _m: line, text, count=1)
    return line + "\n" + text


def create_client(blueprint: Path, client: str, display_name: str, clients_dir: Path) -> Path:
    """Create the client folder and return it. Raises `FileExistsError` or `ValueError` on refusal."""
    if not CLIENT_SLUG.match(client):
        raise ValueError(f"client name {client!r} must be lowercase letters, digits and hyphens")
    source = blueprint / "design.yaml" if blueprint.is_dir() else blueprint
    if not source.is_file():
        raise ValueError(f"no design.yaml at {source}")
    dest = clients_dir / client
    if dest.exists():
        raise FileExistsError(f"{dest} already exists. Choose another name; nothing was changed.")
    base_name = yaml.safe_load(source.read_text(encoding="utf-8")).get("name", blueprint.name)
    dest.mkdir(parents=True)
    (dest / "design.yaml").write_text(
        set_design_name(source.read_text(encoding="utf-8"), f"{display_name} ({base_name})"),
        encoding="utf-8",
    )
    (dest / "notes.md").write_text(
        f"# {display_name}\n\nStarted from blueprint `{source.parent.name}`.\n\n"
        "## Discovery\n\n(Answers to docs/discovery-questions.md.)\n\n"
        "## Decisions\n\n(Choices made with the client and why.)\n\n"
        "## Assumptions\n\n(Anything built without the client saying so.)\n",
        encoding="utf-8",
    )
    (dest / "CHANGELOG.md").write_text(
        f"# Changelog: {display_name}\n\n## {date.today().isoformat()}\n\n"
        f"- Started from blueprint `{source.parent.name}`.\n",
        encoding="utf-8",
    )
    (dest / "build").mkdir()
    (dest / "build" / ".gitkeep").write_text("", encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(prog="new_client", description=__doc__.split("\n")[0])
    parser.add_argument("blueprint", help="blueprint folder name, or a path to a blueprint folder")
    parser.add_argument("client", help="client folder name: lowercase letters, digits, hyphens")
    parser.add_argument("--name", help="client display name (default: from the folder name)")
    parser.add_argument("--clients-dir", type=Path, default=REPO_ROOT / "clients")
    args = parser.parse_args(argv)
    blueprint = Path(args.blueprint)
    if not blueprint.exists():
        blueprint = REPO_ROOT / "blueprints" / args.blueprint
    display = args.name or args.client.replace("-", " ").title()
    try:
        dest = create_client(blueprint, args.client, display, args.clients_dir)
    except (FileExistsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Created {dest}. Next: edit design.yaml, then `uv run python -m tools.validate {dest}`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
