"""Helpers shared by the CLI tools: the .env loader, adapter creation and error handling."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Callable, Mapping

from tools.crm.base import Adapter
from tools.design import PLATFORMS, REPO_ROOT

AdapterFactory = Callable[[str, Mapping[str, str], "str | None", bool], Adapter]

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def ensure_repo_on_path(file: str) -> None:
    """Let `python tools/x.py` import `tools.*` (call from the script's `__main__` guard)."""
    sys.path.insert(0, str(Path(file).resolve().parent.parent))


def parse_env_file(text: str) -> dict[str, str]:
    """Parse KEY=VALUE lines. Skips blanks and comments; strips one pair of matching quotes."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        value = m.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[m.group(1)] = value
    return values


def load_env(path: Path | None = None, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return `environ` (default: the process environment) plus values from `.env` if it exists.

    A variable already set in the environment wins over the file.
    """
    env_path = path if path is not None else REPO_ROOT / ".env"
    merged: dict[str, str] = {}
    if env_path.is_file():
        merged.update(parse_env_file(env_path.read_text(encoding="utf-8")))
    merged.update(os.environ if environ is None else environ)
    return merged


def secret_values(env: Mapping[str, str]) -> list[str]:
    """Environment values that look like credentials, for exact-match redaction."""
    pattern = re.compile(r"token|secret|password|passwd|key|credential|auth", re.I)
    return [v for k, v in env.items() if pattern.search(k) and len(v) >= 6]


def default_factory(platform: str, env: Mapping[str, str], target: str | None, production: bool) -> Adapter:
    """Build an adapter through the registry."""
    from tools.crm.registry import get_adapter

    return get_adapter(platform, env, target, production)


def add_platform_args(parser, *, required: bool = True) -> None:  # type: ignore[no-untyped-def]
    """Add --platform and --target."""
    parser.add_argument("--platform", choices=PLATFORMS, required=required, help="CRM platform")
    parser.add_argument("--target", default=None, help="sandbox or org name (default: the sandbox)")
