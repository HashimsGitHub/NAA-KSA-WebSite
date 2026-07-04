from shared.storage_client import StorageClient

storage = StorageClient()

print(storage.table("AlumniProfiles"))
print(storage.table("UserAccounts"))

print(storage.container("profile-images"))
print(storage.container("blog-images"))

print()

print("SUCCESS")
