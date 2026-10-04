"""Attio adapter: read a workspace, diff it against a design, apply the difference.

Entry point: `make_adapter(env, *, target, production)`. Credentials come from the environment:
`ATTIO_ACCESS_TOKEN` (required) and `ATTIO_TARGET` (a label that says "this is a test workspace").

Attio has no sandbox. Any workspace is treated as production unless `ATTIO_TARGET` is set and the
caller did not pass `production`. A production apply needs the typed confirmation, and the name
shown is the workspace name returned by `GET /v2/self`.

Facts come from `platforms/attio/reference/`, which was read from Attio's OpenAPI spec
(https://api.attio.com/openapi/api).

Review and production gating is done by `tools/crm_apply.py` (D-14), which passes cleared changes
one at a time. The adapter checks that the plan's target is the token's workspace.

Rules kept here, on top of `tools.crm.planner` and `tools.crm.safety`:

- No DELETE is ever sent. The request helper refuses the method. Removing an option or stage is a
  `needs_review` change done by `PATCH is_archived` (D-8).
- `apply` is a dry run unless asked. A dry run makes no HTTP call at all.
- Before each request the target is read again and the request is skipped when already satisfied.
- 409 `slug_conflict` is "already exists": the adapter reads the item and checks it.
- 429 is retried with `Retry-After`, up to five times. Any other error stops the run.
- The token is never logged or put in an error.

Limits of the mapping back to design keys (Attio keeps no keys of its own):

- Stage and option keys are recovered from titles. A title that was changed in Attio shows up as a
  new stage or option plus an archive, not as a rename, unless it slugifies to the design key.
- Attio has no stage type or probability. A stage is "won" if its celebration flag is on. Otherwise
  its type is taken from the design, so the type cannot drift in a way the tool can see.
- Lists that have no `stage` status attribute are not pipelines and are ignored.
"""

from __future__ import annotations

import email.utils
import json
import re
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

import requests

from tools.crm.base import (
    Adapter,
    Change,
    Failure,
    ManualStep,
    Plan,
    Result,
    State,
    StateField,
    StateObject,
    StatePipeline,
    StateRelationship,
    StateStage,
)
from tools.crm.planner import plan_changes
from tools.crm.safety import Mode, SafetyError, get_credential, redact
from tools.design import Design, FieldDef, Pipeline, RelationshipDef, Stage
from tools.generators import attio as gen

PLATFORM = "attio"
BASE_URL = "https://api.attio.com"
SRC_SELF = "https://docs.attio.com/rest-api/endpoint-reference/meta/identify.md"
SRC_OPENAPI = gen.SRC_OPENAPI
SRC_UPDATE_OBJECT = "https://docs.attio.com/rest-api/endpoint-reference/objects/update-an-object.md"
SRC_UPDATE_ATTRIBUTE = "https://docs.attio.com/rest-api/endpoint-reference/attributes/update-an-attribute.md"
SRC_LIST_OBJECTS = "https://docs.attio.com/rest-api/endpoint-reference/objects/list-objects.md"
SRC_CREATE_OPTION = "https://docs.attio.com/rest-api/endpoint-reference/attributes/create-a-select-option.md"
SRC_CREATE_STATUS = "https://docs.attio.com/rest-api/endpoint-reference/attributes/create-a-status.md"
SRC_RATE_LIMITS = "https://docs.attio.com/rest-api/guides/rate-limiting.md"

# Methods the adapter may send. DELETE is deliberately absent (safety rule 3).
ALLOWED_METHODS = frozenset({"GET", "POST", "PATCH"})
NATIVE_OBJECTS = frozenset({"people", "companies", "deals", "users", "workspaces"})
MAX_RETRIES_429 = 5
MAX_RETRIES_5XX_READ = 3
BACKOFF_SECONDS = (1, 2, 4, 8, 16)
MAX_WAIT_SECONDS = 60.0
PAGE_SIZE = 100
MAX_PAGES = 50
TIMEOUT_SECONDS = 30

SOURCE_URLS: dict[str, str] = {
    "add_object": gen.SRC_CREATE_OBJECT,
    "rename_object": SRC_UPDATE_OBJECT,
    "add_relationship": gen.SRC_RECORD_REFERENCE,
    "add_pipeline": gen.SRC_CREATE_LIST,
    "add_stage": SRC_CREATE_STATUS,
    "rename_stage": SRC_OPENAPI,
    "update_stage": SRC_OPENAPI,
    "remove_stage": SRC_OPENAPI,
    "reorder_stages": SRC_OPENAPI,
    "add_field": gen.SRC_CREATE_ATTRIBUTE,
    "rename_field": SRC_UPDATE_ATTRIBUTE,
    "add_option": SRC_CREATE_OPTION,
    "rename_option": SRC_OPENAPI,
    "remove_option": SRC_OPENAPI,
}

