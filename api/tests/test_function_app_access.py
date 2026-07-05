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
