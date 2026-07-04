import pandas as pd
from pathlib import Path

from services.import_service import ImportService


test_file = Path("scripts/test_alumni_import.csv")

df = pd.DataFrame(
    [
        {
            "Full Name": "Import Test Alumni 1",
            "Email Address": "import1@example.com",
            "Mobile No": "+966500000101",
            "City": "Riyadh",
            "Country": "Saudi Arabia",
            "Degree": "BS Computer Science",
            "Graduation Year": "2015",
            "Current Employer": "Example Company",
            "LinkedIn Profile": "https://linkedin.com/in/import1",
        },
        {
            "Full Name": "Import Test Alumni 2",
            "Email Address": "import2@example.com",
            "Mobile No": "+966500000102",
            "City": "Jeddah",
            "Country": "Saudi Arabia",
            "Degree": "MS Engineering",
            "Graduation Year": "2018",
            "Current Employer": "Another Company",
            "LinkedIn Profile": "https://linkedin.com/in/import2",
        },
    ]
)

df.to_csv(test_file, index=False)

service = ImportService()

preview = service.preview_import(str(test_file))

print("Preview:")
print(preview)

assert preview["success"] is True
assert preview["data"]["stats"]["total_records"] == 2

result = service.execute_import(str(test_file))

print("\nExecute:")
print(result)

assert result["success"] is True
assert result["data"]["created_count"] >= 1

# Cleanup imported records
for profile in result["data"]["created"]:
    service.alumni.delete_profile(profile["alumni_id"])

test_file.unlink()

print("\nSUCCESS")