UI_PATHS: dict[str, str] = {
    "remove_object": "Workspace settings, then Objects, then the object, then delete it (custom objects only).",
    "remove_field": "Workspace settings, then Objects, then the object, then Attributes, then archive the attribute.",
    "change_field_type": "Workspace settings, then Objects, then the object, then Attributes, then New attribute.",
    "remove_relationship": "Workspace settings, then Objects, then the object, then Attributes, then archive the attribute.",
    "change_relationship": "Workspace settings, then Objects, then the object, then Attributes, then New attribute.",
    "remove_pipeline": "Lists in the left sidebar, then the list, then List settings.",
}

# Attio type and multiselect flag back to the canonical type.
REVERSE_TYPES: dict[tuple[str, bool], str] = {
    ("text", False): "text",
    ("number", False): "number",
    ("select", False): "select",
    ("select", True): "multi_select",
    ("currency", False): "currency",
    ("date", False): "date",
    ("timestamp", False): "datetime",
    ("checkbox", False): "checkbox",
    ("email-address", False): "email",
    ("phone-number", False): "phone",
    ("actor-reference", False): "user",
}


class AttioApiError(RuntimeError):
    """An Attio API error. `body` is the parsed error body, kept for the failure report."""

    def __init__(self, status: int, code: str, message: str, body: Any = None, error_type: str = "") -> None:
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code
        self.message = message
        self.body = body
        self.error_type = error_type


@dataclass(frozen=True)
class Workspace:
    """Who a token belongs to, from `GET /v2/self`."""

    name: str
    slug: str
    workspace_id: str = ""
    scopes: tuple[str, ...] = ()


@dataclass
class Snapshot:
    """Raw API data from one read. Archived items are kept so the state builder can tell them apart."""

    objects: list[dict[str, Any]] = field(default_factory=list)
    attributes: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    options: dict[tuple[str, str, str], list[dict[str, Any]]] = field(default_factory=dict)
    lists: list[dict[str, Any]] = field(default_factory=list)
    list_attributes: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    statuses: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


# --- helpers ---------------------------------------------------------------------------------


def parse_retry_after(value: str | None, *, now: datetime | None = None) -> float | None:
    """Seconds to wait from a `Retry-After` header: a number of seconds or an HTTP date.

    Source: https://docs.attio.com/rest-api/guides/rate-limiting.md (the docs call it a datetime;
    both forms are accepted, open question Q13). Returns None when absent or unreadable.
    """
    if not value:
        return None
    text = value.strip()
    try:
        return max(0.0, float(text))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            when = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return max(0.0, (when - current).total_seconds())


def _id_of(item: Mapping[str, Any], key: str) -> str:
    ident = item.get("id")
    return str(ident.get(key, "")) if isinstance(ident, Mapping) else ""


def _slugify(text: str) -> str:
    return gen._slugify(text)


def _reverse_type(attr: Mapping[str, Any]) -> str:
    attio_type = str(attr.get("type", ""))
    return REVERSE_TYPES.get((attio_type, bool(attr.get("is_multiselect"))), attio_type)


def _type_matches(attr: Mapping[str, Any], canonical: str) -> bool:
    mapped = gen.TYPE_MAP.get(canonical)
    return mapped is not None and mapped == (attr.get("type"), bool(attr.get("is_multiselect")))


def _cardinality(parent_multi: bool, reverse_multi: bool) -> str:
    """Cardinality from the two `is_multiselect` flags (relationships.md table)."""
    if parent_multi and reverse_multi:
        return "many_to_many"
    if parent_multi:
        return "one_to_many"
    if reverse_multi:
        return "many_to_one"
    return "one_to_one"


def _field_slug(design: Design, f: FieldDef) -> str:
    """The live slug of a design field, following the generator's rules."""
    if gen.PLATFORM in f.native:
        return f.native_names.get(gen.PLATFORM, gen.field_slug(design, f))
    if gen._is_object_name_field(design, f):
        return "name"
    return gen.field_slug(design, f)


def _option_key(title: str, options: tuple[Any, ...]) -> str:
    """Recover an option key from its title: exact label, then a slug that equals a design key."""
    for opt in options:
        if opt.label == title:
            return opt.key
    slug = _slugify(title)
    for opt in options:
        if opt.key == slug:
            return opt.key
    return slug


def _stage_key(title: str, pipeline: Pipeline | None) -> str:
    return _option_key(title, tuple(pipeline.stages) if pipeline else ())


# --- raw snapshot to canonical state ---------------------------------------------------------


