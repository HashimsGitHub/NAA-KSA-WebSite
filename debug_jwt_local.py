import os
import jwt
from datetime import datetime, timezone, timedelta

# 1. Check what secret is actually loaded
# (If you are running in your active terminal, it will look for your env config)
JWT_SECRET = os.environ.get("JWT_SECRET")

print("=" * 60)
print(f"DEBUG: Loaded JWT_SECRET: {repr(JWT_SECRET)}")
print("=" * 60)

if not JWT_SECRET:
    print("⚠️ WARNING: JWT_SECRET environment variable is empty or not set!")
    print("Falling back to a local testing string...")
    JWT_SECRET = "local_debug_fallback_key"

# 2. Mock payload matching an auth token
payload = {
    "sub": "test_user_123",
    "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    "iat": datetime.now(timezone.utc)
}

try:
    # 3. Simulate Token Generation (Login)
    print("\n[Step 1] Attempting to sign and generate token...")
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    print(f"👉 Token generated successfully! Length: {len(token)}")
    
    # 4. Simulate Token Verification (Debug endpoint)
    print("\n[Step 2] Attempting to decode and verify token...")
    decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    print("✅ SUCCESS! Token signature verified perfectly.")
    print(f"👉 Decoded Payload: {decoded}")

except jwt.InvalidSignatureError:
    print("❌ ERROR: InvalidSignatureError! The signature verification failed.")
    print("This means the secret changed or mismatched between encoding and decoding.")
except Exception as e:
    print(f"❌ Unexpected Error: {str(e)}")
print("=" * 60)