"""Shared test helpers: a minimal design that passes --strict, and a way to write variants."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml


def base_design() -> dict[str, Any]:
    """A small design with zero errors and zero warnings."""
    return {
        "extends": "core",
        "name": "Test design",
        "description": "A design used by the tests.",
        "add_objects": [
            {
                "key": "project",
                "label": "Project",
                "plural_label": "Projects",
                "description": "Delivery work after the sale.",
            }
        ],
        "add_fields": [
            {
                "object": "deal",
                "key": "lost_reason",
                "label": "Lost reason",
                "type": "select",
                "description": "Why the deal was lost.",
                "options": {"price": "Price", "timing": "Timing"},
            },
            {
                "object": "project",
                "key": "status",
                "label": "Status",
                "type": "select",
                "description": "Project status.",
                "options": ["not_started", "live"],
            },
            {
                "object": "deal",
                "key": "next_step_date",
                "label": "Next step date",
                "type": "date",
                "description": "When the next step is due.",
            },
        ],
        "add_relationships": [
            {
                "key": "project_company",
                "from": "project",
                "to": "company",
                "cardinality": "many_to_one",
                "from_label": "Company",
                "to_label": "Projects",
                "purpose": "Shows projects per customer.",
            }
        ],
        "pipelines": [
            {
                "object": "deal",
                "key": "sales",
                "name": "Sales",
                "stages": [
                    {
                        "key": "discovery",
                        "label": "Discovery",
                        "type": "open",
                        "probability": 20,
                        "exit_criteria": "Entered when a call has happened.",
                        "required_fields": ["next_step_date"],
                    },
                    {
                        "key": "won",
                        "label": "Won",
                        "type": "won",
                        "probability": 100,
                        "exit_criteria": "Entered when the contract is signed.",
                    },
                    {
                        "key": "lost",
                        "label": "Lost",
                        "type": "lost",
                        "probability": 0,
                        "exit_criteria": "Entered when the buyer says no.",
                        "required_fields": ["lost_reason"],
                    },
                ],
            }
        ],
        "decisions": [
            {"key": f"d{i}", "question": f"Question {i}?", "recommended_default": "Yes."}
            for i in range(3)
        ],
        "automations": [
            {"key": f"a{i}", "name": f"Auto {i}", "trigger": "When x.", "action": "Do y."}
            for i in range(3)
        ],
        "views": [
            {"key": f"v{i}", "name": f"View {i}", "object": "deal", "filter": "All.", "sort": "Name."}
            for i in range(3)
        ],
    }


@pytest.fixture
def design_dict() -> dict[str, Any]:
    """A fresh copy of the passing base design for a test to mutate."""
    return copy.deepcopy(base_design())


@pytest.fixture
def write_design(tmp_path: Path) -> Callable[[dict[str, Any], str], Path]:
    """Write a design dict to a temporary design.yaml and return its path."""

    def _write(data: dict[str, Any], name: str = "design.yaml") -> Path:
        path = tmp_path / name
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return path

    return _write
