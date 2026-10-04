"""Turn a Design into the State a perfect build of it would have.

Used by `diff_design` (the old design stands in for live state) and by test fakes.
"""

from __future__ import annotations

from tools.crm.base import (
    State,
    StateField,
    StateObject,
    StatePipeline,
    StateRelationship,
    StateStage,
)
from tools.design import Design


def state_from_design(design: Design, platform: str = "design") -> State:
    """Build the State that matches `design`. Core objects and fields native to `platform` are native."""
    objects = tuple(StateObject(o.key, o.label, native=o.kind == "core") for o in design.objects)
    fields = tuple(
        StateField(
            f.object, f.key, f.type, f.label,
            options=tuple((o.key, o.label) for o in f.options),
            native=platform in f.native,
        )
        for f in design.fields
    )
    rels = tuple(
        StateRelationship(r.key, r.from_object, r.to_object, r.cardinality, native=platform in r.native)
        for r in design.relationships
    )
    pipes = tuple(
        StatePipeline(
            p.object, p.key, p.name,
            tuple(StateStage(s.key, s.label, s.type, s.probability) for s in p.stages),
        )
        for p in design.pipelines
    )
    return State(platform, objects, fields, rels, pipes)
