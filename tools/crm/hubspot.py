"""HubSpot adapter: read live structure, plan against a design, apply additive changes.

Payloads, names and placeholders come from `tools.generators.hubspot` (one API version constant,
one naming scheme), so a build made from the generator's files and a build made by this adapter
are the same build. The diffing and the safety rules live in `tools.crm.planner` and
`tools.crm.safety`. This module only reads, maps, and calls.

Research for every call is in `platforms/hubspot/reference/`. Rules this adapter keeps:

- Dry run makes no HTTP call at all.
- HubSpot documents no "already exists" signal (limits-and-errors.md), so every change reads the
  live item first, keyed by internal name, label text, or our own `pipelineId` and `stageId`, and
  skips what is already there.
- 429 is retried with backoff (1 s doubling to 10 s, five tries). A daily-limit 429 is not retried.
- The first other error stops the run. The report has applied, failed (with the API error body,
  redacted) and remaining.
- `DELETE` is never issued. Removing an option hides it. HubSpot documents no way to hide or archive
  a stage or a pipeline, so stage removal becomes a manual step at plan time.

Placeholders such as `{objectTypeId.subscription}` stay in the plan file and are resolved from live
reads while applying, so a plan can be applied one change at a time by a later process.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, replace
from pathlib import Path
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
from tools.crm.safety import Mode, check_gates, get_credential, redact
from tools.design import REPO_ROOT, Design, load_core_model
from tools.generators import hubspot as gen
from tools.generators.hubspot import API_VERSION, PLATFORM

BASE_URL = "https://api.hubapi.com"
TOKEN_VAR = "HUBSPOT_ACCESS_TOKEN"
TARGET_VAR = "HUBSPOT_TARGET"
V = API_VERSION

MAX_TRIES = 5
BACKOFF_START = 1.0
BACKOFF_CAP = 10.0
TIMEOUT = 30

# Source pages per change kind (planner `source_urls`). All come from the generator's constants.
SOURCE_URLS: dict[str, str] = {
    "add_object": gen.SRC_CREATE_SCHEMA,
    "rename_object": gen.SRC_SCHEMAS,
    "add_relationship": gen.SRC_ASSOCIATIONS,
    "add_pipeline": gen.SRC_PIPELINES,
    "add_stage": gen.SRC_PIPELINES,
    "rename_stage": gen.SRC_PIPELINES,
    "update_stage": gen.SRC_PIPELINES,
    "reorder_stages": gen.SRC_PIPELINES,
    "remove_stage": gen.SRC_PIPELINES,
    "add_field": gen.SRC_PROPERTIES,
    "rename_field": gen.SRC_PROPERTIES,
    "add_option": gen.SRC_PROPERTIES,
    "rename_option": gen.SRC_PROPERTIES,
    "remove_option": gen.SRC_PROPERTIES,
}

_S = gen.SETTINGS
UI_PATHS: dict[str, str] = {
    "remove_object": f"{_S} > pick the object > Archive (Super Admin)",
    "remove_relationship": f"{_S} > pick the object > Associations tab",
    "change_relationship": f"{_S} > pick the object > Associations tab (Super Admin)",
    "remove_pipeline": f"{_S} > pick the object > Pipelines tab",
    "remove_field": f"{_S} > pick the object > Properties tab",
    "change_field_type": f"{_S} > pick the object > Properties tab",
}

STANDARD_REFS: dict[str, str] = {"companies": "0-2", "contacts": "0-1", "deals": "0-3"}
# Standard path name -> design object key. Fixed by model/core-model.yaml and objects.md.
STANDARD_KEYS: dict[str, str] = {"companies": "company", "contacts": "person", "deals": "deal"}

_URL_NOTE = gen.LOSSY_NOTES["url"]
_PORTAL_FROM_FQN = re.compile(r"^p(\d+)_")
_PLACEHOLDER = re.compile(r"\{objectTypeId\.([a-z0-9_]+)\}")
_TYPE_PLACEHOLDER = re.compile(r"\{typeId\.[a-z0-9_.]+\}")


class HubSpotError(RuntimeError):
    """An API call failed. The message holds the status and the redacted body, never the token."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


# --- HTTP ------------------------------------------------------------------------------------


@dataclass
class _Reply:
    status: int
    data: Any
    text: str


class _Http:
    """A thin client: Bearer token, 429 retry, redacted errors. `session` and `sleep` are injectable."""

    def __init__(self, token: str, session: Any = None, sleep: Callable[[float], None] = time.sleep) -> None:
        self._token = token
        self._session = session or requests.Session()
        self._sleep = sleep

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        params: Mapping[str, Any] | None = None,
        ok: tuple[int, ...] = (200, 201, 204),
        allow: tuple[int, ...] = (),
    ) -> _Reply:
        """Send one request. Statuses in `ok` and `allow` return a reply; anything else raises."""
        url = BASE_URL + path
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        delay = BACKOFF_START
        for attempt in range(1, MAX_TRIES + 1):
            try:
                resp = self._session.request(
                    method, url, headers=headers, params=params, json=body, timeout=TIMEOUT
                )
            except requests.RequestException as exc:  # no retry: a POST may have landed
                raise HubSpotError(
                    f"{method} {path} failed before a reply: {redact(type(exc).__name__, [self._token])}"
                ) from exc
            status = resp.status_code
            text = getattr(resp, "text", "") or ""
            try:
                data = resp.json() if text or status != 204 else None
            except ValueError:
                data = None
            if status == 429:
                policy = data.get("policyName") if isinstance(data, dict) else None
                if policy == "DAILY" or attempt == MAX_TRIES:
                    raise self._error(method, path, status, text)
                self._sleep(self._wait(resp, delay))
                delay = min(delay * 2, BACKOFF_CAP)
                continue
            if status in ok or status in allow:
                return _Reply(status, data, text)
            raise self._error(method, path, status, text)
        raise HubSpotError(f"{method} {path} gave up")  # pragma: no cover

    @staticmethod
    def _wait(resp: Any, delay: float) -> float:
        header = (getattr(resp, "headers", None) or {}).get("Retry-After")
        try:
            return min(float(header), 60.0) if header is not None else delay
        except (TypeError, ValueError):
            return delay

    def _error(self, method: str, path: str, status: int, text: str) -> HubSpotError:
        body = redact(text.strip(), [self._token])
        return HubSpotError(f"{method} {path} -> HTTP {status}: {body[:2000]}", status=status)

    def get(self, path: str, **kw: Any) -> _Reply:
        return self.request("GET", path, **kw)

    def get_optional(self, path: str, extra: tuple[int, ...] = ()) -> Any | None:
        """GET returning None on 404 (and on any status in `extra`)."""
        reply = self.request("GET", path, allow=(404, *extra))
        return None if reply.status in (404, *extra) else reply.data


