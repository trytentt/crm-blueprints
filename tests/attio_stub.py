"""A requests-session stand-in for Attio. No network.

`FixtureSession` replays recorded responses keyed by "METHOD /path". `FakeAttio` is a small stateful
workspace that implements the endpoints the adapter uses, so a plan can be applied and re-read.
Both record every call in `.calls`. Shapes follow platforms/attio/reference/ (from Attio's OpenAPI spec).
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures" / "attio"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Resp:
    def __init__(self, status: int, body: Any = None, headers: dict[str, str] | None = None) -> None:
        self.status_code = status
        self._body = body
        self.headers = headers or {}
        self.text = json.dumps(body) if body is not None else ""

    def json(self) -> Any:
        if self._body is None:
            raise ValueError("no body")
        return self._body


def error(status: int, code: str, message: str, kind: str = "invalid_request_error") -> Resp:
    return Resp(status, {"status_code": status, "type": kind, "code": code, "message": message})


class FixtureSession:
    """Replays `{"METHOD /path": body}` fixtures. A value may be a list: responses are used in turn."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = {k: (list(v) if isinstance(v, list) else v) for k, v in routes.items()}
        self.calls: list[tuple[str, str, Any, Any]] = []

    def request(self, method, url, params=None, json=None, headers=None, timeout=None):  # noqa: A002
        path = url.replace("https://api.attio.com", "")
        self.calls.append((method, path, params, json))
        route = self.routes.get(f"{method} {path}")
        if route is None:
            return error(404, "not_found", f"no fixture for {method} {path}")
        if isinstance(route, list):
            route = route.pop(0) if len(route) > 1 else route[0]
        if isinstance(route, Resp):
            return route
        return Resp(200, route)


SYSTEM_ATTRS = {
    "people": [("name", "personal-name"), ("email_addresses", "email-address"), ("phone_numbers", "phone-number"),
               ("job_title", "text")],
    "companies": [("name", "text"), ("domains", "domain"), ("description", "text")],
    "deals": [("name", "text"), ("value", "currency"), ("owner", "actor-reference"), ("stage", "status")],
}


def attr_obj(slug, title, typ, *, system=False, multi=False, archived=False, relationship=None):
    return {
        "id": {"workspace_id": "w", "object_id": "o", "attribute_id": f"a-{slug}"},
        "title": title, "description": "", "api_slug": slug, "type": typ,
        "is_system_attribute": system, "is_writable": True, "is_required": False, "is_unique": False,
        "is_multiselect": multi, "is_archived": archived, "config": {},
        **({"relationship": relationship} if relationship else {}),
    }


