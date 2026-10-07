"""Records and the adapter interface shared by every platform.

`State` is a platform's live structure in canonical terms, so it can be compared with a `Design`.
Adapters translate their API responses into `State` (matching live names back to design keys) and
translate `Change` payloads into API calls. Diffing and safety rules live in `planner` and `safety`.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any

from tools.design import Design

RISKS = ("safe", "needs_review", "destructive")


@dataclass(frozen=True)
class StateObject:
    """A live object. `native` marks platform built-ins, which the planner never proposes removing."""

    key: str
    label: str = ""
    native: bool = False


@dataclass(frozen=True)
class StateField:
    """A live field. `options` holds option keys and labels as (key, label) pairs."""

    object: str
    key: str
    type: str
    label: str = ""
    options: tuple[tuple[str, str], ...] = ()
    native: bool = False


@dataclass(frozen=True)
class StateRelationship:
    """A live link between two objects."""

    key: str
    from_object: str
    to_object: str
    cardinality: str
    native: bool = False


@dataclass(frozen=True)
class StateStage:
    """A live pipeline stage. `probability` is None where the platform does not expose one."""

    key: str
    label: str = ""
    type: str = "open"
    probability: float | None = None


@dataclass(frozen=True)
class StatePipeline:
    """A live pipeline with its stages in platform order."""

    object: str
    key: str
    name: str = ""
    stages: tuple[StateStage, ...] = ()


@dataclass(frozen=True)
class State:
    """The live structure of one CRM account, in canonical terms."""

    platform: str
    objects: tuple[StateObject, ...] = ()
    fields: tuple[StateField, ...] = ()
    relationships: tuple[StateRelationship, ...] = ()
    pipelines: tuple[StatePipeline, ...] = ()


@dataclass(frozen=True)
class Change:
    """One automatic change. `risk` is safe, needs_review or destructive."""

    kind: str
    target: str
    payload: dict[str, Any]
    risk: str
    source_url: str
    summary: str


@dataclass(frozen=True)
class ManualStep:
    """Something a person must do. Destructive removals carry data-migration `instructions`."""

    title: str
    reason: str
    ui_path: str
    done_when: str
    risk: str = "safe"
    instructions: str = ""
    # True when the step stands for a difference between the design and the live account that this tool could
    # not close itself (an edition without a deploy API, a rename). `crm_drift` counts these; routine hand work
    # such as building a flow is not drift.
    drift: bool = False


@dataclass(frozen=True)
class Plan:
    """Ordered changes and manual steps for one platform and target (sandbox or org name)."""

    platform: str
    target: str
    changes: tuple[Change, ...] = ()
    manual_steps: tuple[ManualStep, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Plain dict, safe for JSON."""
        return {
            "platform": self.platform,
            "target": self.target,
            "changes": [asdict(c) for c in self.changes],
            "manual_steps": [asdict(m) for m in self.manual_steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Plan":
        """Rebuild a plan from `to_dict` output."""
        return cls(
            platform=data["platform"],
            target=data["target"],
            changes=tuple(Change(**c) for c in data.get("changes", [])),
            manual_steps=tuple(ManualStep(**m) for m in data.get("manual_steps", [])),
        )

    def to_json(self) -> str:
        """Stable JSON: indent 2, fixed key order, trailing newline."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "Plan":
        """Rebuild a plan from `to_json` output."""
        return cls.from_dict(json.loads(text))

    @property
    def is_empty(self) -> bool:
        """True when there is nothing to change and nothing for a person to do."""
        return not self.changes and not self.manual_steps


@dataclass(frozen=True)
class Failure:
    """A change that failed, with the API error (already redacted by the adapter)."""

    change: Change
    error: str


@dataclass(frozen=True)
class Result:
    """Outcome of an apply: what went in, what failed, and what was left.

    The apply stops on the first failure, so `failed` has at most one entry.
    """

    applied: tuple[Change, ...] = ()
    failed: tuple[Failure, ...] = ()
    remaining: tuple[Change, ...] = ()
    dry_run: bool = True

    @property
    def ok(self) -> bool:
        """True when nothing failed."""
        return not self.failed


class Adapter(ABC):
    """One platform. Subclasses supply API calls; the planner and safety modules do the rest."""

    platform: str = ""

    @abstractmethod
    def read_state(self) -> State:
        """Read live objects, fields, relationships and pipelines."""

    @abstractmethod
    def plan(self, design: Design, state: State) -> Plan:
        """Diff the design against live state. Normally calls `tools.crm.planner.plan_changes`."""

    @abstractmethod
    def apply(self, plan: Plan, *, dry_run: bool = True) -> Result:
        """Apply a plan. Dry run by default; stop on the first failure."""
