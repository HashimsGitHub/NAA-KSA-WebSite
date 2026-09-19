#!/usr/bin/env python3
from pathlib import Path
import re, shutil
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT/"api"/"function_app.py"
APPJS = ROOT/"frontend"/"app.js"
STYLES = ROOT/"frontend"/"styles.css"
TESTS = ROOT/"scripts"/"test_crud_vcnity.py"
PAGES = ROOT/"frontend"/"pages"
OLD_PAGE = PAGES/"alumni.html"
NEW_PAGE = PAGES/"members.html"

for path in [BACKEND, APPJS, STYLES, TESTS, *PAGES.glob("*.html")]:
    if path.exists():
        b = path.with_name(path.name + ".stage2-backup")
        if not b.exists():
            shutil.copy2(path, b)
            print(f"[BACKUP] {b}")

# BACKEND
text = BACKEND.read_text(encoding="utf-8")
text = text.replace('"""KISS backend for NUST KSA Alumni Portal.', '"""VCNITY Safer Digital Community Hub backend.')
text = text.replace('TABLE_ALUMNI_LEGACY = "AlumniProfiles"  # Stage 1 compatibility only\n', "")
text = text.replace('ROLE_ALUMNI_LEGACY = "alumni"  # Stage 1 compatibility only\n', "")
text = text.replace("    ROLE_ALUMNI_LEGACY,\n", "")
text = text.replace("    if role == ROLE_ALUMNI_LEGACY:\n        return ROLE_MEMBER\n", "")
text = text.replace("def sync_member_user(\n    alumni: Dict[str, Any],", "def sync_member_user(\n    member: Dict[str, Any],")
text = re.sub(r"\balumni\.get\(", "member.get(", text)
text = text.replace('clean(member_id or data.get("member_id") or data.get("alumni_id"))', 'clean(member_id or data.get("member_id"))')
text = text.replace('        "alumni_id": member_id,  # Stage 1 compatibility\n', "")
text = text.replace('or existing.get("linked_alumni_id")', 'or existing.get("linked_member_id")')
text = text.replace("Registration is disabled. Alumni accounts are managed through the member database import.", "Registration is disabled. Member accounts are managed by VCNITY administrators.")
start_marker = "# =========================================================\n# Stage 1 legacy API compatibility."
end_marker = '@app.route(route="users", methods=["GET", "POST"])'
if start_marker in text:
    s = text.index(start_marker)
    e = text.index(end_marker, s)
    text = text[:s] + text[e:]
text = re.sub(r"\n{4,}", "\n\n\n", text)
BACKEND.write_text(text, encoding="utf-8")
print("[UPDATE] api/function_app.py")

# FRONTEND APP.JS
js = APPJS.read_text(encoding="utf-8")
repls = [
("adminState = { events: [], knowledge: [], alumni: [] }","adminState = { events: [], knowledge: [], members: [] }"),
("alumniPaging","memberPaging"),("alumniList","memberList"),("adminAlumniList","adminMemberList"),
("renderAlumni","renderMembers"),("alumniPageSize","memberPageSize"),("alumniTargetLabel","memberTargetLabel"),
("setAlumniPage","setMemberPage"),("renderAlumniPager","renderMemberPager"),("renderAlumniPage","renderMemberPage"),
("alumniParams","memberParams"),("loadAlumni","loadMembers"),("alumniPayload","memberPayload"),
("saveAlumni","saveMember"),("editAlumni","editMember"),("resetAlumniForm","resetMemberForm"),
("adminState.alumni","adminState.members"),("countAlumni","countMembers"),
("saveAlumniButton","saveMemberButton"),("resetAlumniButton","resetMemberButton"),("alumniAdminStatus","memberAdminStatus"),
("data-alumni-page-target","data-member-page-target"),("data-alumni-page","data-member-page"),
("dataset.alumniPageTarget","dataset.memberPageTarget"),("dataset.alumniPage","dataset.memberPage"),
("(item.member_id || item.alumni_id)","item.member_id"),("(a.member_id || a.alumni_id)","a.member_id"),
("alumni-item","member-item"),
]
for a,b in repls: js = js.replace(a,b)
js = js.replace("type === 'alumni' ? 'members' : type", "type === 'members' ? 'members' : type")
js = js.replace("type === 'alumni'", "type === 'members'")
APPJS.write_text(js, encoding="utf-8")
print("[UPDATE] frontend/app.js")

# HTML
for path in list(PAGES.glob("*.html")):
    html = path.read_text(encoding="utf-8")
    html = html.replace("/pages/alumni.html","/pages/members.html")
    html = html.replace('data-page="alumni"','data-page="members"')
    html = html.replace('id="alumniList"','id="memberList"')
    html = html.replace('id="adminAlumniList"','id="adminMemberList"')
    html = html.replace('id="countAlumni"','id="countMembers"')
    html = html.replace('id="saveAlumniButton"','id="saveMemberButton"')
    html = html.replace('id="resetAlumniButton"','id="resetMemberButton"')
    html = html.replace('id="alumniAdminStatus"','id="memberAdminStatus"')
    html = html.replace('<option value="alumni">Member</option>','<option value="member">Member</option>')
    html = html.replace("The current backend still uses the original profile fields internally; these labels present them in VCNITY terminology.","Create and maintain VCNITY community member profiles and access roles.")
    path.write_text(html, encoding="utf-8")
if OLD_PAGE.exists():
    if NEW_PAGE.exists(): NEW_PAGE.unlink()
    OLD_PAGE.rename(NEW_PAGE)
    print("[RENAME] alumni.html -> members.html")

# CSS
css = STYLES.read_text(encoding="utf-8").replace(".alumni-item",".member-item")
STYLES.write_text(css, encoding="utf-8")

# TESTS
tests = TESTS.read_text(encoding="utf-8").replace('"alumni_id"','"member_id"').replace("'alumni_id'","'member_id'")
TESTS.write_text(tests, encoding="utf-8")
print("[UPDATE] tests")
print("Stage 2 source cleanup applied.")
