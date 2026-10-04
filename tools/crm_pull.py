"""Read the live state of a CRM into JSON, or into a draft design.

    uv run python -m tools.crm_pull --platform hubspot --out state.json
    uv run python -m tools.crm_pull --platform attio --to-design draft-design.yaml

Read-only. `--to-design` writes a DRAFT: every description is a TODO, so it fails
`tools.validate` until a person writes what each field is for.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping

if __name__ == "__main__":  # pragma: no cover - allow `python tools/crm_pull.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from tools.cli_common import AdapterFactory, add_platform_args, default_factory, load_env
from tools.crm.base import State
from tools.crm.registry import RegistryError
from tools.crm.safety import SafetyError, redact
from tools.crm.state_io import state_to_json
from tools.design import load_core_model

TODO = "TODO: say what this is used for"


def draft_design(state: State) -> str:
    """Build a draft design.yaml (text) from live state. Core objects, fields and links are left to `extends`."""
    core = load_core_model()
    core_objects = {o.key for o in core.objects}
    core_fields = {(f.object, f.key) for f in core.fields}
    core_rels = {r.key for r in core.relationships}

    objects = [
        {"key": o.key, "label": o.label or o.key, "description": TODO}
        for o in state.objects
        if not o.native and o.key not in core_objects
    ]
    fields: list[dict[str, Any]] = []
    for f in state.fields:
        if f.native or (f.object, f.key) in core_fields:
            continue
        item: dict[str, Any] = {
            "object": f.object, "key": f.key, "label": f.label or f.key, "type": f.type,
            "description": TODO,
        }
        if f.options:
            item["options"] = {k: label or k for k, label in f.options}
        fields.append(item)
    rels = [
        {
            "key": r.key, "from": r.from_object, "to": r.to_object, "cardinality": r.cardinality,
            "from_label": "TODO", "to_label": "TODO", "purpose": TODO,
        }
        for r in state.relationships
        if not r.native and r.key not in core_rels
    ]
    pipelines = [
        {
            "object": p.object, "key": p.key, "name": p.name or p.key,
            "stages": [
                {
                    "key": s.key, "label": s.label or s.key, "type": s.type,
                    "probability": s.probability if s.probability is not None else 0,
                    "exit_criteria": "TODO: write as 'Entered when ...'",
                }
                for s in p.stages
            ],
        }
        for p in state.pipelines
    ]
    body: dict[str, Any] = {
        "extends": "core",
        "name": f"DRAFT from live {state.platform}",
        "description": "DRAFT: read from a live CRM. Fill in every TODO before validating.",
    }
    for key, value in (
        ("add_objects", objects), ("add_fields", fields),
        ("add_relationships", rels), ("pipelines", pipelines),
    ):
        if value:
            body[key] = value
    header = (
        "# DRAFT design read from a live CRM. It will not validate until a person:\n"
        "#   - replaces every TODO (descriptions, labels, exit criteria),\n"
        "#   - adds decisions, automations and views,\n"
        "#   - checks probabilities (the platform may not expose them) and field types.\n"
        "# Nothing here has been reviewed.\n"
    )
    return header + yaml.safe_dump(body, sort_keys=False, allow_unicode=True, width=100)


def main(
    argv: list[str] | None = None,
    *,
    adapter_factory: AdapterFactory | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    """CLI entry point. Returns the exit code."""
    parser = argparse.ArgumentParser(prog="crm_pull", description=__doc__.split("\n")[0])
    add_platform_args(parser)
    parser.add_argument("--out", type=Path, help="write the live state as JSON to this file")
    parser.add_argument("--to-design", type=Path, metavar="FILE", help="write a DRAFT design.yaml here")
    args = parser.parse_args(argv)
    if not args.out and not args.to_design:
        parser.error("give --out and/or --to-design")
    environment = env if env is not None else load_env()
    try:
        adapter = (adapter_factory or default_factory)(args.platform, environment, args.target, False)
        state = adapter.read_state()
    except (RegistryError, SafetyError) as exc:
        print(f"error: {redact(str(exc))}", file=sys.stderr)
        return 2
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(state_to_json(state), encoding="utf-8")
        print(f"Wrote live state to {args.out}")
    if args.to_design:
        args.to_design.parent.mkdir(parents=True, exist_ok=True)
        args.to_design.write_text(draft_design(state), encoding="utf-8")
        print(f"Wrote DRAFT design to {args.to_design}. Fill in the TODOs before validating.")
    print(
        f"{len(state.objects)} objects, {len(state.fields)} fields, "
        f"{len(state.relationships)} relationships, {len(state.pipelines)} pipelines."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
