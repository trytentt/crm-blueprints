"""State to and from plain dicts and JSON, for `crm_pull --out`."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from tools.crm.base import (
    State,
    StateField,
    StateObject,
    StatePipeline,
    StateRelationship,
    StateStage,
)


def state_to_json(state: State) -> str:
    """Stable JSON: indent 2, trailing newline."""
    return json.dumps(asdict(state), indent=2, ensure_ascii=False) + "\n"


def state_from_dict(data: dict[str, Any]) -> State:
    """Rebuild a State from `asdict` output."""
    return State(
        platform=data["platform"],
        objects=tuple(StateObject(**o) for o in data.get("objects", [])),
        fields=tuple(
            StateField(**{**f, "options": tuple(tuple(o) for o in f.get("options", []))})
            for f in data.get("fields", [])
        ),
        relationships=tuple(StateRelationship(**r) for r in data.get("relationships", [])),
        pipelines=tuple(
            StatePipeline(
                **{**p, "stages": tuple(StateStage(**s) for s in p.get("stages", []))}
            )
            for p in data.get("pipelines", [])
        ),
    )


def state_from_json(text: str) -> State:
    """Rebuild a State from `state_to_json` output."""
    return state_from_dict(json.loads(text))
