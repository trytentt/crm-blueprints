"""Safety gates, the production confirmation prompt, and log redaction.

Rules enforced here:
1. Dry run unless `--execute`.
2. Sandbox by default. Production needs `--execute --production` plus typing the account or org name.
3. Changes marked `needs_review` run only with `--allow-review`. Destructive changes never run.
9. Credentials come from environment variables only, and never appear in logs or errors.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, TextIO

from tools.crm.base import Change, Plan

REDACTED = "[redacted]"


class SafetyError(RuntimeError):
    """A safety rule stopped the run. The message never contains credentials."""


@dataclass(frozen=True)
class Mode:
    """What a run is allowed to do."""

    dry_run: bool
    production: bool
    allow_review: bool


def resolve_mode(*, execute: bool, production: bool, allow_review: bool = False) -> Mode:
    """Turn CLI flags into a `Mode`.

    No `--execute` means a dry run. `--production` without `--execute` is refused rather than
    ignored, so a typo cannot look like a safe run. `--allow-review` without `--execute` is
    harmless (a dry run) and allowed.
    """
    if production and not execute:
        raise SafetyError("--production needs --execute. Without --execute this is a dry run.")
    return Mode(dry_run=not execute, production=production, allow_review=allow_review)


def confirm_production(
    account_name: str,
    *,
    input_fn: Callable[[str], str] | None = None,
    interactive: bool | None = None,
    out: TextIO | None = None,
) -> None:
    """Make the user type the account or org name. Raises `SafetyError` unless it matches exactly.

    Refuses to run non-interactively, so a script or pipe cannot confirm on someone's behalf.
    `input_fn` and `interactive` exist for tests; the defaults read the real terminal.
    """
    if not account_name or not account_name.strip():
        raise SafetyError("Production runs need the account or org name to confirm against.")
    if interactive is None:
        interactive = sys.stdin.isatty()
    if not interactive:
        raise SafetyError("Production confirmation needs an interactive terminal.")
    stream = out or sys.stdout
    print(f"PRODUCTION: this will change the live account {account_name!r}.", file=stream)
    reader = input_fn or input
    answer = reader(f"Type the account name ({account_name}) to continue: ")
    if answer.strip() != account_name.strip():
        raise SafetyError("Confirmation did not match the account name. Nothing was changed.")


def check_gates(
    plan: Plan,
    mode: Mode,
    *,
    confirm: Callable[[str], None] | None = None,
) -> tuple[tuple[Change, ...], tuple[Change, ...]]:
    """Split a plan's changes into (runnable, held) for this mode.

    Raises `SafetyError` if the plan contains a destructive change (the planner never makes one,
    so this is a guard against a hand-edited plan file). `needs_review` changes are held unless
    `allow_review` is set. For a production execute run, `confirm(plan.target)` is called first;
    pass `confirm_production` or a stub. A dry run never asks.
    """
    for change in plan.changes:
        if change.risk == "destructive":
            raise SafetyError(
                f"Plan contains a destructive change ({change.kind} {change.target}). "
                "Destructive work is done by hand as a manual step."
            )
    if mode.production and not mode.dry_run:
        (confirm or confirm_production)(plan.target)
    runnable: list[Change] = []
    held: list[Change] = []
    for change in plan.changes:
        if change.risk == "needs_review" and not mode.allow_review:
            held.append(change)
        else:
            runnable.append(change)
    return tuple(runnable), tuple(held)


def get_credential(name: str, env: dict[str, str] | None = None) -> str:
    """Read a credential from the environment. The error names the variable, never a value."""
    value = (env if env is not None else os.environ).get(name, "")
    if not value:
        raise SafetyError(f"Environment variable {name} is not set. Add it to .env (git-ignored).")
    return value


# --- redaction -------------------------------------------------------------------------------

_SENSITIVE_KEY = re.compile(r"token|secret|password|passwd|api[_-]?key|authorization|credential", re.I)

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Authorization headers and bearer tokens.
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{6,}"), r"\1 " + REDACTED),
    # key=value or key: value where the key names a secret.
    (
        re.compile(
            r"(?i)\b([\w-]*(?:token|secret|password|passwd|api[_-]?key|authorization|credential)[\w-]*"
            r"[\"']?\s*[:=]\s*[\"']?)([^\s\"',;&}]+)"
        ),
        r"\1" + REDACTED,
    ),
    # HubSpot private app tokens, OpenAI/Anthropic-style keys, Slack tokens, GitHub tokens.
    (re.compile(r"\b(?:pat-[a-z]{2,3}\d?-|sk-|xox[abprs]-|ghp_|gho_|github_pat_)[A-Za-z0-9_-]{8,}"), REDACTED),
    # Salesforce session ids (org id, bang, long token).
    (re.compile(r"\b00D[A-Za-z0-9]{12,15}![A-Za-z0-9._]{20,}"), REDACTED),
    # Email addresses.
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"), REDACTED),
    # Phone numbers: start with +, a leading 0, or a bracketed area code, then 8 or more digit-ish characters.
    (re.compile(r"(?<![\w.])(?:\+\d|\(?0\d|\(\d{2,4}\))[\d\s().-]{7,}\d"), REDACTED),
)


def redact(text: str, secrets: Iterable[str] = ()) -> str:
    """Remove tokens, emails and phone numbers from log text.

    `secrets` are exact credential values to strip wherever they appear, for example the values
    read from the environment. Order matters: secrets first, then patterns.
    """
    for secret in secrets:
        if secret and len(secret) >= 4:
            text = text.replace(secret, REDACTED)
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_data(value: Any, secrets: Iterable[str] = ()) -> Any:
    """Redact strings inside nested dicts and lists. Values under secret-looking keys are removed."""
    secrets = tuple(secrets)
    if isinstance(value, str):
        return redact(value, secrets)
    if isinstance(value, dict):
        return {
            k: (REDACTED if isinstance(k, str) and _SENSITIVE_KEY.search(k) else redact_data(v, secrets))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_data(v, secrets) for v in value]
    return value


def write_apply_log(log_dir: Path, name: str, text: str, secrets: Iterable[str] = ()) -> Path:
    """Write redacted text to `log_dir/name` and return the path. Creates the directory."""
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / name
    path.write_text(redact(text, secrets), encoding="utf-8")
    return path
