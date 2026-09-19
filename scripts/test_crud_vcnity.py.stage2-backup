#!/usr/bin/env python3
import getpass
import json
import sys
import uuid
from urllib import error, request

BASE_URL = "http://localhost:7071/api"
PASS = FAIL = WARN = 0


def api(method, path, data=None, session_id=None):
    url = f"{BASE_URL}{path}"
    body = None if data is None else json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if session_id:
        headers["X-Session-Id"] = session_id
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"success": False, "message": raw}
        return exc.code, payload
    except Exception as exc:
        return 0, {"success": False, "message": str(exc)}


def check(condition, label, details=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"[PASS] {label}")
        return True
    FAIL += 1
    print(f"[FAIL] {label}")
    if details:
        print(f"       {details}")
    return False


def warn(label, details=""):
    global WARN
    WARN += 1
    print(f"[WARN] {label}")
    if details:
        print(f"       {details}")


def payload_data(status, payload, expected, label):
    if not check(status == expected and payload.get("success") is True, label, f"HTTP {status}: {payload}"):
        return None
    return payload.get("data")


def find_id(items, key, value):
    for item in items or []:
        if item.get(key) == value:
            return item
    return None


def login():
    print("VCNITY CRUD test suite")
    print("----------------------")
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password: ")
    status, payload = api("POST", "/auth/login", {"email": email, "password": password})
    data = payload_data(status, payload, 200, "Admin login")
    if not data:
        sys.exit(1)
    check(data.get("user", {}).get("role") == "admin", "Logged-in role is admin")
    return data["session_id"]


def test_health():
    status, payload = api("GET", "/health")
    data = payload_data(status, payload, 200, "Health endpoint")
    if data:
        check(data.get("community_id") == "VCNITY-DEV", "API reports COMMUNITY_ID=VCNITY-DEV", f"Reported: {data.get('community_id')!r}")


def test_events(session_id, token):
    item_id = f"crud-event-{token}"
    created = False
    print("\n=== Events CRUD ===")
    try:
        event = {"id": item_id, "title": f"CRUD Event {token}", "summary": "Automated CRUD test event.", "description": "Created by the automated VCNITY CRUD suite.", "event_date": "2026-12-12", "venue": "Test Venue", "city": "Brisbane", "tags": "crud,test", "status": "published", "cover_image_url": ""}
        status, payload = api("POST", "/events", event, session_id)
        created = bool(payload_data(status, payload, 201, "Events CREATE"))
        status, payload = api("GET", "/events")
        items = payload_data(status, payload, 200, "Events READ list")
        check(find_id(items, "id", item_id) is not None, "Events READ created record")
        update = {"title": f"CRUD Event UPDATED {token}", "summary": "Updated by CRUD test.", "city": "Ipswich"}
        status, payload = api("PUT", f"/events/{item_id}", update, session_id)
        data = payload_data(status, payload, 200, "Events UPDATE")
        if data:
            check(data.get("title") == update["title"], "Events UPDATE title")
            check(data.get("city") == "Ipswich", "Events UPDATE city")
        status, payload = api("GET", "/events")
        items = payload_data(status, payload, 200, "Events READ after update")
        found = find_id(items, "id", item_id)
        check(bool(found and found.get("title") == update["title"]), "Events READ verifies update")
        status, payload = api("DELETE", f"/events/{item_id}", session_id=session_id)
        payload_data(status, payload, 200, "Events DELETE")
        created = False
        status, payload = api("GET", "/events")
        items = payload_data(status, payload, 200, "Events READ after delete")
        check(find_id(items, "id", item_id) is None, "Events DELETE verified")
    finally:
        if created:
            api("DELETE", f"/events/{item_id}", session_id=session_id)


def test_knowledge(session_id, token):
    item_id = f"crud-knowledge-{token}"
    created = False
    print("\n=== Knowledge Hub CRUD ===")
    try:
        article = {"id": item_id, "title": f"CRUD Knowledge {token}", "summary": "Automated CRUD test knowledge article.", "body": "Initial article body created by the VCNITY CRUD suite.", "tags": "crud,test", "status": "published", "cover_image_url": ""}
        status, payload = api("POST", "/knowledge", article, session_id)
        created = bool(payload_data(status, payload, 201, "Knowledge CREATE"))
        status, payload = api("GET", "/knowledge", session_id=session_id)
        items = payload_data(status, payload, 200, "Knowledge READ list")
        check(find_id(items, "id", item_id) is not None, "Knowledge READ created record")
        update = {"title": f"CRUD Knowledge UPDATED {token}", "body": "Updated article body.", "tags": "crud,test,updated"}
        status, payload = api("PUT", f"/knowledge/{item_id}", update, session_id)
        data = payload_data(status, payload, 200, "Knowledge UPDATE")
        if data:
            check(data.get("title") == update["title"], "Knowledge UPDATE title")
            check(data.get("body") == update["body"], "Knowledge UPDATE body")
        status, payload = api("GET", "/knowledge", session_id=session_id)
        items = payload_data(status, payload, 200, "Knowledge READ after update")
        found = find_id(items, "id", item_id)
        check(bool(found and found.get("title") == update["title"]), "Knowledge READ verifies update")
        status, payload = api("DELETE", f"/knowledge/{item_id}", session_id=session_id)
        payload_data(status, payload, 200, "Knowledge DELETE")
        created = False
        status, payload = api("GET", "/knowledge", session_id=session_id)
        items = payload_data(status, payload, 200, "Knowledge READ after delete")
        check(find_id(items, "id", item_id) is None, "Knowledge DELETE verified")
    finally:
        if created:
            api("DELETE", f"/knowledge/{item_id}", session_id=session_id)


