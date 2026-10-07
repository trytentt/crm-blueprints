"""Safety gates, confirmation prompt and redaction."""

from __future__ import annotations

import io

import pytest

from tests.fake_adapter import FakeAdapter, state_matching
from tools.crm.base import Account, Change, Plan
from tools.crm.safety import (
    REDACTED,
    Mode,
    SafetyError,
    check_gates,
    confirm_live_account,
    confirm_production,
    get_credential,
    redact,
    redact_data,
    resolve_mode,
    write_apply_log,
)


def change(kind="add_field", risk="safe", target="deal.x"):
    return Change(kind, target, {}, risk, "", "s")


# --- modes -------------------------------------------------------------------------------------


def test_default_is_dry_run():
    m = resolve_mode(execute=False, production=False)
    assert m.dry_run and not m.production and not m.allow_review


def test_execute_sandbox():
    m = resolve_mode(execute=True, production=False)
    assert not m.dry_run and not m.production


def test_production_without_execute_is_refused():
    with pytest.raises(SafetyError, match="--execute"):
        resolve_mode(execute=False, production=True)


def test_execute_and_production():
    m = resolve_mode(execute=True, production=True, allow_review=True)
    assert not m.dry_run and m.production and m.allow_review


# --- gates -------------------------------------------------------------------------------------


def test_review_changes_held_without_allow_review():
    plan = Plan("attio", "sb", (change(), change("rename_field", "needs_review", "deal.y")))
    runnable, held = check_gates(plan, Mode(False, False, False))
    assert [c.kind for c in runnable] == ["add_field"]
    assert [c.kind for c in held] == ["rename_field"]


def test_review_changes_run_with_allow_review():
    plan = Plan("attio", "sb", (change(), change("rename_field", "needs_review")))
    runnable, held = check_gates(plan, Mode(False, False, True))
    assert len(runnable) == 2 and held == ()


def test_destructive_change_always_refused():
    plan = Plan("attio", "sb", (change("remove_field", "destructive"),))
    for mode in (Mode(True, False, True), Mode(False, False, True), Mode(False, True, True)):
        with pytest.raises(SafetyError, match="destructive"):
            check_gates(plan, mode)


LIVE = Account("Acme Live Ltd", "username build-user.live")


def test_production_confirmation_is_the_live_name_not_the_plan_target():
    seen = []
    plan = Plan("attio", "acme-sbx", (change(),), account=LIVE.identity)
    confirm_live_account(plan, LIVE, confirm=seen.append)
    assert seen == ["Acme Live Ltd"]  # never "acme-sbx"


def test_a_plan_made_for_another_account_is_refused_before_any_prompt():
    def boom(name):
        raise AssertionError("must not be asked")

    other = Plan("attio", "acme-sbx", (change(),), account=Account("Acme Sandbox", "username build-user.sandbox").identity)
    with pytest.raises(SafetyError, match="made for the account"):
        confirm_live_account(other, LIVE, confirm=boom)


def test_a_plan_with_no_stored_account_is_refused_for_production():
    with pytest.raises(SafetyError, match="no account identity"):
        confirm_live_account(Plan("attio", "p", (change(),)), LIVE, confirm=lambda n: None)


def test_production_refusal_stops_the_run():
    def refuse(name):
        raise SafetyError("no")

    with pytest.raises(SafetyError):
        confirm_live_account(Plan("attio", "p", (change(),), account=LIVE.identity), LIVE, confirm=refuse)


def test_default_confirmation_is_used_for_production(monkeypatch):
    monkeypatch.setattr(
        "tools.crm.safety.confirm_production", lambda name, detail="": (_ for _ in ()).throw(SafetyError(f"asked {name}"))
    )
    with pytest.raises(SafetyError, match="asked Acme Live Ltd"):
        confirm_live_account(Plan("attio", "p", (change(),), account=LIVE.identity), LIVE)


def test_confirmation_prompt_shows_the_live_details():
    out = io.StringIO()
    confirm_production("Acme Live Ltd", detail="username build-user.live", input_fn=lambda p: "Acme Live Ltd",
                       interactive=True, out=out)
    assert "Acme Live Ltd" in out.getvalue() and "username build-user.live" in out.getvalue()


# --- confirmation prompt -----------------------------------------------------------------------


def test_confirm_accepts_exact_name():
    confirm_production("Acme Ltd", input_fn=lambda prompt: "Acme Ltd", interactive=True, out=io.StringIO())


def test_confirm_strips_whitespace():
    confirm_production("Acme Ltd", input_fn=lambda p: "  Acme Ltd \n", interactive=True, out=io.StringIO())