def build_state(snap: Snapshot, design: Design | None) -> tuple[State, dict[tuple[str, ...], str]]:
    """Map a raw snapshot to a canonical `State`, plus the live ids needed to PATCH items later.

    With a design, object, field, option and stage keys are the design's. Without one, keys are the
    Attio slugs and slugified titles. `ids` maps ("option", object_slug, attribute_slug, key) and
    ("status", list_slug, key) to the live id.
    """
    ids: dict[tuple[str, ...], str] = {}
    obj_key: dict[str, str] = {}
    fields_by_slug: dict[tuple[str, str], list[FieldDef]] = {}
    if design is not None:
        for o in design.objects:
            obj_key[gen.object_slug(design, o)] = o.key
        for f in design.fields:
            obj = design.get_object(f.object)
            if obj is not None:
                fields_by_slug.setdefault((gen.object_slug(design, obj), _field_slug(design, f)), []).append(f)

    def okey(slug: str) -> str:
        return obj_key.get(slug, slug)

    objects: list[StateObject] = []
    live_slugs: set[str] = set()
    for o in snap.objects:
        slug = str(o.get("api_slug", ""))
        live_slugs.add(slug)
        design_obj = design.get_object(okey(slug)) if design else None
        native = slug in NATIVE_OBJECTS or bool(design_obj and design_obj.kind == "core")
        objects.append(StateObject(okey(slug), str(o.get("singular_noun", "")), native))

    fields: list[StateField] = []
    seen_fields: set[tuple[str, str]] = set()
    for oslug, attrs in snap.attributes.items():
        for a in attrs:
            if a.get("is_archived") or a.get("type") in ("record-reference", "status"):
                continue
            slug = str(a.get("api_slug", ""))
            system = bool(a.get("is_system_attribute"))
            opts_raw = [
                o for o in snap.options.get(("objects", oslug, slug), []) if not o.get("is_archived")
            ]
            matched = fields_by_slug.get((oslug, slug), [])
            targets: list[FieldDef | None] = list(matched) or [None]
            for fdef in targets:
                if fdef is None:
                    key, ftype, native, label, design_opts = slug, _reverse_type(a), system, str(a.get("title", "")), ()
                else:
                    native = gen.PLATFORM in fdef.native or system
                    key = fdef.key
                    ftype = fdef.type if (native or _type_matches(a, fdef.type)) else _reverse_type(a)
                    label = fdef.label if native else str(a.get("title", ""))
                    design_opts = fdef.options
                options: list[tuple[str, str]] = []
                for o in opts_raw:
                    title = str(o.get("title", ""))
                    okey_ = _option_key(title, design_opts)
                    options.append((okey_, title))
                    ids[("option", oslug, slug, okey_)] = _id_of(o, "option_id") or title
                fields.append(StateField(okey(oslug), key, ftype, label, tuple(options), native))
                seen_fields.add((okey(oslug), key))
    if design is not None:
        # Attio gives every custom object its own name attribute, so a design `name` field maps to it.
        for f in design.fields:
            if gen._is_object_name_field(design, f):
                obj = design.get_object(f.object)
                if obj and gen.object_slug(design, obj) in live_slugs and (f.object, f.key) not in seen_fields:
                    fields.append(StateField(f.object, f.key, f.type, f.label, (), True))

    relationships = _build_relationships(snap, design, okey)

    pipelines: list[StatePipeline] = []
    for lst in snap.lists:
        lslug = str(lst.get("api_slug", ""))
        stage_attr = next(
            (
                a for a in snap.list_attributes.get(lslug, [])
                if a.get("api_slug") == "stage" and a.get("type") == "status" and not a.get("is_archived")
            ),
            None,
        )
        if stage_attr is None:
            continue
        parent = lst.get("parent_object")
        parent_slug = str(parent[0] if isinstance(parent, list) and parent else parent or "")
        pl_obj = okey(parent_slug)
        design_pl = design.get_pipeline(pl_obj, lslug) if design else None
        stages: list[StateStage] = []
        for s in snap.statuses.get(lslug, []):
            if s.get("is_archived"):
                continue
            title = str(s.get("title", ""))
            key = _stage_key(title, design_pl)
            design_stage = next((x for x in design_pl.stages if x.key == key), None) if design_pl else None
            if s.get("celebration_enabled"):
                stype = "won"
            else:
                stype = design_stage.type if design_stage and design_stage.type != "won" else "open"
            stages.append(StateStage(key, title, stype, None))
            ids[("status", lslug, key)] = _id_of(s, "status_id") or title
        pipelines.append(StatePipeline(pl_obj, lslug, str(lst.get("name", "")), tuple(stages)))

    state = State(PLATFORM, tuple(objects), tuple(fields), tuple(relationships), tuple(pipelines))
    return state, ids