# --- mapping live shapes to canonical terms --------------------------------------------------


def canonical_type(prop: Mapping[str, Any]) -> str:
    """Map a HubSpot property back to a canonical field type, the inverse of the generator's TYPE_MAP.

    `url` and `text` are the same HubSpot type; the generator ends a url description with a fixed
    note, which is how the round trip tells them apart. Unmapped shapes come back as
    `unknown:<type>/<fieldType>` so they show up as a difference rather than matching by accident.
    """
    t, ft = prop.get("type"), prop.get("fieldType")
    if t == "enumeration":
        owner = prop.get("referencedObjectType") or prop.get("externalOptionsReferenceType")
        if prop.get("externalOptions") and owner == "OWNER":
            return "user"
        return "multi_select" if ft == "checkbox" else "select"
    if t == "bool":
        return "checkbox"
    if t == "date":
        return "date"
    if t == "datetime":
        return "datetime"
    if t == "number":
        hint = prop.get("numberDisplayHint")
        if prop.get("showCurrencySymbol") or hint == "currency":
            return "currency"
        return "percent" if hint == "percentage" else "number"
    if t == "string":
        if ft == "textarea":
            return "long_text"
        if ft == "phonenumber":
            return "phone"
        if prop.get("textDisplayHint") == "email":
            return "email"
        if str(prop.get("description") or "").rstrip().endswith(_URL_NOTE):
            return "url"
        return "text"
    return f"unknown:{t}/{ft}"


def _visible_options(prop: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (str(o.get("value")), str(o.get("label") or ""))
        for o in prop.get("options") or []
        if not o.get("hidden")
    )


def _is_hubspot_owned(prop: Mapping[str, Any]) -> bool:
    meta = prop.get("modificationMetadata") or {}
    return bool(prop.get("hubspotDefined") or meta.get("readOnlyDefinition"))


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _core_native_map() -> dict[tuple[str, str], Any]:
    """(standard path name, HubSpot property name) -> core FieldDef, from the core model."""
    core = load_core_model()
    path_of = {o.key: o.native_names.get(PLATFORM, "") for o in core.objects}
    return {
        (path_of[f.object], f.native_names.get(PLATFORM, f.key)): f
        for f in core.fields
        if PLATFORM in f.native
    }


def _stage_state(object_key: str, pipeline_key: str, stage: Mapping[str, Any], deal: bool) -> StateStage:
    meta = stage.get("metadata") or {}
    sid = str(stage.get("id"))
    key = sid[len(pipeline_key) + 2 :] if sid.startswith(pipeline_key + "__") else sid
    closed_flag = meta.get("isClosed")
    if not deal:
        return StateStage(key, str(stage.get("label") or ""), "closed" if closed_flag == "true" else "open", None)
    try:
        prob = float(meta.get("probability"))
    except (TypeError, ValueError):
        prob = None
    closed = closed_flag == "true" if closed_flag is not None else prob in (0.0, 1.0)
    if closed and prob is not None and prob >= 1.0:
        kind = "won"
    elif closed and prob is not None and prob <= 0.0:
        kind = "lost"
    else:
        kind = "open"
    return StateStage(key, str(stage.get("label") or ""), kind, None if prob is None else round(prob * 100, 4))


def _find_limits(data: Any) -> list[dict[str, Any]]:
    """Every dict with a typeId and a maxToObjectIds, however the response nests them."""
    found: list[dict[str, Any]] = []
    if isinstance(data, dict):
        if "typeId" in data and "maxToObjectIds" in data:
            found.append(data)
        for value in data.values():
            found.extend(_find_limits(value))
    elif isinstance(data, list):
        for item in data:
            found.extend(_find_limits(item))
    return found


# --- account identity and entitlements -------------------------------------------------------


@dataclass(frozen=True)
class Identity:
    """Which HubSpot account the token reaches. `portal_id` is None when no call gave one."""

    portal_id: str | None
    source: str
    account_type: str | None = None


@dataclass(frozen=True)
class Entitlement:
    """Whether the account may create custom objects. `allowed` None means the read gave no answer."""

    allowed: bool | None
    remaining: int | None
    detail: str


UNKNOWN_ENTITLEMENT = Entitlement(None, None, "custom-object limits were not read")


def _first_number(data: Any, names: tuple[str, ...]) -> int | None:
    if isinstance(data, dict):
        for name in names:
            if isinstance(data.get(name), (int, float)) and not isinstance(data.get(name), bool):
                return int(data[name])
        for value in data.values():
            hit = _first_number(value, names)
            if hit is not None:
                return hit
    elif isinstance(data, list):
        for item in data:
            hit = _first_number(item, names)
            if hit is not None:
                return hit
    return None


