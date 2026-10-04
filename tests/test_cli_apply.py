"""crm_apply: dry run, gating, production confirmation, idempotency, stop on failure, the log."""

from __future__ import annotations

import io
import sys

import pytest

from tests.cli_helpers import behind_state, factory_for, make_plan_file, read_logs
from tools import crm_apply
from tools.design import load_design


@pytest.fixture
def design(write_design, design_dict):
    return load_design(write_design(design_dict))


def run(plan_path, adapter, tmp_path, *flags, env=None):
    argv = [str(plan_path), "--clients-dir", str(tmp_path / "clients"), *flags]
    return crm_apply.main(argv, adapter_factory=factory_for(adapter), env=env or {})


def test_plan_has_the_expected_mix(design, tmp_path):
    path, adapter = make_plan_file(design, tmp_path)
    plan = adapter.plan(design, adapter.read_state())
    assert sorted((c.kind, c.risk) for c in plan.changes) == [
        ("add_field", "safe"), ("add_option", "safe"), ("add_stage", "safe"),
        ("rename_field", "needs_review"),
    ]


def test_dry_run_is_the_default(design, tmp_path, capsys):
    path, adapter = make_plan_file(design, tmp_path)
    before = adapter.state
    assert run(path, adapter, tmp_path) == 0
    assert adapter.calls == [] and adapter.state == before
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "Would apply: 3" in out
    assert "Held for review (need --allow-review): 1" in out


def test_execute_applies_safe_and_holds_review(design, tmp_path, capsys):
    path, adapter = make_plan_file(design, tmp_path)
    assert run(path, adapter, tmp_path, "--execute", "--client", "acme") == 0
    assert sorted(c.kind for c in adapter.calls) == ["add_field", "add_option", "add_stage"]
    assert "Held for review (need --allow-review): 1" in capsys.readouterr().out


def test_allow_review_applies_review_changes(design, tmp_path):
    path, adapter = make_plan_file(design, tmp_path)
    assert run(path, adapter, tmp_path, "--execute", "--allow-review", "--client", "acme") == 0
    assert "rename_field" in [c.kind for c in adapter.calls]
    assert len(adapter.calls) == 4


def test_execute_needs_a_client_for_the_log(design, tmp_path, capsys):
    path, adapter = make_plan_file(design, tmp_path)
    assert run(path, adapter, tmp_path, "--execute") == 2
    assert adapter.calls == []
    assert "--client" in capsys.readouterr().err


def test_production_without_execute_is_refused(design, tmp_path, capsys):
    path, adapter = make_plan_file(design, tmp_path)
    assert run(path, adapter, tmp_path, "--production") == 2
    assert "--production needs --execute" in capsys.readouterr().err
    assert adapter.calls == []


class _Tty(io.StringIO):
    def isatty(self):
        return True


def test_production_needs_the_typed_name(design, tmp_path, monkeypatch, capsys):
    path, adapter = make_plan_file(design, tmp_path)
    monkeypatch.setattr(sys, "stdin", _Tty())
    monkeypatch.setattr("builtins.input", lambda prompt="": "wrong name")
    flags = ("--execute", "--production", "--client", "acme", "--target", "Acme Ltd")
    assert run(path, adapter, tmp_path, *flags) == 2
    assert adapter.calls == []
    assert "did not match" in capsys.readouterr().err


def test_production_runs_after_the_right_name(design, tmp_path, monkeypatch):
    path, adapter = make_plan_file(design, tmp_path)
    factory = factory_for(adapter)
    monkeypatch.setattr(sys, "stdin", _Tty())
    monkeypatch.setattr("builtins.input", lambda prompt="": "Acme Ltd")
    argv = [str(path), "--clients-dir", str(tmp_path / "clients"), "--execute", "--production",
            "--client", "acme", "--target", "Acme Ltd"]
    assert crm_apply.main(argv, adapter_factory=factory, env={}) == 0
    assert factory.calls == [("attio", "Acme Ltd", True)]
    assert len(adapter.calls) == 3


def test_production_refuses_without_a_terminal(design, tmp_path, monkeypatch):
    path, adapter = make_plan_file(design, tmp_path)
    monkeypatch.setattr(sys, "stdin", io.StringIO())
    monkeypatch.setattr("builtins.input", lambda prompt="": "sandbox")
    assert run(path, adapter, tmp_path, "--execute", "--production", "--client", "acme") == 2
    assert adapter.calls == []