def _build_relationships(
    snap: Snapshot, design: Design | None, okey: Callable[[str], str]
) -> list[StateRelationship]:
    """Pair record-reference attributes into relationships. System ones are native and left out."""
    refs: dict[tuple[str, str], dict[str, Any]] = {}
    for oslug, attrs in snap.attributes.items():
        for a in attrs:
            if a.get("type") == "record-reference" and not a.get("is_archived") and not a.get("is_system_attribute"):
                refs[(oslug, str(a.get("api_slug", "")))] = a
    consumed: set[tuple[str, str]] = set()
    out: list[StateRelationship] = []

    if design is not None:
        for rel in design.relationships:
            if gen.PLATFORM in rel.native:
                continue
            from_slug = gen.object_slug_for(design, rel.from_object)
            to_slug = gen.object_slug_for(design, rel.to_object)
            fwd_id = (from_slug, _slugify(rel.from_label))
            fwd = refs.get(fwd_id)
            if fwd is None:
                continue
            rev_id = (to_slug, _slugify(rel.to_label))
            consumed.update({fwd_id, rev_id})
            rinfo = fwd.get("relationship") or {}
            if "is_multiselect" in rinfo:
                reverse_multi: bool | None = bool(rinfo["is_multiselect"])
            elif rev_id in refs:
                reverse_multi = bool(refs[rev_id].get("is_multiselect"))
            else:
                reverse_multi = None
            card = (
                rel.cardinality
                if reverse_multi is None
                else _cardinality(bool(fwd.get("is_multiselect")), reverse_multi)
            )
            out.append(StateRelationship(rel.key, rel.from_object, rel.to_object, card))

    for (oslug, aslug), a in sorted(refs.items()):
        if (oslug, aslug) in consumed:
            continue
        rinfo = a.get("relationship") or {}
        target = str(rinfo.get("object_slug") or rinfo.get("object") or "")
        back = (target, str(rinfo.get("api_slug", "")))
        if back in refs and back in consumed:
            continue
        if back in refs and back < (oslug, aslug):
            continue  # the other side of this pair sorts first and carries it
        consumed.add((oslug, aslug))
        rev_multi = bool(rinfo.get("is_multiselect")) if rinfo else False
        out.append(
            StateRelationship(
                f"{okey(oslug)}.{aslug}", okey(oslug), okey(target), _cardinality(bool(a.get("is_multiselect")), rev_multi)
            )
        )
    return out


# --- the adapter -----------------------------------------------------------------------------

_RE_OBJECT = re.compile(r"^/v2/objects/([^/]+)$")
_RE_LIST = re.compile(r"^/v2/lists/([^/]+)$")
_RE_ATTR_COLL = re.compile(r"^/v2/(objects|lists)/([^/]+)/attributes$")
_RE_ATTR = re.compile(r"^/v2/(objects|lists)/([^/]+)/attributes/([^/]+)$")
_RE_SUB_COLL = re.compile(r"^/v2/(objects|lists)/([^/]+)/attributes/([^/]+)/(options|statuses)$")
_RE_SUB = re.compile(r"^/v2/(objects|lists)/([^/]+)/attributes/([^/]+)/(options|statuses)/([^/]+)$")