# --- the adapter -----------------------------------------------------------------------------


class HubSpotAdapter(Adapter):
    """Reads and builds HubSpot structure. Build one with `make_adapter`."""

    platform = PLATFORM

    def __init__(
        self,
        token: str,
        *,
        target: str,
        production: bool = False,
        session: Any = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._http = _Http(token, session, sleep)
        self.target = target
        self.production = production
        self.mode = Mode(dry_run=True, production=production, allow_review=False)
        self.entitlement: Entitlement = UNKNOWN_ENTITLEMENT
        self.skipped: list[Change] = []
        self._identity: Identity | None = None
        self._type_ids: dict[str, str] = {}

    # -- identity ---------------------------------------------------------------------------

    def read_identity(self) -> Identity:
        """Name the portal this token reaches, so a production prompt can quote it.

        The research has no account-info page. First try `GET /account-info/v3/details`, HubSpot's
        Account Information API (page URL not confirmed in this repo; the live smoke test is what
        checks it). If that gives no portal id, take it from a documented response: a custom object
        schema's `fullyQualifiedName` is `p{HubId}_{name}`
        (https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/guide.md).
        An account with neither gives `portal_id=None`.
        """
        if self._identity is not None:
            return self._identity
        reply = self._http.request("GET", "/account-info/v3/details", allow=(400, 401, 403, 404))
        if reply.status == 401:
            raise HubSpotError("GET /account-info/v3/details -> HTTP 401: the access token was refused", status=401)
        if reply.status == 200 and isinstance(reply.data, dict) and reply.data.get("portalId"):
            self._identity = Identity(str(reply.data["portalId"]), "account-info", reply.data.get("accountType"))
            return self._identity
        for schema in self._schemas():
            m = _PORTAL_FROM_FQN.match(str(schema.get("fullyQualifiedName") or ""))
            if m:
                self._identity = Identity(m.group(1), "schema fullyQualifiedName")
                return self._identity
        self._identity = Identity(None, "none")
        return self._identity

    def target_label(self) -> str:
        """The name a production confirmation must type: the target label plus the portal id."""
        ident = self.read_identity()
        if ident.portal_id:
            return f"{self.target} (HubSpot portal {ident.portal_id})"
        return self.target

    # -- reading ----------------------------------------------------------------------------

    def _schemas(self) -> list[dict[str, Any]]:
        """List custom object schemas. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/get-schemas.md"""
        data = self._http.get(f"/crm-object-schemas/{V}/schemas").data or {}
        return list(data.get("results") or [])

    def _read_entitlement(self) -> Entitlement:
        """Read custom-object limits (OQ-3).

        Source: https://developers.hubspot.com/docs/api-reference/latest/crm/limits-tracking/guide.md
        The research does not show the response, so any `maxLimit` or `limit` and `usage` number in
        the body is used. 403 or 404 without a missing-scope list means the account lacks the
        feature; a missing-scope 403 or an unreadable body leaves the answer unknown.
        """
        reply = self._http.request("GET", f"/crm/limits/{V}/custom-object-types", allow=(402, 403, 404))
        if reply.status in (402, 403, 404):
            scopes = (reply.data or {}).get("context", {}).get("missingScopes") if isinstance(reply.data, dict) else None
            if scopes:
                return Entitlement(None, None, f"the key lacks scope {', '.join(scopes)} to read custom-object limits")
            return Entitlement(False, 0, f"the limits call returned HTTP {reply.status}: custom objects are not available")
        maximum = _first_number(reply.data, ("maxLimit", "limit", "max", "maximum"))
        if maximum is None:
            return Entitlement(None, None, "the limits response had no maximum")
        used = _first_number(reply.data, ("usage", "currentUsage", "used", "count")) or 0
        remaining = max(maximum - used, 0)
        return Entitlement(remaining > 0, remaining, f"{used} of {maximum} custom object definitions used")

    def _read_labels(self, a_ref: str, b_ref: str) -> list[dict[str, Any]]:
        """Association labels from a to b. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associations-schema/guide.md"""
        reply = self._http.request("GET", f"/crm/associations/{V}/{a_ref}/{b_ref}/labels", allow=(400, 404))
        if reply.status != 200 or not isinstance(reply.data, dict):
            return []
        return [r for r in reply.data.get("results") or [] if r.get("category") == "USER_DEFINED"]

    def _read_limits(self, a_ref: str, b_ref: str) -> dict[int, int] | None:
        """typeId -> maxToObjectIds for a to b, or None when the call is refused (a tier without limits).

        Source: https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associations-schema/guide.md
        The research shows the create body only, so the read is parsed for any typeId with a maxToObjectIds.
        """
        reply = self._http.request(
            "GET", f"/crm/associations/{V}/definitions/configurations/{a_ref}/{b_ref}", allow=(400, 403, 404)
        )
        if reply.status != 200:
            return None
        return {int(x["typeId"]): int(x["maxToObjectIds"]) for x in _find_limits(reply.data)}

    def read_state(self) -> State:
        """Read objects, properties, pipelines and association labels into canonical `State`.

        Sources: schemas (objects.md), properties and groups (fields.md), pipelines (pipelines.md),
        association labels and limits (relationships.md), all under platforms/hubspot/reference/.
        Keys follow the generator's naming. Three things need the design to finish and are bound in
        `plan`: relationship keys (HubSpot does not return the label's internal name, OQ-10 note in
        limits-and-errors.md), design-defined native properties, and won or lost on custom pipelines.
        HubSpot's own `default` deal pipeline is left out: it exists everywhere and cannot be removed.
        """
        self.entitlement = self._read_entitlement()
        schemas = self._schemas()
        self._type_ids = {str(s["name"]): str(s["objectTypeId"]) for s in schemas if s.get("objectTypeId")}
        refs: dict[str, str] = {path: path for path in STANDARD_REFS}  # object key source -> path ref
        keys: dict[str, str] = dict(STANDARD_KEYS)
        for s in schemas:
            refs[str(s["name"])] = str(s["objectTypeId"])
            keys[str(s["name"])] = str(s["name"])

        labels_of = {"company": "Company", "person": "Person", "deal": "Deal"}
        objects = [StateObject(k, labels_of[k], native=True) for k in STANDARD_KEYS.values()]
        for s in schemas:
            objects.append(StateObject(str(s["name"]), str((s.get("labels") or {}).get("singular") or "")))

        core = _core_native_map()
        fields: list[StateField] = []
        for source, ref in refs.items():
            obj_key = keys[source]
            primary = next(
                (str(s.get("primaryDisplayProperty")) for s in schemas if str(s["name"]) == source), None
            )
            for prop in self._properties(ref):
                name = str(prop["name"])
                options = _visible_options(prop)
                core_field = core.get((source, name)) if source in STANDARD_REFS else None
                if core_field is not None:
                    fields.append(
                        StateField(obj_key, core_field.key, core_field.type, core_field.label, options, native=True)
                    )
                    continue
                owned = _is_hubspot_owned(prop) or name == primary or name.startswith("hs_")
                fields.append(
                    StateField(obj_key, name, canonical_type(prop), str(prop.get("label") or ""), options, native=owned)
                )
            self._groups(ref)  # read for the record; groups are created on demand while applying

        pipelines = self._read_pipelines(refs, keys)
        relationships = self._read_relationships(refs, keys)
        return State(PLATFORM, tuple(objects), tuple(fields), tuple(relationships), tuple(pipelines))

    def _properties(self, ref: str) -> list[dict[str, Any]]:
        """All properties of an object. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide.md"""
        data = self._http.get(f"/crm/properties/{V}/{ref}").data or {}
        return list(data.get("results") or [])

    def _groups(self, ref: str) -> list[dict[str, Any]]:
        """All property groups of an object. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/properties/property-groups/create-property.md"""
        data = self._http.get(f"/crm/properties/{V}/{ref}/groups").data or {}
        return list(data.get("results") or [])

    def _read_pipelines(self, refs: Mapping[str, str], keys: Mapping[str, str]) -> list[StatePipeline]:
        """Pipelines of deals and custom objects. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md"""
        out: list[StatePipeline] = []
        for source, ref in refs.items():
            if source not in ("deals",) and source in STANDARD_REFS:
                continue  # HubSpot has no pipelines on contacts or companies
            obj_key = keys[source]
            data = self._http.get_optional(f"/crm/pipelines/{V}/{ref}")
            for pl in (data or {}).get("results") or []:
                pid = str(pl.get("id"))
                if source == "deals" and pid == "default":
                    continue
                key = pid[len(obj_key) + 2 :] if pid.startswith(obj_key + "__") and len(pid) > len(obj_key) + 2 else pid
                stages = sorted(pl.get("stages") or [], key=lambda s: s.get("displayOrder", 0))
                out.append(
                    StatePipeline(
                        obj_key, key, str(pl.get("label") or ""),
                        tuple(_stage_state(obj_key, key, s, deal=source == "deals") for s in stages),
                    )
                )
        return out

    def _read_relationships(self, refs: Mapping[str, str], keys: Mapping[str, str]) -> list[StateRelationship]:
        """One entry per user-defined label and direction, key `assoc:[from,to,typeId,label]`.

        `plan` folds the two directions of a design relationship into one. The cardinality of an
        entry is `many_to_one` when a limit of 1 sits on its label, `unknown` when limits could not
        be read, else `many_to_many`.
        """
        out: list[StateRelationship] = []
        sources = list(refs)
        for a in sources:
            for b in sources:
                if a == b:
                    continue
                labels = self._read_labels(refs[a], refs[b])
                if not labels:
                    continue
                limits = self._read_limits(refs[a], refs[b])
                for entry in labels:
                    type_id = int(entry["typeId"])
                    if limits is None:
                        card = "unknown"
                    else:
                        card = "many_to_one" if limits.get(type_id) == 1 else "many_to_many"
                    key = "assoc:" + json.dumps([keys[a], keys[b], type_id, entry.get("label")])
                    out.append(StateRelationship(key, keys[a], keys[b], card))
        return out

    # -- planning ---------------------------------------------------------------------------

    def plan(self, design: Design, state: State) -> Plan:
        """Diff `design` against `state` with the shared planner, then apply HubSpot's limits.

        Payloads come from the generator's builders. After the planner runs:
        custom objects the account cannot hold become manual steps (OQ-3, plan-requirements.md);
        pipelines on contacts or companies, object renames (OQ-4) and stage removals become manual
        steps; the generator's manual steps for views, workflows, stage gates and standard-object
        required properties are added through `extra_manual_steps`.
        """
        bound = self._bind(design, state)
        target = self.target_label() if self.production else self.target
        base = plan_changes(
            design, bound, self._payload, target=target, source_urls=SOURCE_URLS, ui_paths=UI_PATHS,
            extra_manual_steps=_generator_steps(design),
        )
        changes, converted = self._limit_changes(design, base.changes)
        return replace(base, changes=tuple(changes), manual_steps=base.manual_steps + tuple(converted))

    def _bind(self, design: Design, state: State) -> State:
        """Finish mapping live names to design keys, which needs the design."""
        # Relationships: fold the two directions of each design relationship into one.
        entries = [
            (r, json.loads(r.key[len("assoc:") :])) for r in state.relationships if r.key.startswith("assoc:")
        ]
        rels = [r for r in state.relationships if not r.key.startswith("assoc:")]
        used: set[str] = set()
        for rel in design.relationships:
            if PLATFORM in rel.native or rel.from_object == rel.to_object:
                continue
            names = {rel.from_label, rel.to_label}
            fwd = [(r, e) for r, e in entries if (r.from_object, r.to_object) == (rel.from_object, rel.to_object) and e[3] in names]
            back = [(r, e) for r, e in entries if (r.from_object, r.to_object) == (rel.to_object, rel.from_object) and e[3] in names]
            if not fwd and not back:
                continue
            used.update(r.key for r, _ in fwd + back)
            cards = [r.cardinality for r, _ in fwd + back]
            if "unknown" in cards:
                card = rel.cardinality
            else:
                capped_from = any(r.cardinality == "many_to_one" for r, _ in fwd)
                capped_to = any(r.cardinality == "many_to_one" for r, _ in back)
                card = (
                    "one_to_one" if capped_from and capped_to
                    else "many_to_one" if capped_from
                    else "one_to_many" if capped_to
                    else "many_to_many"
                )
            rels.append(StateRelationship(rel.key, rel.from_object, rel.to_object, card))
        for r, e in entries:
            if r.key not in used:
                rels.append(StateRelationship(f"{r.from_object}_to_{r.to_object}_{_slug(str(e[3]))}", r.from_object, r.to_object, "many_to_many"))

        # Design-defined native properties: HubSpot name -> design key, and HubSpot's own options kept.
        fields = list(state.fields)
        for f in design.fields:
            if PLATFORM not in f.native:
                continue
            name = f.native_names.get(PLATFORM, f.key)
            live = next((x for x in fields if x.object == f.object and x.key in (name, f.key)), None)
            if live is None:
                continue
            design_opts = {o.key for o in f.options}
            kept = tuple(o for o in live.options if o[0] in design_opts)
            fields = [x for x in fields if x is not live]
            fields.append(StateField(f.object, f.key, f.type, f.label, kept, native=True))

        # Custom object pipelines: HubSpot has closed, the design has won or lost.
        custom = {o.key for o in design.custom_objects}
        pipelines = []
        for p in state.pipelines:
            dp = design.get_pipeline(p.object, p.key)
            if p.object in custom and dp is not None:
                want = {s.key: s.type for s in dp.stages}
                stages = tuple(
                    replace(s, type=want[s.key]) if s.type == "closed" and want.get(s.key) in ("won", "lost") else s
                    for s in p.stages
                )
                p = replace(p, stages=stages)
            pipelines.append(p)
        return replace(state, fields=tuple(fields), relationships=tuple(rels), pipelines=tuple(pipelines))

    def _limit_changes(self, design: Design, changes: tuple[Change, ...]) -> tuple[list[Change], list[ManualStep]]:
        """Drop changes HubSpot cannot take and say so as manual steps."""
        manual: list[ManualStep] = []
        blocked: set[str] = set()
        ent = self.entitlement
        new_objects = [c for c in changes if c.kind == "add_object"]
        if ent.allowed is False:
            blocked = {c.target for c in new_objects}
        elif ent.remaining is not None:
            blocked = {c.target for c in new_objects[ent.remaining :]}
        for key in sorted(blocked, key=[c.target for c in new_objects].index):
            obj = design.get_object(key)
            label = obj.label if obj else key
            manual.append(
                ManualStep(
                    title=f"Custom object {label} cannot be created through the API",
                    reason=(
                        f"The account cannot hold another custom object ({ent.detail}). Custom objects need "
                        f"Enterprise. See {_plan_requirements_path(design)} for the tier table. Changes that "
                        f"depend on {label} (its properties, pipelines and relationships) were left out of this plan."
                    ),
                    ui_path=f"{_S} > Create custom object (needs Enterprise)",
                    done_when=f"{label} exists in the account, or the client has agreed to drop it from the design. Then re-plan.",
                )
            )
        rel_ends = {r.key: (r.from_object, r.to_object) for r in design.relationships}
        kept: list[Change] = []
        for c in changes:
            ends = rel_ends.get(c.target, ()) if c.kind == "add_relationship" else (c.target.split(".")[0],)
            if blocked.intersection(ends):
                continue
            if c.kind in ("add_pipeline", "add_stage", "rename_stage", "update_stage", "reorder_stages", "remove_stage"):
                obj_key, pl_key = c.target.split(".")[:2]
                pl = design.get_pipeline(obj_key, pl_key)
                if pl is not None and not gen.pipeline_supported(design, pl):
                    continue  # covered by the generator's "model without a pipeline" manual step
            if c.kind == "rename_object":
                manual.append(
                    ManualStep(
                        title=f"Rename custom object {c.target} by hand",
                        reason="HubSpot treats a custom object's labels as fixed after creation (OQ-4).",
                        ui_path=f"{_S} > pick the object > Edit labels",
                        done_when=f"The object shows its design label and re-planning shows no difference.",
                    )
                )
                continue
            if c.kind == "remove_stage":
                manual.append(
                    ManualStep(
                        title=f"Retire stage {c.target}",
                        reason=(
                            "The design no longer has this stage. HubSpot documents no way to hide or archive a "
                            "stage, and a delete is blocked while records use it (pipelines.md). This tool never deletes."
                        ),
                        ui_path=f"{_S} > pick the object > Pipelines tab > the pipeline > the stage row",
                        done_when="The stage is empty of records, removed in the CRM, and re-planning shows no difference.",
                        risk="destructive",
                        instructions=(
                            "1. Move every record out of the stage. 2. Remove the stage from workflows and views. "
                            "3. Delete it in the pipeline settings. " + _MIGRATION
                        ),
                    )
                )
                continue
            kept.append(c)
        return kept, manual

    def _payload(self, kind: str, target: str, ctx: dict[str, Any]) -> dict[str, Any]:
        """Build the API payload of one change from the generator's builders."""
        d: Design = ctx["design"]
        if kind == "add_object":
            obj = ctx["object"]
            req = next(r for r in gen.schema_requests(d) if r["body"]["name"] == obj.key)
            return {"method": "POST", "path": req["path"], "body": req["body"], "object": obj.key}
        if kind == "add_relationship":
            return _relationship_payload(d, ctx["relationship"])
        if kind == "add_pipeline":
            pl = ctx["pipeline"]
            pid = gen.pipeline_id(d, pl)
            req = next((r for r in gen.pipeline_requests(d) if r["body"]["pipelineId"] == pid), None)
            if req is None:  # unsupported pipeline, dropped later in `_limit_changes`
                return {}
            return {"method": "POST", "path": req["path"], "body": req["body"], "pipeline_id": pid}
        if kind in ("add_stage", "rename_stage", "update_stage"):
            pl, stage = ctx["pipeline"], ctx["stage"]
            ref = gen.object_ref_for(d, pl.object)
            base = f"/crm/pipelines/{V}/{ref}/{gen.pipeline_id(d, pl)}"
            body = {
                "label": stage.label,
                "displayOrder": [s.key for s in pl.stages].index(stage.key),
                "metadata": gen.stage_metadata(pl, stage),
            }
            sid = gen.stage_id(pl, stage)
            if kind == "add_stage":
                return {"method": "POST", "path": base + "/stages", "stage_id": sid, "pipeline_path": base,
                        "body": {**body, "stageId": sid}}
            return {"method": "PATCH", "path": f"{base}/stages/{sid}", "stage_id": sid, "pipeline_path": base, "body": body}
        if kind == "reorder_stages":
            pl = ctx["pipeline"]
            ref = gen.object_ref_for(d, pl.object)
            base = f"/crm/pipelines/{V}/{ref}/{gen.pipeline_id(d, pl)}"
            return {"pipeline_path": base, "order": [gen.stage_id(pl, s) for s in pl.stages]}
        if kind == "add_field":
            return _field_payload(d, ctx["field"])
        if kind == "rename_field":
            f = ctx["field"]
            return {"method": "PATCH", "path": _prop_path(d, f), "body": {"label": f.label}}
        if kind in ("add_option", "rename_option", "remove_option"):
            f = ctx["field"]
            if kind == "remove_option":
                value, label = ctx["live_option"]
            else:
                value, label = ctx["option"].key, ctx["option"].label
            return {"path": _prop_path(d, f), "value": value, "label": label}
        return {}

    # -- applying ---------------------------------------------------------------------------

    def apply(self, plan: Plan, *, dry_run: bool = True) -> Result:
        """Apply a plan. Dry run (the default) makes no HTTP call.

        A real run holds `needs_review` changes unless `self.mode.allow_review` is set, refuses a
        destructive change, re-checks live state before each change, skips satisfied ones (listed in
        `self.skipped`), and stops at the first failure. The production prompt belongs to the caller
        (D-14); this method does not ask again. HubSpot sources are in each handler's docstring.
        """
        runnable, held = check_gates(
            plan, replace(self.mode, dry_run=dry_run), confirm=lambda _target: None
        )
        self.skipped = []
        if dry_run:
            return Result(applied=(), remaining=runnable + held, dry_run=True)
        applied: list[Change] = []
        for i, change in enumerate(runnable):
            handler = _HANDLERS.get(change.kind)
            try:
                if handler is None:
                    raise HubSpotError(f"No HubSpot handler for change kind {change.kind!r}")
                done = handler(self, change)
            except HubSpotError as exc:
                return Result(tuple(applied), (Failure(change, str(exc)),), runnable[i + 1 :] + held, dry_run=False)
            (applied if done else self.skipped).append(change)
        return Result(tuple(applied), (), held, dry_run=False)

    # placeholder resolution

    def _resolve(self, value: Any) -> Any:
        """Replace `{objectTypeId.x}` placeholders in strings, lists and dicts from live reads."""
        if isinstance(value, str):
            return _PLACEHOLDER.sub(lambda m: self._object_type_id(m.group(1)), value)
        if isinstance(value, list):
            return [self._resolve(v) for v in value]
        if isinstance(value, dict):
            return {k: self._resolve(v) for k, v in value.items()}
        return value

    def _object_type_id(self, key: str) -> str:
        if key not in self._type_ids:
            self._type_ids = {str(s["name"]): str(s["objectTypeId"]) for s in self._schemas() if s.get("objectTypeId")}
        if key not in self._type_ids:
            raise HubSpotError(f"Placeholder {{objectTypeId.{key}}} cannot be resolved: no custom object {key} in the account")
        return self._type_ids[key]

    # handlers: each returns True when it changed something, False when live state already matched

    def _h_add_object(self, c: Change) -> bool:
        """Create a custom object. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/objects/schemas/create-schema.md"""
        key = c.payload["object"]
        if any(str(s["name"]) == key for s in self._schemas()):
            self._type_ids.pop(key, None)
            return False
        body = self._resolve(c.payload["body"])
        reply = self._http.request("POST", c.payload["path"], body=body)
        if isinstance(reply.data, dict) and reply.data.get("objectTypeId"):
            self._type_ids[key] = str(reply.data["objectTypeId"])
        return True

    def _h_add_relationship(self, c: Change) -> bool:
        """Create a paired association label, then its limits. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associations-schema/guide.md"""
        p = c.payload
        a_ref, b_ref = self._resolve(p["from_ref"]), self._resolve(p["to_ref"])
        names = {p["from_label"], p["to_label"]}
        changed = False
        created_ids: set[int] = set()
        have = [e for e in self._read_labels(a_ref, b_ref) if e.get("label") in names]
        if not have:
            req = p["label"]
            reply = self._http.request("POST", self._resolve(req["path"]), body=req["body"])
            changed = True
            for entry in (reply.data or {}).get("results") or []:
                if "typeId" in entry:
                    created_ids.add(int(entry["typeId"]))
        for lim in p["limits"]:
            la, lb = self._resolve(lim["a_ref"]), self._resolve(lim["b_ref"])
            entries = [e for e in self._read_labels(la, lb) if e.get("label") in names]
            if created_ids:
                narrowed = [e for e in entries if int(e["typeId"]) in created_ids]
                entries = narrowed or entries
            if not entries:
                raise HubSpotError(f"Cannot find the label {sorted(names)} between {la} and {lb} to limit it")
            type_id = int(entries[0]["typeId"])
            existing = self._read_limits(la, lb) or {}
            if existing.get(type_id) == 1:
                continue
            body = json.loads(json.dumps(lim["request"]["body"]))
            body["inputs"][0]["typeId"] = type_id
            self._http.request("POST", self._resolve(lim["request"]["path"]), body=self._resolve(body))
            changed = True
        return changed

    def _h_add_pipeline(self, c: Change) -> bool:
        """Create a pipeline with its stages. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md"""
        path = self._resolve(c.payload["path"])
        if self._http.get_optional(f"{path}/{c.payload['pipeline_id']}") is not None:
            return False
        self._http.request("POST", path, body=self._resolve(c.payload["body"]))
        return True

    def _h_add_stage(self, c: Change) -> bool:
        """Add one stage. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/stages/create-pipeline-stage.md"""
        pipe = self._http.get_optional(self._resolve(c.payload["pipeline_path"]))
        if pipe is None:
            raise HubSpotError(f"Pipeline for {c.target} does not exist, so the stage cannot be added")
        if any(s.get("id") == c.payload["stage_id"] for s in pipe.get("stages") or []):
            return False
        self._http.request("POST", self._resolve(c.payload["path"]), body=c.payload["body"])
        return True

    def _h_patch_stage(self, c: Change) -> bool:
        """Rename a stage or change its metadata. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md"""
        pipe = self._http.get_optional(self._resolve(c.payload["pipeline_path"]))
        stage = next((s for s in (pipe or {}).get("stages") or [] if s.get("id") == c.payload["stage_id"]), None)
        if stage is None:
            raise HubSpotError(f"Stage for {c.target} does not exist in the live pipeline")
        body = c.payload["body"]
        live_meta = stage.get("metadata") or {}
        if stage.get("label") == body["label"] and all(live_meta.get(k) == v for k, v in body["metadata"].items()):
            return False
        self._http.request("PATCH", self._resolve(c.payload["path"]), body=body)
        return True

    def _h_reorder(self, c: Change) -> bool:
        """Set displayOrder on stages. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide.md"""
        base = self._resolve(c.payload["pipeline_path"])
        pipe = self._http.get_optional(base)
        live = {s["id"]: s.get("displayOrder") for s in (pipe or {}).get("stages") or []}
        changed = False
        for order, sid in enumerate(i for i in c.payload["order"] if i in live):
            if live[sid] != order:
                self._http.request("PATCH", f"{base}/stages/{sid}", body={"displayOrder": order})
                changed = True
        return changed

    def _h_add_field(self, c: Change) -> bool:
        """Create a property, its group first, and mark it required on a custom object. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide.md"""
        p = c.payload
        path = self._resolve(p["path"])
        changed = False
        group = p.get("group")
        if group:
            gpath = f"{self._resolve(p['groups_path'])}/{group['name']}"
            if self._http.get_optional(gpath) is None:
                self._http.request("POST", self._resolve(p["groups_path"]), body=group)
                changed = True
        if self._http.get_optional(f"{path}/{p['body']['name']}") is None:
            self._http.request("POST", path, body=self._resolve(p["body"]))
            changed = True
        if p.get("required_via"):
            spath = self._resolve(p["required_via"])
            schema = self._http.get_optional(spath)
            required = list((schema or {}).get("requiredProperties") or [])
            if schema is not None and p["body"]["name"] not in required:
                self._http.request(
                    "PATCH", spath, body={"clearDescription": False, "requiredProperties": [*required, p["body"]["name"]]}
                )
                changed = True
        return changed

    def _h_rename_field(self, c: Change) -> bool:
        """Change a property label. Source: https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide.md"""
        path = self._resolve(c.payload["path"])
        live = self._http.get_optional(path)
        if live is None:
            raise HubSpotError(f"Property for {c.target} does not exist")
        if live.get("label") == c.payload["body"]["label"]:
            return False
        self._http.request("PATCH", path, body=c.payload["body"])
        return True

    def _h_option(self, c: Change) -> bool:
        """Add, relabel or hide one option, sending the whole list (PATCH replaces it).

        Hiding is how an option is removed: hidden options stay on old records. Source:
        https://developers.hubspot.com/docs/api-reference/latest/crm/properties/guide.md
        """
        path = self._resolve(c.payload["path"])
        live = self._http.get_optional(path)
        if live is None:
            raise HubSpotError(f"Property for {c.target} does not exist")
        options = [dict(o) for o in live.get("options") or []]
        value, label = c.payload["value"], c.payload["label"]
        match = next((o for o in options if o.get("value") == value), None)
        if c.kind == "add_option":
            if match is None:
                options.append({"label": label, "value": value, "displayOrder": len(options), "hidden": False})
            elif match.get("hidden"):
                match["hidden"] = False
            else:
                return False
        elif c.kind == "rename_option":
            if match is None or match.get("label") == label:
                return False
            match["label"] = label
        else:  # remove_option: hide, never delete
            if match is None or match.get("hidden"):
                return False
            match["hidden"] = True
        self._http.request("PATCH", path, body={"options": options})
        return True


_HANDLERS: dict[str, Callable[[HubSpotAdapter, Change], bool]] = {
    "add_object": HubSpotAdapter._h_add_object,
    "add_relationship": HubSpotAdapter._h_add_relationship,
    "add_pipeline": HubSpotAdapter._h_add_pipeline,
    "add_stage": HubSpotAdapter._h_add_stage,
    "rename_stage": HubSpotAdapter._h_patch_stage,
    "update_stage": HubSpotAdapter._h_patch_stage,
    "reorder_stages": HubSpotAdapter._h_reorder,
    "add_field": HubSpotAdapter._h_add_field,
    "rename_field": HubSpotAdapter._h_rename_field,
    "add_option": HubSpotAdapter._h_option,
    "rename_option": HubSpotAdapter._h_option,
    "remove_option": HubSpotAdapter._h_option,
}

_MIGRATION = "Export the data first. Never delete before the data is safe elsewhere."


# --- payload helpers -------------------------------------------------------------------------


def _prop_name(f: Any) -> str:
    return f.native_names.get(PLATFORM, f.key) if PLATFORM in f.native else f.key


def _prop_path(d: Design, f: Any) -> str:
    return f"/crm/properties/{V}/{gen.object_ref_for(d, f.object)}/{_prop_name(f)}"


def _field_payload(d: Design, f: Any) -> dict[str, Any]:
    obj = d.get_object(f.object)
    ref = gen.object_ref_for(d, f.object)
    group_name = gen.group_for(d, f)
    group = None
    if group_name not in gen.BUILTIN_GROUPS:
        label = d.name if group_name == gen.design_group(d) else group_name.replace("_", " ").capitalize()
        group = {"name": group_name, "label": label}
    required_via = None
    if obj is not None and f.required and obj.kind == "custom" and not gen.is_existing(d, obj):
        _, _, primary = gen.primary_property(d, obj)
        if f is not primary:
            required_via = f"/crm-object-schemas/{V}/schemas/{ref}"
    return {
        "path": f"/crm/properties/{V}/{ref}",
        "groups_path": f"/crm/properties/{V}/{ref}/groups",
        "body": gen.property_body(d, f, group=group_name),
        "group": group,
        "required_via": required_via,
    }


def _relationship_payload(d: Design, rel: Any) -> dict[str, Any]:
    requests_ = gen.association_requests(d)
    label = next(r for r in requests_ if r["path"].endswith("/labels") and r["body"].get("name") == rel.key)
    limits = []
    for a, b in ((rel.from_object, rel.to_object), (rel.to_object, rel.from_object)):
        wanted = gen.type_id_name(rel, a, b)
        for r in requests_:
            if "/configurations/" in r["path"] and r["body"]["inputs"][0]["typeId"] == wanted:
                limits.append(
                    {"a_ref": gen.object_ref_for(d, a), "b_ref": gen.object_ref_for(d, b), "request": r}
                )
    return {
        "from_ref": gen.object_ref_for(d, rel.from_object),
        "to_ref": gen.object_ref_for(d, rel.to_object),
        "from_label": rel.from_label,
        "to_label": rel.to_label,
        "label": label,
        "limits": limits,
    }


def _generator_steps(design: Design) -> list[ManualStep]:
    """The generator's manual steps for what the API cannot do, minus the credential and tier set-up."""
    return [
        ManualStep(title=s["title"], reason=s["why"], ui_path=s["where"], done_when=s["done_when"])
        for s in gen.manual_steps(design)
        if s["group"] != "setup"
    ]


def _plan_requirements_path(design: Design) -> str:
    if design.source_path:
        folder = Path(design.source_path).resolve().parent
        try:
            folder = folder.relative_to(REPO_ROOT)
        except ValueError:
            pass
        return str(folder / "hubspot" / "plan-requirements.md")
    return "blueprints/<name>/hubspot/plan-requirements.md"


# --- factory ---------------------------------------------------------------------------------


def make_adapter(
    env: Mapping[str, str],
    *,
    target: str | None = None,
    production: bool = False,
    session: Any = None,
    sleep: Callable[[float], None] = time.sleep,
) -> HubSpotAdapter:
    """Build the adapter from environment variables.

    `HUBSPOT_ACCESS_TOKEN` is a service key or private app token, sent as a Bearer token.
    `HUBSPOT_TARGET` labels the developer test account or sandbox; `target` overrides it. Raises
    `SafetyError` (naming the variable, never a value) when either is missing.
    """
    token = get_credential(TOKEN_VAR, dict(env))
    label = target or env.get(TARGET_VAR, "")
    label = get_credential(TARGET_VAR, {TARGET_VAR: label}) if not label else label
    return HubSpotAdapter(token, target=label, production=production, session=session, sleep=sleep)
