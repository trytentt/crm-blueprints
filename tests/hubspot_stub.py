"""An in-memory HubSpot for tests: a `requests.Session` stand-in that answers the endpoints the adapter uses.

It holds mutable account state seeded from `tests/fixtures/hubspot/`. It has no network. Every call is
recorded in `calls` as (method, path) so a test can assert what was and was not sent.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures" / "hubspot"
STANDARD = {"companies": "0-2", "contacts": "0-1", "deals": "0-3"}
V = "2026-09"


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Resp:
    def __init__(self, status: int, data: Any = None, headers: dict[str, str] | None = None) -> None:
        self.status_code = status
        self._data = data
        self.text = "" if data is None else json.dumps(data)
        self.headers = headers or {}

    def json(self) -> Any:
        if self._data is None:
            raise ValueError("no body")
        return self._data


class FakeHubSpot:
    """Stateful stub. `enterprise=False` makes the custom-object limits call return 403."""

    def __init__(self, *, enterprise: bool = True, max_objects: int = 10, portal: int = 12345678,
                 account_type: str | None = "DEVELOPER_TEST", portal_name: str | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self.bodies: list[tuple[str, str, Any]] = []
        self.enterprise = enterprise
        self.max_objects = max_objects
        self.portal = portal
        self.account_type = account_type
        self.portal_name = portal_name
        self.schemas: dict[str, dict[str, Any]] = {}  # objectTypeId -> schema
        native = fixture("native_properties.json")
        self.props: dict[str, dict[str, dict[str, Any]]] = {
            STANDARD[k]: {p["name"]: copy.deepcopy(p) for p in v} for k, v in native.items()
        }
        self.groups: dict[str, dict[str, dict[str, Any]]] = {t: {} for t in STANDARD.values()}
        self.pipelines: dict[str, dict[str, dict[str, Any]]] = {"0-3": {"default": fixture("default_deal_pipeline.json")}}
        self.labels: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.limits: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self._next_obj = 3000000
        self._next_type = 100
        self.queue: list[tuple[re.Pattern[str], str | None, Resp]] = []  # one-shot canned replies
        self.sleeps: list[float] = []

    # -- test controls --------------------------------------------------------------------

    def reply_once(self, method: str | None, path_regex: str, resp: Resp) -> None:
        self.queue.append((re.compile(path_regex), method, resp))

    def writes(self) -> list[tuple[str, str]]:
        return [c for c in self.calls if c[0] != "GET"]

    # -- session API ----------------------------------------------------------------------

    def request(self, method: str, url: str, headers: dict[str, str] | None = None, params: Any = None,
                json: Any = None, timeout: Any = None) -> Resp:  # noqa: A002
        assert (headers or {}).get("Authorization", "").startswith("Bearer "), "no bearer token sent"
        path = url.replace("https://api.hubapi.com", "")
        self.calls.append((method, path))
        self.bodies.append((method, path, copy.deepcopy(json)))
        for i, (rx, m, resp) in enumerate(self.queue):
            if rx.search(path) and (m is None or m == method):
                self.queue.pop(i)
                return resp
        return self._route(method, path, json)

    # -- helpers --------------------------------------------------------------------------

    def _tid(self, ref: str) -> str | None:
        if ref in STANDARD:
            return STANDARD[ref]
        if ref in self.schemas:
            return ref
        for tid, s in self.schemas.items():
            if ref in (s["fullyQualifiedName"], s["name"]):
                return tid
        return ref if ref in STANDARD.values() else None

    def _route(self, method: str, path: str, body: Any) -> Resp:
        p = path.split("?")[0]
        if p == "/account-info/v3/details":
            info = {**fixture("account_info.json"), "portalId": self.portal}
            if self.account_type is None:
                info.pop("accountType")
            else:
                info["accountType"] = self.account_type
            if self.portal_name is not None:
                info["portalName"] = self.portal_name
            return Resp(200, info)
        if p == f"/crm/limits/{V}/custom-object-types":
            if not self.enterprise:
                return Resp(403, {"status": "error", "message": "feature not available", "category": "FORBIDDEN"})
            return Resp(200, {"results": [{"name": "custom-object-types", "usage": len(self.schemas), "maxLimit": self.max_objects}]})
        if p == f"/crm-object-schemas/{V}/schemas":
            if method == "GET":
                return Resp(200, {"results": list(self.schemas.values())})
            return self._create_schema(body)
        m = re.fullmatch(rf"/crm-object-schemas/{V}/schemas/([^/]+)", p)
        if m:
            tid = self._tid(m.group(1))
            if tid not in self.schemas:
                return Resp(404, {"status": "error", "message": "not found"})
            if method == "GET":
                return Resp(200, self.schemas[tid])
            self.schemas[tid].update({k: v for k, v in body.items() if k != "clearDescription"})
            return Resp(200, self.schemas[tid])
        m = re.fullmatch(rf"/crm/properties/{V}/([^/]+)/groups(?:/([^/]+))?", p)
        if m:
            return self._groups(method, m.group(1), m.group(2), body)
        m = re.fullmatch(rf"/crm/properties/{V}/([^/]+)(?:/([^/]+))?", p)
        if m:
            return self._props(method, m.group(1), m.group(2), body)
        m = re.fullmatch(rf"/crm/pipelines/{V}/([^/]+)(?:/([^/]+))?(?:/stages(?:/([^/]+))?)?", p)
        if m:
            return self._pipelines(method, p, m.group(1), m.group(2), m.group(3), body)
        m = re.fullmatch(rf"/crm/associations/{V}/definitions/configurations/([^/]+)/([^/]+)(/batch/create)?", p)
        if m:
            a, b = self._tid(m.group(1)), self._tid(m.group(2))
            if method == "GET":
                return Resp(200, {"results": self.limits.get((a, b), [])})
            for inp in body["inputs"]:
                assert isinstance(inp["typeId"], int), "unresolved typeId sent"
                self.limits.setdefault((a, b), []).append(dict(inp))
            return Resp(201, {"results": body["inputs"]})
        m = re.fullmatch(rf"/crm/associations/{V}/([^/]+)/([^/]+)/labels", p)
        if m:
            a, b = self._tid(m.group(1)), self._tid(m.group(2))
            if a is None or b is None:
                return Resp(404, {"status": "error", "message": "unknown object"})
            if method == "GET":
                return Resp(200, {"results": self.labels.get((a, b), [])})
            t1, t2 = self._next_type, self._next_type + 1
            self._next_type += 2
            e1 = {"category": "USER_DEFINED", "typeId": t1, "label": body["label"]}
            e2 = {"category": "USER_DEFINED", "typeId": t2, "label": body["inverseLabel"]}
            self.labels.setdefault((a, b), []).append(e1)
            self.labels.setdefault((b, a), []).append(e2)
            return Resp(201, {"results": [e1, e2]})
        return Resp(404, {"status": "error", "message": f"stub has no route for {method} {p}"})

    def _create_schema(self, body: dict[str, Any]) -> Resp:
        for key in ("name", "labels", "properties", "requiredProperties", "searchableProperties",
                    "secondaryDisplayProperties", "associatedObjects", "allowsSensitiveProperties",
                    "shouldCreateSameObjectAssociation"):
            if key not in body:
                return Resp(400, {"status": "error", "message": f"missing {key}", "category": "VALIDATION_ERROR"})
        for tid in body["associatedObjects"]:
            if "{" in tid or (tid not in STANDARD.values() and tid not in self.schemas):
                return Resp(400, {"status": "error", "message": f"bad associatedObjects {tid}", "category": "VALIDATION_ERROR"})
        if len(self.schemas) >= self.max_objects:
            return Resp(403, {"status": "error", "message": "limit reached", "category": "FORBIDDEN"})
        self._next_obj += 1
        tid = f"2-{self._next_obj}"
        schema = copy.deepcopy(body)
        schema.update(objectTypeId=tid, fullyQualifiedName=f"p{self.portal}_{body['name']}", archived=False)
        self.schemas[tid] = schema
        self.props[tid] = {}
        self.groups[tid] = {}
        for pr in body["properties"]:
            self.props[tid][pr["name"]] = {**pr, "groupName": "default", "hubspotDefined": False,
                                           "modificationMetadata": {"readOnlyDefinition": False}}
        self.pipelines[tid] = {}
        for a in body["associatedObjects"]:
            self.labels.setdefault((tid, a), [])
        return Resp(201, schema)

    def _groups(self, method: str, ref: str, name: str | None, body: Any) -> Resp:
        tid = self._tid(ref)
        if tid is None:
            return Resp(404, {"status": "error", "message": "unknown object"})
        if method == "GET" and name:
            g = self.groups[tid].get(name)
            return Resp(200, g) if g else Resp(404, {"status": "error", "message": "no group"})
        if method == "GET":
            return Resp(200, {"results": list(self.groups[tid].values())})
        self.groups[tid][body["name"]] = dict(body)
        return Resp(201, body)

    def _props(self, method: str, ref: str, name: str | None, body: Any) -> Resp:
        tid = self._tid(ref)
        if tid is None:
            return Resp(404, {"status": "error", "message": "unknown object"})
        props = self.props[tid]
        if method == "GET" and name is None:
            return Resp(200, {"results": list(props.values())})
        if method == "GET":
            return Resp(200, props[name]) if name in props else Resp(404, {"status": "error", "message": "no property"})
        if method == "POST":
            if body["groupName"] not in self.groups[tid] and not body["groupName"].endswith("information"):
                return Resp(400, {"status": "error", "message": "group does not exist", "category": "VALIDATION_ERROR"})
            props[body["name"]] = {**body, "hubspotDefined": False, "modificationMetadata": {"readOnlyDefinition": False}}
            return Resp(201, props[body["name"]])
        if name not in props:
            return Resp(404, {"status": "error", "message": "no property"})
        props[name].update(body)
        return Resp(200, props[name])

    def _pipelines(self, method: str, path: str, ref: str, pid: str | None, sid: str | None, body: Any) -> Resp:
        tid = self._tid(ref)
        if tid is None or tid not in self.pipelines:
            return Resp(404, {"status": "error", "message": "unknown object"})
        pls = self.pipelines[tid]
        is_stage = "/stages" in path
        if not pid:
            if method == "GET":
                return Resp(200, {"results": list(pls.values())})
            pl = {"id": body["pipelineId"], "label": body["label"], "displayOrder": body["displayOrder"],
                  "stages": [{"id": s["stageId"], "label": s["label"], "displayOrder": s["displayOrder"],
                              "metadata": self._meta(tid, s["metadata"])} for s in body["stages"]]}
            for s in body["stages"]:
                if not isinstance(s["metadata"], dict):
                    return Resp(400, {"status": "error", "message": "metadata required"})
            pls[pl["id"]] = pl
            return Resp(201, pl)
        pl = pls.get(pid)
        if pl is None:
            return Resp(404, {"status": "error", "message": "no pipeline"})
        if not is_stage:
            return Resp(200, pl)
        if method == "POST":
            pl["stages"].append({"id": body["stageId"], "label": body["label"], "displayOrder": body["displayOrder"],
                                 "metadata": self._meta(tid, body["metadata"])})
            return Resp(201, pl["stages"][-1])
        stage = next((s for s in pl["stages"] if s["id"] == sid), None)
        if stage is None:
            return Resp(404, {"status": "error", "message": "no stage"})
        if method == "GET":
            return Resp(200, stage)
        for k, v in body.items():
            if k == "metadata":
                stage["metadata"].update(self._meta(tid, v))
            else:
                stage[k] = v
        return Resp(200, stage)

    @staticmethod
    def _meta(tid: str, meta: dict[str, str]) -> dict[str, str]:
        out = dict(meta)
        if tid == "0-3" and "probability" in out:  # deals read back with isClosed (pipelines.md)
            out["isClosed"] = "true" if out["probability"] in ("0.0", "1.0") else "false"
        return out
