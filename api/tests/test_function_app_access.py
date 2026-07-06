from api import function_app


class DummyReq:
    def __init__(self, method="GET", headers=None, params=None, body=None):
        self.method = method
        self.headers = headers or {}
        self.params = params or {}
        self._body = body or {}
        self.route_params = {}

    def get_json(self):
        return self._body


def test_health():
    res = function_app.health(DummyReq())
    assert res.status_code == 200
    assert b"NUST Alumni API is running" in res.get_body()


def test_events_get_is_public():
    res = function_app.events(DummyReq(method="GET"))
    assert res.status_code in (200, 400)


def test_knowledge_get_requires_login():
    res = function_app.knowledge(DummyReq(method="GET"))
    assert res.status_code == 401
    assert b"Login required" in res.get_body()


def test_alumni_get_requires_login():
    res = function_app.alumni(DummyReq(method="GET"))
    assert res.status_code == 401
    assert b"Login required" in res.get_body()


def test_register_is_disabled():
    res = function_app.register(DummyReq(method="POST", body={}))
    assert res.status_code == 410
    assert b"Registration is disabled" in res.get_body()


def test_admin_summary_requires_admin():
    res = function_app.admin_summary(DummyReq(method="GET"))
    assert res.status_code == 401
    assert b"Login required" in res.get_body()


def test_admin_summary_returns_counts(monkeypatch):
    def fake_require_role(req, allowed):
        assert allowed == [function_app.ROLE_ADMIN]
        return {"email": "admin@example.com", "role": function_app.ROLE_ADMIN}

    def fake_list_table_rows(table_name):
        return {
            function_app.TABLE_ALUMNI: [{}, {}],
            function_app.TABLE_EVENTS: [{}],
            function_app.TABLE_KNOWLEDGE: [{}, {}, {}],
        }[table_name]

    monkeypatch.setattr(function_app, "require_role", fake_require_role)
    monkeypatch.setattr(function_app, "list_table_rows", fake_list_table_rows)

    res = function_app.admin_summary(DummyReq(method="GET"))
    assert res.status_code == 200
    body = res.get_body()
    assert b'"alumni": 2' in body
    assert b'"events": 1' in body
    assert b'"knowledge": 3' in body


def test_admin_summary_alias_uses_same_counts(monkeypatch):
    monkeypatch.setattr(
        function_app,
        "require_role",
        lambda req, allowed: {"email": "admin@example.com", "role": function_app.ROLE_ADMIN},
    )
    monkeypatch.setattr(
        function_app,
        "list_table_rows",
        lambda table_name: [{}] if table_name == function_app.TABLE_EVENTS else [],
    )

    res = function_app.admin_summary_alias(DummyReq(method="GET"))
    assert res.status_code == 200
    assert b'"events": 1' in res.get_body()
