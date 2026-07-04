import os
import sys
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient


REQUIRED_TABLES = [
    "AlumniProfiles",
    "UserAccounts",
    "RegistrationRequests",
    "Sessions",
    "LoginTokens",
    "Events",
    "EventRegistrations",
    "BlogPosts",
    "MediaAssets",
    "AuditLogs",
    "ImportJobs",
    "SystemSettings",
]

REQUIRED_CONTAINERS = [
    "profile-images",
    "blog-images",
    "event-images",
    "blog-content",
    "event-assets",
    "documents",
    "imports",
]


def get_connection_string() -> str:
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    if not connection_string:
        print("ERROR: AZURE_STORAGE_CONNECTION_STRING environment variable is not set.")
        print()
        print("PowerShell:")
        print('$env:AZURE_STORAGE_CONNECTION_STRING="your_connection_string_here"')
        print()
        print("Command Prompt:")
        print('set AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here')
        sys.exit(1)

    return connection_string


def validate_tables(connection_string: str) -> bool:
    print("\nChecking Azure Tables...")

    service = TableServiceClient.from_connection_string(connection_string)
    existing_tables = {table.name for table in service.list_tables()}

    success = True

    for table_name in REQUIRED_TABLES:
        if table_name in existing_tables:
            print(f"  OK      {table_name}")
        else:
            print(f"  MISSING {table_name}")
            success = False

    return success


def validate_containers(connection_string: str) -> bool:
    print("\nChecking Blob Containers...")

    service = BlobServiceClient.from_connection_string(connection_string)
    existing_containers = {container.name for container in service.list_containers()}

    success = True

    for container_name in REQUIRED_CONTAINERS:
        if container_name in existing_containers:
            print(f"  OK      {container_name}")
        else:
            print(f"  MISSING {container_name}")
            success = False

    return success


def main():
    print("NUST KSA Alumni Portal - Azure Storage Validation")

    connection_string = get_connection_string()

    tables_ok = validate_tables(connection_string)
    containers_ok = validate_containers(connection_string)

    print("\nValidation Summary")

    if tables_ok and containers_ok:
        print("SUCCESS: All required Azure Tables and Blob Containers exist.")
        sys.exit(0)

    print("FAILED: Some required Azure Tables or Blob Containers are missing.")
    sys.exit(1)


if __name__ == "__main__":
    main()