def test_members(session_id, token):
    member_id = f"crud-member-{token}"

    original_email = f"crud-{token}@example.com"
    original_mobile = "0400000999"

    new_email = f"crud-updated-{token}@example.com"
    new_mobile = "0400000888"

    created = False

    print("\n=== Community Member CRUD ===")

    try:
        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------
        member = {
            "member_id": member_id,
            "full_name": f"CRUD Test Member {token}",
            "email": original_email,
            "mobile": original_mobile,
            "city": "Brisbane",
            "country": "Australia",
            "degree": "Community Member",
            "department": "Test Community",
            "graduation_year": "2026",
            "current_company": "VCNITY Test Organisation",
            "current_position": "Test Member",
            "industry": "Community",
            "linkedin_url": "",
            "bio": "Temporary member created by the automated CRUD suite.",
            "skills": "testing,community",
            "profile_image_url": "",
            "role": "member",
            "status": "active",
            "visibility": "visible",
            "show_email": True,
            "show_mobile": False,
        }

        status, payload = api(
            "POST",
            "/members",
            member,
            session_id,
        )

        created = bool(
            payload_data(
                status,
                payload,
                201,
                "Members CREATE",
            )
        )

        # -------------------------------------------------
        # READ CREATED MEMBER
        # -------------------------------------------------
        status, payload = api(
            "GET",
            "/members",
            session_id=session_id,
        )

        items = payload_data(
            status,
            payload,
            200,
            "Members READ list",
        )

        check(
            find_id(items, "member_id", member_id) is not None,
            "Members READ created record",
        )

        # -------------------------------------------------
        # VERIFY INITIAL LOGIN
        # username = email
        # password = mobile
        # -------------------------------------------------
        status, payload = api(
            "POST",
            "/auth/login",
            {
                "email": original_email,
                "password": original_mobile,
            },
        )

        check(
            status == 200 and payload.get("success") is True,
            "Member initial login works with email/mobile",
            f"HTTP {status}: {payload}",
        )

        # -------------------------------------------------
        # NORMAL PROFILE UPDATE
        # -------------------------------------------------
        update = {
            "full_name": f"CRUD Test Member UPDATED {token}",
            "city": "Logan",
            "current_position": "Updated Test Role",
            "skills": "testing,community,updated",
        }

        status, payload = api(
            "PUT",
            f"/members/{member_id}",
            update,
            session_id,
        )

        data = payload_data(
            status,
            payload,
            200,
            "Members UPDATE",
        )

        if data:
            check(
                data.get("full_name") == update["full_name"],
                "Members UPDATE name",
            )

            check(
                data.get("city") == "Logan",
                "Members UPDATE city",
            )

        # -------------------------------------------------
        # VERIFY NORMAL UPDATE
        # -------------------------------------------------
        status, payload = api(
            "GET",
            "/members",
            session_id=session_id,
        )

        items = payload_data(
            status,
            payload,
            200,
            "Members READ after update",
        )

        found = find_id(
            items,
            "alumni_id",
            member_id,
        )

        check(
            bool(
                found
                and found.get("current_position")
                == "Updated Test Role"
            ),
            "Members READ verifies update",
        )

        # -------------------------------------------------
        # CHANGE EMAIL + MOBILE
        #
        # Expected:
        # username changes to new_email
        # password changes to new_mobile
        # old UserAccounts record removed
        # -------------------------------------------------
        credential_update = {
            "email": new_email,
            "mobile": new_mobile,
        }

        status, payload = api(
            "PUT",
            f"/members/{member_id}",
            credential_update,
            session_id,
        )

        data = payload_data(
            status,
            payload,
            200,
            "Members UPDATE email/mobile",
        )

        if data:
            check(
                data.get("email") == new_email,
                "Members UPDATE email verified",
            )

            # show_mobile=False means the public member
            # response should not expose the mobile number.
            check(
                data.get("mobile", "") == "",
                "Member mobile remains hidden publicly",
            )

        # -------------------------------------------------
        # VERIFY MEMBER PROFILE NOW USES NEW EMAIL
        # -------------------------------------------------
        status, payload = api(
            "GET",
            "/members",
            session_id=session_id,
        )

        items = payload_data(
            status,
            payload,
            200,
            "Members READ after email/mobile update",
        )

        found = find_id(
            items,
            "alumni_id",
            member_id,
        )

        check(
            bool(
                found
                and found.get("email") == new_email
            ),
            "Member profile contains new email",
        )

        # -------------------------------------------------
        # VERIFY USERACCOUNTS INTEGRITY
        # -------------------------------------------------
        status, payload = api(
            "GET",
            "/users",
            session_id=session_id,
        )

        users = payload_data(
            status,
            payload,
            200,
            "Users READ after member email change",
        )

        old_account = find_id(
            users,
            "email",
            original_email,
        )

        new_account = find_id(
            users,
            "email",
            new_email,
        )

        check(
            old_account is None,
            "Old member login removed after email change",
        )

        check(
            new_account is not None,
            "New member login created after email change",
        )

        if new_account:
            check(
                new_account.get("mobile") == new_mobile,
                "User account contains updated mobile",
            )

            check(
                new_account.get("role") == "member",
                "Member role preserved after email change",
            )

            check(
                new_account.get("status") == "approved",
                "Member login remains approved",
            )

        # -------------------------------------------------
        # VERIFY NEW CREDENTIALS WORK
        # -------------------------------------------------
        status, payload = api(
            "POST",
            "/auth/login",
            {
                "email": new_email,
                "password": new_mobile,
            },
        )

        check(
            status == 200 and payload.get("success") is True,
            "Member login works with new email/mobile",
            f"HTTP {status}: {payload}",
        )

        # -------------------------------------------------
        # VERIFY OLD EMAIL + OLD MOBILE NO LONGER WORK
        # -------------------------------------------------
        status, payload = api(
            "POST",
            "/auth/login",
            {
                "email": original_email,
                "password": original_mobile,
            },
        )

        check(
            status == 401,
            "Old member credentials rejected after email change",
            f"HTTP {status}: {payload}",
        )

        # -------------------------------------------------
        # VERIFY NEW EMAIL + OLD MOBILE ALSO FAILS
        #
        # This proves the password changed when mobile changed.
        # -------------------------------------------------
        status, payload = api(
            "POST",
            "/auth/login",
            {
                "email": new_email,
                "password": original_mobile,
            },
        )

        check(
            status == 401,
            "Old mobile password rejected after mobile change",
            f"HTTP {status}: {payload}",
        )

        # -------------------------------------------------
        # DELETE MEMBER
        # -------------------------------------------------
        status, payload = api(
            "DELETE",
            f"/members/{member_id}",
            session_id=session_id,
        )

        payload_data(
            status,
            payload,
            200,
            "Members DELETE",
        )

        created = False

        # -------------------------------------------------
        # VERIFY PROFILE DELETED
        # -------------------------------------------------
        status, payload = api(
            "GET",
            "/members",
            session_id=session_id,
        )

        items = payload_data(
            status,
            payload,
            200,
            "Members READ after delete",
        )

        check(
            find_id(
                items,
                "alumni_id",
                member_id,
            )
            is None,
            "Members DELETE profile verified",
        )

        # -------------------------------------------------
        # VERIFY LINKED USERACCOUNT ALSO DELETED
        #
        # Important: check new_email because that is now
        # the member's current login identity.
        # -------------------------------------------------
        status, payload = api(
            "GET",
            "/users",
            session_id=session_id,
        )

        users = payload_data(
            status,
            payload,
            200,
            "Users READ after member delete",
        )

        orphan_new = find_id(
            users,
            "email",
            new_email,
        )

        orphan_old = find_id(
            users,
            "email",
            original_email,
        )

        check(
            orphan_new is None,
            "Member DELETE removed current linked user account",
        )

        check(
            orphan_old is None,
            "No old-email user account remains",
        )

        # -------------------------------------------------
        # VERIFY DELETED MEMBER CAN NO LONGER LOGIN
        # -------------------------------------------------
        status, payload = api(
            "POST",
            "/auth/login",
            {
                "email": new_email,
                "password": new_mobile,
            },
        )

        check(
            status == 401,
            "Deleted member login rejected",
            f"HTTP {status}: {payload}",
        )

    finally:
        # Emergency cleanup if the test fails halfway through.
        if created:
            api(
                "DELETE",
                f"/members/{member_id}",
                session_id=session_id,
            )


def test_dashboard(session_id):
    print("\n=== Admin Dashboard ===")
    status, payload = api("GET", "/dashboard/summary", session_id=session_id)
    data = payload_data(status, payload, 200, "Dashboard summary")
    if data:
        check(all(k in data for k in ("members", "events", "knowledge")), "Dashboard summary fields")


def main():
    session_id = login()
    token = uuid.uuid4().hex[:8]
    test_health()
    test_events(session_id, token)
    test_knowledge(session_id, token)
    test_members(session_id, token)
    test_dashboard(session_id)
    print("\n==============================")
    print("VCNITY CRUD TEST SUMMARY")
    print("==============================")
    print(f"PASS : {PASS}")
    print(f"FAIL : {FAIL}")
    print(f"WARN : {WARN}")
    if FAIL:
        print("\nResult: FAILED")
        sys.exit(1)
    print("\nResult: PASSED WITH WARNINGS" if WARN else "\nResult: PASSED")


if __name__ == "__main__":
    main()