@pytest.mark.parametrize("answer", ["", "acme ltd", "yes", "Acme", "y"])
def test_confirm_rejects_wrong_answer(answer):
    with pytest.raises(SafetyError, match="did not match"):
        confirm_production("Acme Ltd", input_fn=lambda p: answer, interactive=True, out=io.StringIO())


def test_confirm_refuses_non_interactive():
    with pytest.raises(SafetyError, match="interactive"):
        confirm_production("Acme Ltd", input_fn=lambda p: "Acme Ltd", interactive=False, out=io.StringIO())


def test_confirm_needs_a_name():
    with pytest.raises(SafetyError, match="account or org name"):
        confirm_production("  ", input_fn=lambda p: "", interactive=True, out=io.StringIO())


def test_confirm_prompt_names_the_account():
    prompts = []
    confirm_production("Acme Ltd", input_fn=lambda p: prompts.append(p) or "Acme Ltd", interactive=True, out=io.StringIO())
    assert "Acme Ltd" in prompts[0]


# --- adapter flow with the fake ----------------------------------------------------------------


def test_fake_adapter_dry_run_applies_nothing(write_design, design_dict):
    from tools.design import load_design
    from dataclasses import replace

    design = load_design(write_design(design_dict))
    s = state_matching(design)
    s = replace(s, fields=tuple(f for f in s.fields if f.key != "next_step_date"))
    adapter = FakeAdapter(s)
    plan = adapter.plan(design, s)
    result = adapter.apply(plan)  # dry run by default
    assert result.dry_run and result.applied == () and len(result.remaining) == 1
    assert adapter.calls == []


def test_fake_adapter_stops_on_first_failure(write_design, design_dict):
    from tools.design import load_design
    from dataclasses import replace

    design = load_design(write_design(design_dict))
    s = state_matching(design)
    s = replace(s, fields=tuple(f for f in s.fields if f.native))
    adapter = FakeAdapter(s, fail_on="deal.next_step_date")
    plan = adapter.plan(design, s)
    result = adapter.apply(plan, dry_run=False)
    assert not result.ok
    assert result.failed[0].change.target == "deal.next_step_date"
    assert result.failed[0].error == "400 bad request"
    assert len(result.applied) + 1 + len(result.remaining) == len(plan.changes)


# --- redaction ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,secret",
    [
        ("Authorization: Bearer abcDEF123456789xyz", "abcDEF123456789xyz"),
        ("token=sk-live-1234567890abcdef", "1234567890abcdef"),
        ("api_key: 'abc123def456ghi'", "abc123def456ghi"),
        ("using pat-eu1-12345678-aaaa-bbbb-cccc-1234567890ab for hubspot", "12345678-aaaa"),
        ("password=hunter2hunter2", "hunter2hunter2"),
        ("sid 00D5g000001AbcD!AQEAQabcdefghijklmnopqrstuvwxyz0123456789", "AQEAQabcdefghijklmnop"),
        ("Contact jane.doe+crm@example.co.uk about it", "jane.doe"),
        ("call +44 7700 900123 now", "7700 900123"),
        ("call 07700 900123 now", "07700 900123"),
        ("call (020) 7946 0958 now", "7946 0958"),
        ("call (415) 555-0100 now", "555-0100"),
    ],
)
def test_redact_removes_sensitive_text(text, secret):
    out = redact(text)
    assert secret not in out
    assert REDACTED in out


def test_redact_keeps_harmless_text():
    text = "Added field deal.lost_reason on 2026-10-04 with 12 options (id 4521)."
    assert redact(text) == text


def test_redact_known_secret_values():
    out = redact("request failed for xyz987", secrets=["xyz987"])
    assert "xyz987" not in out


def test_redact_ignores_empty_and_tiny_secrets():
    assert redact("a b c", secrets=["", "a"]) == "a b c"


def test_redact_data_nested():
    data = {
        "headers": {"Authorization": "Bearer abcdef123456", "Accept": "json"},
        "body": {"email": "a@example.com", "items": ["call 07700 900123", 5]},
        "api_key": "whatever",
    }
    out = redact_data(data)
    assert out["headers"]["Authorization"] == REDACTED
    assert out["headers"]["Accept"] == "json"
    assert out["body"]["email"] == REDACTED
    assert out["body"]["items"] == ["call " + REDACTED, 5]
    assert out["api_key"] == REDACTED


def test_write_apply_log_redacts(tmp_path):
    path = write_apply_log(tmp_path / "build" / "apply-log", "run.log", "user a@example.com token=secret123456")
    text = path.read_text()
    assert "a@example.com" not in text and "secret123456" not in text


def test_get_credential():
    assert get_credential("TOKEN_X", {"TOKEN_X": "v"}) == "v"
    with pytest.raises(SafetyError) as exc:
        get_credential("TOKEN_X", {})
    assert "TOKEN_X" in str(exc.value)