def test_reapplying_the_same_plan_changes_nothing(design, tmp_path, capsys):
    path, adapter = make_plan_file(design, tmp_path)
    assert run(path, adapter, tmp_path, "--execute", "--allow-review", "--client", "acme") == 0
    first = len(adapter.calls)
    assert run(path, adapter, tmp_path, "--execute", "--allow-review", "--client", "acme") == 0
    # The additive changes are skipped. The rename is not judged without --design, so it is retried.
    assert len(adapter.calls) == first + 1 and adapter.calls[-1].kind == "rename_field"
    # With the design, every change is seen to be in place.
    assert run(path, adapter, tmp_path, "--execute", "--allow-review", "--client", "acme",
               "--design", str(design.source_path)) == 0
    assert len(adapter.calls) == first + 1
    assert adapter.plan(design, adapter.read_state()).changes == ()


def test_replan_after_apply_is_empty(design, tmp_path):
    path, adapter = make_plan_file(design, tmp_path)
    run(path, adapter, tmp_path, "--execute", "--allow-review", "--client", "acme")
    assert adapter.plan(design, adapter.read_state()).changes == ()


def test_skips_a_change_made_by_someone_else_meanwhile(design, tmp_path):
    path, adapter = make_plan_file(design, tmp_path)
    live = adapter.state
    # The field appears in the live CRM after the plan was made.
    adapter.state = behind_state(design)
    from tests.fake_adapter import state_matching
    full = state_matching(design)
    adapter.state = type(live)(
        live.platform, live.objects,
        live.fields + tuple(f for f in full.fields if f.key == "next_step_date"),
        live.relationships, live.pipelines,
    )
    run(path, adapter, tmp_path, "--execute", "--client", "acme")
    assert "add_field" not in [c.kind for c in adapter.calls]
    assert len(adapter.calls) == 2


def test_stops_at_the_first_failure_and_reports(design, tmp_path, capsys):
    path, adapter = make_plan_file(design, tmp_path)
    plan_targets = [c.target for c in adapter.plan(design, adapter.read_state()).changes if c.risk == "safe"]
    adapter.fail_on = plan_targets[1]
    assert run(path, adapter, tmp_path, "--execute", "--client", "acme") == 1
    assert [c.target for c in adapter.calls] == plan_targets[:1]
    out = capsys.readouterr().out
    assert "Failed: 1" in out and "400 bad request" in out
    assert "Remaining (not attempted): 1" in out
    log = read_logs(tmp_path / "clients", "acme")[0]
    assert [c["target"] for c in log["applied"]] == plan_targets[:1]
    assert log["failed"][0]["change"]["target"] == plan_targets[1]
    assert log["failed"][0]["error"] == "400 bad request"
    assert [c["target"] for c in log["remaining"]] == plan_targets[2:]


def test_log_is_written_and_redacted(design, tmp_path):
    path, adapter = make_plan_file(design, tmp_path)
    adapter.fail_on = next(c.target for c in adapter.plan(design, adapter.read_state()).changes if c.risk == "safe")
    secret = "hunter2-very-secret-value"
    env = {"ATTIO_API_KEY": secret}
    # The adapter's error echoes the credential and an email address.
    from dataclasses import replace
    original = adapter.apply

    def leaky(plan, *, dry_run=True):
        res = original(plan, dry_run=dry_run)
        if res.failed:
            f = res.failed[0]
            res = replace(res, failed=(replace(f, error=f"401 with {secret} for jo@example.com"),))
        return res

    adapter.apply = leaky  # type: ignore[method-assign]
    assert run(path, adapter, tmp_path, "--execute", "--client", "acme", env=env) == 1
    files = list((tmp_path / "clients" / "acme" / "build" / "apply-log").glob("*.json"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert secret not in text and "jo@example.com" not in text and "[redacted]" in text


def test_dry_run_with_client_still_logs(design, tmp_path):
    path, adapter = make_plan_file(design, tmp_path)
    run(path, adapter, tmp_path, "--client", "acme")
    (log,) = read_logs(tmp_path / "clients", "acme")
    assert log["executed"] is False and log["dry_run"] is True


def test_destructive_change_in_plan_is_refused(design, tmp_path, capsys):
    from dataclasses import replace
    path, adapter = make_plan_file(design, tmp_path)
    from tests.cli_helpers import load_plan
    plan = load_plan(path)
    bad = replace(plan.changes[0], risk="destructive")
    path.write_text(replace(plan, changes=(bad,) + plan.changes[1:]).to_json(), encoding="utf-8")
    assert run(path, adapter, tmp_path, "--execute", "--client", "acme") == 2
    assert adapter.calls == [] and "destructive" in capsys.readouterr().err


def test_unreadable_plan_is_an_error(tmp_path, design, capsys):
    _, adapter = make_plan_file(design, tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert run(bad, adapter, tmp_path) == 2
