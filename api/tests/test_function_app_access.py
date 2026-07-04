import json

from api import function_app


class FakeRequest:
    def __init__(self, method="GET", params=None, headers=None, payload=None):
        self.method = method
        self.params = params or {}
        self.headers = headers or {}
        self.route_params = {}
        self._payload = payload or {}

    def get_json(self):
        return self._payload


class FakeContentRepository:
    def __init__(self, table_key):
        self.table_key = table_key

    def list(self, published_only=True, category=""):
        return [{"id": "1", "title": f"{self.table_key}:{category}", "status": "published"}]

    def create(self, item, created_by):
        return {"id": "2", **item, "created_by": created_by}


def response_json(resp):
    return json.loads(resp.get_body().decode("utf-8"))


def test_events_get_is_public(monkeypatch):
    monkeypatch.setattr(function_app, "ContentRepository", FakeContentRepository)
    monkeypatch.setattr(function_app, "current_user", lambda req: {})

    resp = function_app.events(FakeRequest("GET"))
    payload = response_json(resp)

    assert resp.status_code == 200
    assert payload["success"] is True
    assert payload["data"][0]["title"] == "events:event"


def test_knowledge_get_requires_login(monkeypatch):
    monkeypatch.setattr(function_app, "ContentRepository", FakeContentRepository)
    monkeypatch.setattr(function_app, "current_user", lambda req: {})

    resp = function_app.knowledge(FakeRequest("GET"))
    payload = response_json(resp)

    assert resp.status_code == 401
    assert payload["success"] is False
    assert payload["message"] == "Login required"


def test_knowledge_get_after_login(monkeypatch):
    monkeypatch.setattr(function_app, "ContentRepository", FakeContentRepository)
    monkeypatch.setattr(function_app, "current_user", lambda req: {"sub": "member@nust.edu", "role": "alumni"})

    resp = function_app.knowledge(FakeRequest("GET"))
    payload = response_json(resp)

    assert resp.status_code == 200
    assert payload["success"] is True
    assert payload["data"][0]["title"] == "blogs:knowledge"


def test_alumni_search_requires_login(monkeypatch):
    monkeypatch.setattr(function_app, "current_user", lambda req: {})

    resp = function_app.alumni(FakeRequest("GET"))
    payload = response_json(resp)

    assert resp.status_code == 401
    assert payload["success"] is False
    assert payload["message"] == "Login required"
