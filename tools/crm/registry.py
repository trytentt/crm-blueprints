"""Find the adapter for a platform.

Convention (D-14): each module `tools/crm/<platform>.py` exposes
`make_adapter(env, *, target, production) -> Adapter`. The module is imported only when asked for,
so a missing or broken platform module never stops the others from working.
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Mapping

from tools.crm.base import Adapter
from tools.crm.safety import SafetyError
from tools.design import PLATFORMS


class RegistryError(RuntimeError):
    """The adapter could not be found or built. The message never contains credentials."""


def get_adapter(
    platform: str,
    env: Mapping[str, str] | None = None,
    target: str | None = None,
    production: bool = False,
) -> Adapter:
    """Import `tools.crm.<platform>` and build its adapter.

    Raises `RegistryError` for an unknown platform, a missing module, a module without
    `make_adapter`, or missing credentials.
    """
    if platform not in PLATFORMS:
        raise RegistryError(f"Unknown platform {platform!r}. Choose one of: {', '.join(PLATFORMS)}.")
    module_name = f"tools.crm.{platform}"
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            raise RegistryError(f"No adapter for {platform}: {module_name} does not exist yet.") from exc
        raise RegistryError(f"The {platform} adapter needs a package that is not installed ({exc.name}).") from exc
    factory = getattr(module, "make_adapter", None)
    if factory is None:
        raise RegistryError(f"{module_name} has no make_adapter(env, *, target, production).")
    try:
        return factory(os.environ if env is None else env, target=target, production=production)
    except SafetyError as exc:
        raise RegistryError(f"Cannot build the {platform} adapter: {exc}") from exc
