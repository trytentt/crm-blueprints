"""crm_pull, crm_plan and crm_drift: read-only tools, exit codes, draft design."""

from __future__ import annotations

import json

import pytest
import yaml

from tests.cli_helpers import behind_state, factory_for
from tests.fake_adapter import StatefulFakeAdapter, state_matching
from tools import crm_drift, crm_plan, crm_pull
from tools.crm.state_io import state_from_json
from tools.design import load_design
from tools.validate import validate_design


@pytest.fixture
def design(write_design, design_dict):
    return load_design(write_design(design_dict))


def test_plan_prints_by_risk_saves_json_and_never_applies(design, tmp_path, capsys):
    adapter = StatefulFakeAdapter(behind_state(design))
    out = tmp_path / "plan.json"
    rc = crm_plan.main(
        [str(design.source_path), "--platform", "attio", "--out", str(out)],
        adapter_factory=factory_for(adapter), env={},
    )
    assert rc == 0 and adapter.calls == []
    text = capsys.readouterr().out
    assert text.index("SAFE") < text.index("NEEDS REVIEW")
    assert "[add_field]" in text and "Nothing was changed" in text
    assert json.loads(out.read_text())["platform"] == "attio"


def test_plan_lists_manual_steps(design, tmp_path, capsys):
    state = state_matching(design)
    from dataclasses import replace
    state = replace(state, fields=state.fields + (
        __import__("tools.crm.base", fromlist=["StateField"]).StateField("deal", "extra", "text", "Extra"),
    ))
    adapter = StatefulFakeAdapter(state)
    crm_plan.main([str(design.source_path), "--platform", "attio"],
                  adapter_factory=factory_for(adapter), env={})
    text = capsys.readouterr().out
    assert "MANUAL STEPS" in text and "[DESTRUCTIVE] Remove field deal.extra" in text


def test_plan_reports_missing_adapter_cleanly(design, capsys):
    rc = crm_plan.main([str(design.source_path), "--platform", "salesforce"], env={})
    # Either the adapter module exists and lacks credentials, or it does not exist yet.
    assert rc == 2 and "error:" in capsys.readouterr().err


def test_drift_exit_codes(design, capsys):
    clean = StatefulFakeAdapter(state_matching(design))
    assert crm_drift.main([str(design.source_path), "--platform", "attio"],
                          adapter_factory=factory_for(clean), env={}) == 0
    assert "No drift" in capsys.readouterr().out
    behind = StatefulFakeAdapter(behind_state(design))
    assert crm_drift.main([str(design.source_path), "--platform", "attio"],
                          adapter_factory=factory_for(behind), env={}) == 1
    assert "add_field" in capsys.readouterr().out


def test_drift_reports_extras_in_live(design, capsys):
    from dataclasses import replace
    from tools.crm.base import StateField
    state = state_matching(design)
    state = replace(state, fields=state.fields + (StateField("deal", "extra", "text", "Extra"),))
    rc = crm_drift.main([str(design.source_path), "--platform", "attio"],
                        adapter_factory=factory_for(StatefulFakeAdapter(state)), env={})
    assert rc == 1
    assert "deal.extra" in capsys.readouterr().out


def test_drift_counts_a_manual_step_that_stands_for_a_difference(design):
    """Regression: on an edition with no deploy API every change is a manual step, and an unbuilt org is not 'no drift'."""
    from tools.crm.base import ManualStep, Plan
    from tools.crm_drift import drift_plan
    gap = ManualStep("Add field", "cannot deploy here", "UI", "exists", drift=True)
    routine = ManualStep("Build flow", "no API", "UI", "runs")
    assert drift_plan(Plan("salesforce", "t", (), (routine, gap))).manual_steps == (gap,)
    assert Plan.from_json(Plan("salesforce", "t", (), (gap,)).to_json()).manual_steps == (gap,)


def test_drift_ignores_safe_manual_steps(design):
    from tools.crm.base import ManualStep, Plan
    from tools.crm_drift import drift_plan
    plan = Plan("attio", "t", (), (ManualStep("Build flow", "no API", "UI", "runs"),))
    assert drift_plan(plan).is_empty


def test_pull_writes_state_json(design, tmp_path):
    adapter = StatefulFakeAdapter(state_matching(design))
    out = tmp_path / "state.json"
    assert crm_pull.main(["--platform", "attio", "--out", str(out)],
                         adapter_factory=factory_for(adapter), env={}) == 0
    assert state_from_json(out.read_text()) == adapter.state


def test_pull_needs_an_output(capsys):
    with pytest.raises(SystemExit):
        crm_pull.main(["--platform", "attio"], env={})


def test_to_design_writes_a_draft_that_fails_validation(design, tmp_path):
    from tests.fake_adapter import state_matching
    adapter = StatefulFakeAdapter(state_matching(design))
    out = tmp_path / "draft.yaml"
    assert crm_pull.main(["--platform", "attio", "--to-design", str(out)],
                         adapter_factory=factory_for(adapter), env={}) == 0
    text = out.read_text()
    assert text.startswith("# DRAFT") and "TODO" in text
    data = yaml.safe_load(text)
    assert data["name"].startswith("DRAFT")
    assert {o["key"] for o in data["add_objects"]} == {"project"}
    assert {(f["object"], f["key"]) for f in data["add_fields"]} == {
        ("deal", "lost_reason"), ("deal", "next_step_date"), ("project", "status")}
    draft = load_design(out)  # it loads...
    issues = validate_design(draft)
    assert any(i.severity == "error" and "TODO" in i.message for i in issues)
    assert any(i.severity == "error" for i in issues)
