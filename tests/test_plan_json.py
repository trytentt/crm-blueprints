"""Plan JSON round-trip."""

from __future__ import annotations

import json

from tools.crm.base import Change, ManualStep, Plan, Result


def sample() -> Plan:
    return Plan(
        platform="hubspot",
        target="sandbox-123",
        changes=(
            Change("add_field", "deal.x", {"name": "x", "options": [{"a": 1}], "n": None}, "safe", "https://e.test", "Add x"),
            Change("rename_field", "deal.y", {}, "needs_review", "", "Rename y"),
        ),
        manual_steps=(
            ManualStep("Remove z", "Never deleted", "Settings", "Gone", "destructive", "1. Export."),
            ManualStep("Build flow", "No API", "Automations", "Runs"),
        ),
    )


def test_round_trip_equal():
    plan = sample()
    assert Plan.from_json(plan.to_json()) == plan


def test_json_is_stable_and_valid():
    text = sample().to_json()
    assert text.endswith("\n") and text == sample().to_json()
    data = json.loads(text)
    assert list(data) == ["platform", "target", "changes", "manual_steps"]
    assert data["changes"][0]["risk"] == "safe"


def test_empty_plan_round_trips():
    assert Plan.from_json(Plan("attio", "t").to_json()) == Plan("attio", "t")


def test_result_ok():
    assert Result().ok
