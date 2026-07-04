from api.shared.response_utils import (
    success_response,
    error_response,
    unauthorized_response,
    forbidden_response,
)


ok = success_response("Test success", {"value": 123})
print(ok)
assert ok["success"] is True
assert ok["data"]["value"] == 123

err = error_response("Test error", ["Something failed"])
print(err)
assert err["success"] is False
assert len(err["errors"]) == 1

unauth = unauthorized_response()
assert unauth["success"] is False

forbidden = forbidden_response()
assert forbidden["success"] is False

print("\nSUCCESS")