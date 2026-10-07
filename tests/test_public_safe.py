"""The repo is public-safe (DECISIONS D-16): no local paths, no secrets, no real email addresses in any file.

Scans every file git tracks, plus untracked files that are not ignored, so a new file is checked before it
is committed. Findings are reported as `path:line: kind: text`. A deliberate fixture goes in `ALLOWED`
with the reason.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tools.design import REPO_ROOT

LOCAL_PATH = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\+Users\\)[A-Za-z0-9._-]+")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")
SECRET_SHAPES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OpenAI-style key (sk-)", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("GitHub token (ghp_)", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}")),
    ("Slack token (xoxb/xoxp)", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("AWS access key id (AKIA)", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("bearer token", re.compile(r"(?i)\bbearer\s+(?!<|\{|\$|\[)[A-Za-z0-9._~+/=-]{20,}")),
    ("Google API key (AIza)", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("HubSpot private app token", re.compile(r"\bpat-[a-z]{2,3}\d?-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")),
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")

# Domains that cannot belong to a real person (RFC 2606 and 6761, plus the repo's own fake ones).
FAKE_DOMAINS = {
    "example.com", "example.org", "example.net", "acme.test", "acme.example", "example.test",
    "test", "invalid", "localhost",
    "example.co.uk",  # the UK form; used by one redaction test that needs a two-part suffix
}
FAKE_SUFFIXES = (".test", ".example", ".invalid", ".localhost", ".example.com", ".example.org", ".example.net")

_PAT = "secret-shaped string: HubSpot private app token"
_SK = "secret-shaped string: OpenAI-style key (sk-)"
# (path, kind) -> reason, for a finding that is deliberate. Every entry must still match something.
ALLOWED: dict[tuple[str, str], str] = {
    ("tests/test_crm_hubspot.py", _PAT): "dummy token (00000000-aaaa-...) the HubSpot adapter test hands to the stub",
    ("tests/test_end_to_end.py", _PAT): "dummy token (00000000-aaaa-...) the end-to-end test hands to the stub",
    ("tests/test_safety.py", _PAT): "made-up token (12345678-aaaa-...) whose redaction the test checks",
    ("tests/test_safety.py", _SK): "made-up key (sk-live-1234567890abcdef) whose redaction the test checks",
}
# Files that hold samples of what the scanner must catch. Skipped whole.
SELF_FIXTURES = {"tests/test_public_safe.py": "its parametrised samples are the bad strings on purpose"}


def _files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout.decode()
    return sorted(REPO_ROOT / p for p in out.split("\0") if p and (REPO_ROOT / p).is_file())


def _fake_domain(domain: str) -> bool:
    d = domain.lower().rstrip(".")
    return d in FAKE_DOMAINS or d.endswith(FAKE_SUFFIXES)


def scan_text(text: str) -> list[tuple[int, str, str]]:
    """Return (line number, kind, excerpt) for every public-safety finding in `text`."""
    found: list[tuple[int, str, str]] = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in LOCAL_PATH.finditer(line):
            found.append((n, "local absolute path", m.group(0)))
        if PRIVATE_KEY.search(line):
            found.append((n, "private key", "-----BEGIN ... PRIVATE KEY-----"))
        for kind, pattern in SECRET_SHAPES:
            for m in pattern.finditer(line):
                found.append((n, f"secret-shaped string: {kind}", m.group(0)[:8] + "..."))
        for m in EMAIL.finditer(line):
            if not _fake_domain(m.group(1)):
                found.append((n, "email address outside the fake-domain allow-list", m.group(0)))
    return found


def scan_repo() -> list[str]:
    report: list[str] = []
    for path in _files():
        data = path.read_bytes()
        if b"\0" in data[:8192]:
            continue  # binary
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in SELF_FIXTURES:
            continue
        for n, kind, excerpt in scan_text(data.decode("utf-8", errors="replace")):
            if (rel, kind) in ALLOWED:
                continue
            report.append(f"{rel}:{n}: {kind}: {excerpt}")
    return report


def test_the_repo_is_public_safe():
    findings = scan_repo()
    assert not findings, "public-safety findings:\n" + "\n".join(findings)


# --- the scanner itself: each rule catches what it claims to ----------------------------------------------


@pytest.mark.parametrize(
    "text, kind",
    [
        ("see /Users/jane/work/file.py", "local absolute path"),
        ("at /home/build/repo", "local absolute path"),
        (r"C:\Users\jane\Desktop", "local absolute path"),
        ("key = sk-abcdefghijklmnop1234", "OpenAI-style key"),
        ("token ghp_abcdefghijklmnopqrstuvwx", "GitHub token"),
        ("xoxb-1234567890-abcdefghij", "Slack token"),
        ("AKIAABCDEFGHIJKLMNOP", "AWS access key id"),
        ("Authorization: Bearer abcdefghijklmnopqrstuvwxyz0123", "bearer token"),
        ("-----BEGIN RSA PRIVATE KEY-----", "private key"),
        ("mail jane.doe@gmail.com", "email address"),
        ("pat-eu1-12345678-aaaa-bbbb-cccc-123456789012", "HubSpot private app token"),
    ],
)
def test_scanner_catches(text, kind):
    assert any(kind in k for _n, k, _e in scan_text(text)), text


@pytest.mark.parametrize(
    "text",
    [
        "jo@example.com and a@b.example.org and c@acme.test",
        "Authorization: Bearer <token>",
        "Authorization: Bearer ${TOKEN}",
        "uses /usr/local/bin and ~/projects and C:\\Program Files",
        "the sk- prefix is short here",
    ],
)
def test_scanner_leaves_alone(text):
    assert scan_text(text) == []


def test_every_allow_listed_finding_still_exists():
    """An allow-list entry for a finding that is gone hides nothing and misleads, so remove it."""
    live = set()
    for path in _files():
        data = path.read_bytes()
        if b"\0" in data[:8192]:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel not in SELF_FIXTURES:
            live |= {(rel, kind) for _n, kind, _x in scan_text(data.decode("utf-8", errors="replace"))}
    assert set(ALLOWED) <= live, set(ALLOWED) - live