class AttioAdapter(Adapter):
    """Reads, plans and applies against one Attio workspace.

    `production` is the effective flag: true unless a test label is set and the caller did not
    ask for production. The CLI does the review and production gating (D-14) and may set `mode`;
    the adapter does not hold back a change the CLI has cleared.
    """

    platform = PLATFORM

    def __init__(
        self,
        token: str,
        *,
        session: Any | None = None,
        label: str = "",
        production: bool = True,
        production_flag: bool = False,
        sleep: Callable[[float], None] = time.sleep,
        base_url: str = BASE_URL,
    ) -> None:
        if not token:
            raise SafetyError("ATTIO_ACCESS_TOKEN is empty.")
        self._token = token
        self.session = session if session is not None else requests.Session()
        self.label = label
        self.production = production
        self.mode = Mode(dry_run=True, production=production, allow_review=False)  # the CLI sets this
        self._production_flag = production_flag
        self._verified_target = ""
        self._sleep = sleep
        self._base_url = base_url.rstrip("/")
        self.request_log: list[str] = []
        self.skipped: list[Change] = []
        self.workspace: Workspace | None = None
        self._snapshot: Snapshot | None = None
        self._ids: dict[tuple[str, ...], str] = {}
        self._last_state: State | None = None
        self._last_design: Design | None = None

    def __repr__(self) -> str:  # never show the token
        return f"AttioAdapter(label={self.label!r}, production={self.production})"

    # -- HTTP ------------------------------------------------------------------------------

    def _call(
        self, method: str, path: str, *, params: Mapping[str, Any] | None = None, body: Any = None
    ) -> Any:
        """Send one request and return the parsed JSON. Retries 429 and, for reads, 5xx.

        Source: https://docs.attio.com/rest-api/guides/rate-limiting.md and
        https://docs.attio.com/rest-api/guides/authentication.md (Bearer token). Error shape:
        platforms/attio/reference/limits-and-errors.md. Never sends DELETE.
        """
        if method not in ALLOWED_METHODS:
            raise ValueError(f"{method} is never sent by this adapter.")
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        rate_tries = 0
        server_tries = 0
        while True:
            try:
                resp = self.session.request(
                    method, self._base_url + path, params=params, json=body,
                    headers=headers, timeout=TIMEOUT_SECONDS,
                )
            except requests.RequestException as exc:
                raise AttioApiError(0, "network_error", type(exc).__name__) from None
            self.request_log.append(f"{method} {path} {resp.status_code}")
            if resp.status_code == 429 and rate_tries < MAX_RETRIES_429:
                wait = parse_retry_after(resp.headers.get("Retry-After"))
                if wait is None:
                    wait = BACKOFF_SECONDS[min(rate_tries, len(BACKOFF_SECONDS) - 1)]
                self._sleep(min(max(wait, 1.0), MAX_WAIT_SECONDS))
                rate_tries += 1
                continue
            if resp.status_code >= 500 and method == "GET" and server_tries < MAX_RETRIES_5XX_READ:
                self._sleep(BACKOFF_SECONDS[server_tries])
                server_tries += 1
                continue
            if resp.status_code >= 400:
                raise self._error(resp)
            try:
                return resp.json()
            except ValueError:
                return {}

    @staticmethod
    def _error(resp: Any) -> AttioApiError:
        try:
            body = resp.json()
        except ValueError:
            body = None
        if isinstance(body, dict):
            return AttioApiError(
                resp.status_code, str(body.get("code", "")), str(body.get("message", "")),
                body, str(body.get("type", "")),
            )
        return AttioApiError(resp.status_code, "", str(getattr(resp, "text", ""))[:200], body)

    def _data(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        """GET a resource and return its `data`. Source: https://api.attio.com/openapi/api."""
        body = self._call("GET", path, params=params)
        return body.get("data") if isinstance(body, dict) else None

    def _get_or_none(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        """GET one item, or None on 404. Source: https://api.attio.com/openapi/api."""
        try:
            return self._data(path, params)
        except AttioApiError as exc:
            if exc.status == 404:
                return None
            raise

    # -- identity --------------------------------------------------------------------------

    def identify(self) -> Workspace:
        """Check the token and return the workspace it belongs to.

        Source: https://docs.attio.com/rest-api/endpoint-reference/meta/identify.md.
        An inactive or revoked token returns 200 with `active: false`, so the field is checked.
        """
        body = self._call("GET", "/v2/self")
        info = body.get("data", body) if isinstance(body, dict) else {}
        if not isinstance(info, dict) or not info.get("active"):
            raise SafetyError("The Attio token is not active (revoked, unknown or expired). Nothing was read.")
        self.workspace = Workspace(
            name=str(info.get("workspace_name", "")),
            slug=str(info.get("workspace_slug", "")),
            workspace_id=str(info.get("workspace_id", "")),
            scopes=tuple(str(info.get("scope", "")).split()),
        )
        return self.workspace

    # -- reading ---------------------------------------------------------------------------

    def _attributes(self, target: str, parent: str) -> list[dict[str, Any]]:
        """All attributes of an object or list, archived included, paged.

        Source: https://api.attio.com/openapi/api (list attributes), reference/fields.md.
        """
        out: list[dict[str, Any]] = []
        for page in range(MAX_PAGES):
            batch = self._data(
                f"/v2/{target}/{parent}/attributes",
                {"limit": PAGE_SIZE, "offset": page * PAGE_SIZE, "show_archived": "true"},
            ) or []
            out.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
        return out

    def _sub_items(self, target: str, parent: str, attr: str, kind: str) -> list[dict[str, Any]]:
        """Options or statuses of an attribute, archived included.

        Source: https://api.attio.com/openapi/api (list select options, list statuses).
        """
        return self._data(
            f"/v2/{target}/{parent}/attributes/{attr}/{kind}", {"show_archived": "true"}
        ) or []

    def fetch_snapshot(self) -> Snapshot:
        """Read objects, attributes, options, lists, stage attributes and statuses.

        Sources: https://docs.attio.com/rest-api/endpoint-reference/objects/list-objects.md and
        https://api.attio.com/openapi/api (attributes, options, statuses, lists).
        """
        snap = Snapshot()
        snap.objects = self._data("/v2/objects") or []
        for o in snap.objects:
            slug = str(o.get("api_slug", ""))
            attrs = self._attributes("objects", slug)
            snap.attributes[slug] = attrs
            for a in attrs:
                if a.get("type") == "select" and not a.get("is_archived"):
                    asl = str(a.get("api_slug", ""))
                    snap.options[("objects", slug, asl)] = self._sub_items("objects", slug, asl, "options")
        snap.lists = self._data("/v2/lists") or []
        for lst in snap.lists:
            lslug = str(lst.get("api_slug", ""))
            attrs = self._attributes("lists", lslug)
            snap.list_attributes[lslug] = attrs
            if any(a.get("api_slug") == "stage" and a.get("type") == "status" and not a.get("is_archived") for a in attrs):
                snap.statuses[lslug] = self._sub_items("lists", lslug, "stage", "statuses")
        return snap

    def read_state(self, design: Design | None = None) -> State:
        """Read the workspace into a canonical `State`.

        Source: https://api.attio.com/openapi/api. Checks the token first (`identify`); the
        workspace name and slug are then on `self.workspace`. With a `design`, keys are the
        design's; without one they are slugs. `plan` re-maps a slug-keyed state against its design.
        """
        self.identify()
        snap = self.fetch_snapshot()
        state, ids = build_state(snap, design)
        self._snapshot, self._ids = snap, ids
        self._last_state, self._last_design = state, design
        return state

    # -- planning --------------------------------------------------------------------------

    def plan(self, design: Design, state: State) -> Plan:
        """Diff the design against the state with `tools.crm.planner`, with Attio payloads.

        Source for payload shapes: https://api.attio.com/openapi/api via `tools.generators.attio`.
        If `state` came from `read_state()` with no design it is re-keyed against `design` first.
        """
        if state is self._last_state and self._last_design is None and self._snapshot is not None:
            state, self._ids = build_state(self._snapshot, design)
        workspace = self.workspace or self.identify()
        plan = plan_changes(
            design, state, lambda kind, target, ctx: self._payload(kind, target, ctx),
            target=workspace.name, source_urls=SOURCE_URLS, ui_paths=UI_PATHS,
            extra_manual_steps=self._manual_steps(design, state),
        )
        # The API cannot reorder stages, so a reorder is a person's job.
        changes = tuple(c for c in plan.changes if c.kind != "reorder_stages")
        reorders = [
            ManualStep(
                title=f"Reorder stages: {c.target}",
                reason="Attio cannot reorder statuses through the API. Order follows creation order.",
                ui_path="Lists in the left sidebar, then the list, then the Stage attribute settings.",
                done_when=c.summary.replace("Reorder stages of ", "the stages read in this order: ", 1) + ".",
            )
            for c in plan.changes
            if c.kind == "reorder_stages"
        ]
        return replace(plan, changes=changes, manual_steps=plan.manual_steps + tuple(reorders))

    @staticmethod
    def _manual_steps(design: Design, state: State) -> list[ManualStep]:
        deals_live = any(o.key == "deal" for o in state.objects)
        steps = []
        for s in gen.manual_steps(design):
            if s["title"] == "Enable the Deals object" and deals_live:
                continue
            steps.append(ManualStep(title=s["title"], reason=s["why"], ui_path=s["where"], done_when=s["done_when"]))
        return steps

    def _payload(self, kind: str, target: str, ctx: dict[str, Any]) -> dict[str, Any]:
        """The requests behind one change, in the generator's request shape.

        Create payloads come from `tools.generators.attio`; PATCH bodies follow
        https://docs.attio.com/rest-api/endpoint-reference/attributes/update-an-attribute.md and
        https://docs.attio.com/rest-api/endpoint-reference/objects/update-an-object.md.
        """
        design: Design = ctx["design"]
        reqs: list[dict[str, Any]] = []
        fld: FieldDef | None = ctx.get("field")
        pl: Pipeline | None = ctx.get("pipeline")
        stage: Stage | None = ctx.get("stage")

        def patch(path: str, data: dict[str, Any]) -> dict[str, Any]:
            return {"method": "PATCH", "path": path, "body": {"data": data}}

        def parent_of(f: FieldDef) -> str:
            obj = design.get_object(f.object)
            return gen.object_slug(design, obj) if obj else f.object

        if kind == "add_object":
            reqs = [gen.object_request(design, ctx["object"])]
        elif kind == "rename_object":
            o = ctx["object"]
            reqs = [patch(f"/v2/objects/{gen.object_slug(design, o)}",
                          {"singular_noun": o.label, "plural_noun": o.plural_label})]
        elif kind == "add_relationship":
            reqs = [gen.relationship_request(design, ctx["relationship"])]
        elif kind == "add_pipeline" and pl:
            reqs = gen.list_requests(design, pl) + gen.status_requests(pl)
        elif kind == "add_stage" and pl and stage:
            reqs = [gen.status_request(pl, stage)]
        elif kind in ("rename_stage", "update_stage", "remove_stage") and pl:
            key = stage.key if stage else ctx["live_stage"].key
            ident = self._ids.get(("status", pl.key, key)) or (ctx["live_stage"].label if "live_stage" in ctx else "")
            if not ident:
                raise AttioApiError(0, "unresolved", f"No live id for stage {pl.key}.{key}. Run read_state first.")
            path = f"/v2/lists/{pl.key}/attributes/stage/statuses/{ident}"
            if kind == "rename_stage" and stage:
                reqs = [patch(path, {"title": stage.label})]
            elif kind == "update_stage" and stage:
                reqs = [patch(path, {"celebration_enabled": stage.type == "won"})]
            else:
                reqs = [patch(path, {"is_archived": True})]
        elif kind == "add_field" and fld:
            slug = _field_slug(design, fld)
            reqs = [gen.attribute_request("objects", parent_of(fld), fld, slug)]
            reqs += gen.option_requests("objects", parent_of(fld), slug, fld)
        elif kind == "rename_field" and fld:
            reqs = [patch(f"/v2/objects/{parent_of(fld)}/attributes/{_field_slug(design, fld)}", {"title": fld.label})]
        elif kind in ("add_option", "rename_option", "remove_option") and fld:
            parent, slug = parent_of(fld), _field_slug(design, fld)
            if kind == "add_option":
                one = replace(fld, options=(ctx["option"],))
                reqs = gen.option_requests("objects", parent, slug, one)
                for lst in self._lost_reason_lists(design, fld):
                    reqs += gen.option_requests("lists", lst.key, fld.key, one)
            else:
                opt_key = ctx["option"].key if kind == "rename_option" else ctx["live_option"][0]
                ident = self._ids.get(("option", parent, slug, opt_key)) or (
                    ctx["live_option"][1] if kind == "remove_option" else ""
                )
                if not ident:
                    raise AttioApiError(0, "unresolved", f"No live id for option {target}. Run read_state first.")
                data = {"title": ctx["option"].label} if kind == "rename_option" else {"is_archived": True}
                reqs = [patch(f"/v2/objects/{parent}/attributes/{slug}/options/{ident}", data)]
        return {"requests": reqs}

    def _lost_reason_lists(self, design: Design, fld: FieldDef) -> list[Pipeline]:
        """Pipelines whose live list already holds a copy of this lost-reason select."""
        if self._snapshot is None:
            return []
        out = []
        for pl in design.pipelines:
            if fld in gen._lost_reason_fields(design, pl):
                attrs = self._snapshot.list_attributes.get(pl.key, [])
                if any(a.get("api_slug") == fld.key and not a.get("is_archived") for a in attrs):
                    out.append(pl)
        return out

    # -- applying --------------------------------------------------------------------------

    def _current(self, req: Mapping[str, Any]) -> dict[str, Any] | None:
        """Read the item a request is about, or None if it is not there.

        Source: https://api.attio.com/openapi/api (get object, list, attribute; list options and
        statuses). Options and statuses are matched by id or title, archived ones included.
        """
        path = str(req["path"])
        data = (req.get("body") or {}).get("data", {})
        method = req["method"]
        if method == "POST" and path == "/v2/objects":
            return self._get_or_none(f"/v2/objects/{data['api_slug']}")
        if method == "POST" and path == "/v2/lists":
            return self._get_or_none(f"/v2/lists/{data['api_slug']}")
        m = _RE_ATTR_COLL.match(path)
        if m and method == "POST":
            return self._get_or_none(f"/v2/{m[1]}/{m[2]}/attributes/{data['api_slug']}")
        m = _RE_SUB_COLL.match(path)
        if m and method == "POST":
            items = self._sub_items(m[1], m[2], m[3], m[4])
            return next((i for i in items if i.get("title") == data.get("title")), None)
        m = _RE_SUB.match(path)
        if m and method == "PATCH":
            items = self._sub_items(m[1], m[2], m[3], m[4])
            idkey = "option_id" if m[4] == "options" else "status_id"
            found = next((i for i in items if _id_of(i, idkey) == m[5] or i.get("title") == m[5]), None)
            if found is None and "title" in data:
                found = next((i for i in items if i.get("title") == data["title"]), None)
            return found
        m = _RE_ATTR.match(path)
        if m and method == "PATCH":
            return self._get_or_none(f"/v2/{m[1]}/{m[2]}/attributes/{m[3]}")
        m = _RE_OBJECT.match(path)
        if m and method == "PATCH":
            return self._get_or_none(f"/v2/objects/{m[1]}")
        raise ValueError(f"Unsupported request {method} {path}")

    @staticmethod
    def _check_existing(
        req: Mapping[str, Any], found: Mapping[str, Any] | None, body: Any = None, error_type: str = ""
    ) -> bool:
        """True if the request is already satisfied by `found`.

        Source: https://api.attio.com/openapi/api and reference/limits-and-errors.md (Q9: an archived
        item probably still holds its slug). A create that finds an archived item, or an attribute of
        another type, raises, because the tool must not restore or change in place.
        """
        if found is None:
            return False
        data = (req.get("body") or {}).get("data", {})
        if req["method"] == "POST":
            if found.get("is_archived"):
                raise AttioApiError(
                    409, "slug_conflict",
                    "The item exists but is archived. Restoring it is a reviewed change done by hand.",
                    body, error_type,
                )
            if "type" in data and found.get("type") != data["type"]:
                raise AttioApiError(
                    409, "slug_conflict",
                    f"The attribute exists with type {found.get('type')}; the design says {data['type']}. "
                    "Types are never changed in place.",
                    body, error_type,
                )
            return True
        return all(found.get(k) == v for k, v in data.items())

    def _run_request(self, req: Mapping[str, Any]) -> bool:
        """Run one request unless already satisfied. True if it was sent, False if skipped.

        Sources: https://docs.attio.com/rest-api/endpoint-reference/attributes/create-an-attribute.md
        (and the other create and update pages named in `SOURCE_URLS`); 409 handling per
        reference/limits-and-errors.md: a 409 slug_conflict means "already exists", so the item is
        read back and checked.
        """
        if self._check_existing(req, self._current(req)):
            return False
        try:
            self._call(req["method"], req["path"], body=req.get("body"))
        except AttioApiError as exc:
            if req["method"] == "POST" and exc.status == 409 and exc.code == "slug_conflict":
                if self._check_existing(req, self._current(req), exc.body, exc.error_type):
                    return False
            raise
        return True

    def _check_target(self, name: str) -> None:
        """Refuse a plan made for a different workspace than this token's.

        Source: https://docs.attio.com/rest-api/endpoint-reference/meta/identify.md. The workspace
        name comes from `GET /v2/self`, so the CLI's production confirmation names the same account.
        Checked once per adapter.
        """
        if self._verified_target == name:
            return
        live = self.identify()
        if name != live.name:
            raise SafetyError(
                f"The plan was made for workspace {name!r} but this token belongs to {live.name!r}. "
                "Nothing was changed."
            )
        self._verified_target = name

    def apply(self, plan: Plan, *, dry_run: bool = True) -> Result:
        """Apply a plan. Dry run by default and a dry run sends no HTTP request at all.

        Sources: the create and update endpoints in `SOURCE_URLS`, https://api.attio.com/openapi/api.
        The caller (`tools/crm_apply.py`) has already cleared review and production gates, so
        changes are not held back here. A destructive change is still refused. Runs changes in plan
        order, stops on the first error, never sends DELETE.
        """
        for change in plan.changes:
            if change.risk == "destructive":
                raise SafetyError(f"Plan contains a destructive change ({change.kind} {change.target}).")
        if dry_run:
            return Result(applied=(), failed=(), remaining=plan.changes, dry_run=True)
        if self.production and not self._production_flag:
            raise SafetyError(
                "ATTIO_TARGET is not set, so this workspace is treated as production. "
                "Re-run with --production (and confirm the workspace name), or set ATTIO_TARGET "
                "for a test workspace. Nothing was changed."
            )
        self._check_target(plan.target)
        applied: list[Change] = []
        self.skipped = []
        for i, change in enumerate(plan.changes):
            try:
                sent = [self._run_request(r) for r in change.payload.get("requests", [])]
            except AttioApiError as exc:
                text = redact(json.dumps(exc.body, sort_keys=True) if exc.body is not None else str(exc), [self._token])
                return Result(
                    tuple(applied), (Failure(change, f"{exc.status} {text}"),), plan.changes[i + 1:], dry_run=False
                )
            applied.append(change)
            if not any(sent):
                self.skipped.append(change)
        return Result(tuple(applied), (), (), dry_run=False)


def make_adapter(
    env: Mapping[str, str], *, target: str | None, production: bool, session: Any | None = None, **kwargs: Any
) -> AttioAdapter:
    """Build an Attio adapter from environment variables.

    `env` needs ATTIO_ACCESS_TOKEN; ATTIO_TARGET labels a test workspace. `target` is the label the
    user named on the command line (or None). If both are set they must match. The adapter is
    production unless the label is set and `production` is false; its `production` attribute is
    the effective value, so a caller building a `Mode` should read it. `session` and the other
    keyword arguments are for tests.
    """
    token = get_credential("ATTIO_ACCESS_TOKEN", dict(env))
    label = env.get("ATTIO_TARGET", "").strip()
    if target and label and target.strip() != label:
        raise SafetyError(f"--target {target!r} does not match ATTIO_TARGET {label!r}. Nothing was read.")
    effective = production or not label
    return AttioAdapter(
        token, session=session, label=label, production=effective, production_flag=production, **kwargs
    )
