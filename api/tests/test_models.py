from models.user import User
from models.alumni import AlumniProfile
from models.session import Session


user = User(
    user_id="u1",
    email="test@example.com",
    full_name="Test User",
)

assert user.role == "alumni"
assert user.status == "pending"

alumni = AlumniProfile(
    alumni_id="a1",
    full_name="Test Alumni",
    city="Riyadh",
    graduation_year="2015",
)

assert alumni.visibility == "visible"
assert alumni.status == "active"

session = Session(
    session_id="s1",
    email="test@example.com",
    user_id="u1",
    role="alumni",
    status="approved",
    created_at="now",
    expires_at="later",
)

assert session.revoked is False

print("SUCCESS")