class FakeAttio:
    """In-memory Attio workspace. Set `fail`, `rate_limit` or `deals` to steer a test."""

    def __init__(self, *, deals: bool = True, active: bool = True, name: str = "Acme Test", slug: str = "acme-test",
                 default_statuses: tuple[str, ...] = ()) -> None:
        self.active, self.name, self.slug = active, name, slug
        self.default_statuses = default_statuses
        self.objects: dict[str, dict] = {}
        self.attrs: dict[tuple[str, str], list[dict]] = {}
        self.subs: dict[tuple[str, str, str, str], list[dict]] = {}
        self.lists: dict[str, dict] = {}
        self.calls: list[tuple[str, str, Any, Any]] = []
        self.fail: dict[str, Resp] = {}  # "METHOD /path" -> response, used once
        self.rate_limit: dict[str, list[Resp]] = {}
        self._n = 0
        for slug_, label in (("people", "Person"), ("companies", "Company")) + ((("deals", "Deal"),) if deals else ()):
            self._add_object(slug_, label, label + "s")
            for a, t in SYSTEM_ATTRS[slug_]:
                self.attrs[("objects", slug_)].append(attr_obj(a, a.title(), t, system=True))

    # -- helpers
    def _id(self) -> str:
        self._n += 1
        return f"id-{self._n}"

    def _add_object(self, slug, singular, plural):
        self.objects[slug] = {"id": {"workspace_id": "w", "object_id": self._id()}, "api_slug": slug,
                              "singular_noun": singular, "plural_noun": plural}
        self.attrs[("objects", slug)] = []

    @property
    def methods(self) -> list[str]:
        return [c[0] for c in self.calls]

    @property
    def writes(self) -> list[tuple[str, str, Any, Any]]:
        return [c for c in self.calls if c[0] != "GET"]

    # -- dispatch
    def request(self, method, url, params=None, json=None, headers=None, timeout=None):  # noqa: A002
        path = url.replace("https://api.attio.com", "")
        self.calls.append((method, path, params, copy.deepcopy(json)))
        key = f"{method} {path}"
        if key in self.rate_limit and self.rate_limit[key]:
            return self.rate_limit[key].pop(0)
        if key in self.fail:
            return self.fail.pop(key)
        if method == "DELETE":
            return error(405, "method_not_allowed", "no deletes in this stub")
        data = (json or {}).get("data", {})
        params = params or {}
        if path == "/v2/self":
            if not self.active:
                return Resp(200, {"active": False})
            return Resp(200, {"active": True, "scope": "object_configuration:read-write list_configuration:read-write",
                              "workspace_id": "w", "workspace_name": self.name, "workspace_slug": self.slug})
        if path == "/v2/objects":
            if method == "GET":
                return Resp(200, {"data": list(self.objects.values())})
            if data["api_slug"] in self.objects:
                return error(409, "slug_conflict", "An object with the same API slug already exists.")
            self._add_object(data["api_slug"], data["singular_noun"], data["plural_noun"])
            self.attrs[("objects", data["api_slug"])].append(attr_obj("name", "Name", "text", system=True))
            return Resp(200, {"data": self.objects[data["api_slug"]]})
        m = re.match(r"^/v2/objects/([^/]+)$", path)
        if m:
            obj = self.objects.get(m[1])
            if obj is None:
                return error(404, "not_found", "Object not found")
            if method == "PATCH":
                obj.update({k: v for k, v in data.items()})
            return Resp(200, {"data": obj})
        if path == "/v2/lists":
            if method == "GET":
                return Resp(200, {"data": list(self.lists.values())})
            if data["api_slug"] in self.lists:
                return error(409, "slug_conflict", "A list with the same API slug already exists.")
            if data["parent_object"] not in self.objects:
                return error(404, "not_found", "Parent object not found")
            self.lists[data["api_slug"]] = {"id": {"workspace_id": "w", "list_id": self._id()},
                                            "api_slug": data["api_slug"], "name": data["name"],
                                            "parent_object": [data["parent_object"]]}
            self.attrs[("lists", data["api_slug"])] = []
            return Resp(200, {"data": self.lists[data["api_slug"]]})
        m = re.match(r"^/v2/lists/([^/]+)$", path)
        if m:
            return Resp(200, {"data": self.lists[m[1]]}) if m[1] in self.lists else error(404, "not_found", "no list")
        m = re.match(r"^/v2/(objects|lists)/([^/]+)/attributes$", path)
        if m:
            return self._attributes(method, m[1], m[2], data, params)
        m = re.match(r"^/v2/(objects|lists)/([^/]+)/attributes/([^/]+)$", path)
        if m:
            a = next((x for x in self.attrs.get((m[1], m[2]), []) if x["api_slug"] == m[3]), None)
            if a is None:
                return error(404, "not_found", "Attribute not found")
            if method == "PATCH":
                a.update(data)
            return Resp(200, {"data": a})
        m = re.match(r"^/v2/(objects|lists)/([^/]+)/attributes/([^/]+)/(options|statuses)(?:/([^/]+))?$", path)
        if m:
            return self._sub(method, m, data, params)
        return error(404, "not_found", f"unknown path {path}")

    def _attributes(self, method, target, parent, data, params):
        if (target, parent) not in self.attrs:
            return error(404, "not_found", "Parent not found")
        items = self.attrs[(target, parent)]
        if method == "GET":
            shown = [a for a in items if params.get("show_archived") == "true" or not a["is_archived"]]
            lo = int(params.get("offset", 0))
            return Resp(200, {"data": shown[lo: lo + int(params.get("limit", 100))]})
        if any(a["api_slug"] == data["api_slug"] for a in items):
            return error(409, "slug_conflict", "An attribute with the same API slug already exists.")
        a = attr_obj(data["api_slug"], data["title"], data["type"], multi=data["is_multiselect"])
        rel = data.get("relationship")
        if rel:
            other = (target, rel["object"])
            a["relationship"] = {"object_slug": rel["object"], "title": rel["title"],
                                 "api_slug": rel["api_slug"], "is_multiselect": rel["is_multiselect"]}
            self.attrs[other].append(attr_obj(
                rel["api_slug"], rel["title"], "record-reference", multi=rel["is_multiselect"],
                relationship={"object_slug": parent, "title": data["title"], "api_slug": data["api_slug"],
                              "is_multiselect": data["is_multiselect"]}))
        items.append(a)
        if data["type"] == "status":
            self.subs[(target, parent, data["api_slug"], "statuses")] = [
                {"id": {"status_id": self._id()}, "title": t, "is_archived": False, "celebration_enabled": False}
                for t in self.default_statuses
            ]
        return Resp(200, {"data": a})

    def _sub(self, method, m, data, params):
        key = (m[1], m[2], m[3], m[4])
        items = self.subs.setdefault(key, [])
        idkey = "option_id" if m[4] == "options" else "status_id"
        if m[5] is None:
            if method == "GET":
                return Resp(200, {"data": [i for i in items
                                           if params.get("show_archived") == "true" or not i["is_archived"]]})
            if any(i["title"] == data["title"] for i in items):
                return error(409, "slug_conflict", "There is already another item with the title.")
            item = {"id": {idkey: self._id()}, "title": data["title"], "is_archived": False}
            if m[4] == "statuses":
                item["celebration_enabled"] = data.get("celebration_enabled", False)
            items.append(item)
            return Resp(200, {"data": item})
        item = next((i for i in items if i["id"][idkey] == m[5] or i["title"] == m[5]), None)
        if item is None:
            return error(404, "not_found", "Not found")
        if method == "PATCH":
            item.update(data)
        return Resp(200, {"data": item})

    # -- reading what was built
    def titles(self, target, parent, attr, kind, *, archived=False):
        return [i["title"] for i in self.subs.get((target, parent, attr, kind), []) if i["is_archived"] == archived]
