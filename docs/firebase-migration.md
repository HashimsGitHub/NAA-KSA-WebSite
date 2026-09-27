# NUST Alumni Firebase migration (in progress)

Project ID: `nust-alumni-association`

This branch is an implementation workspace. Do **not** deploy Hosting yet: the `/api/**` rewrite points to `nust-alumni-api`, which must first be built and deployed to Cloud Run. The current `api/function_app.py` still depends on Azure Functions, Azure Tables and Blob Storage. The Azure deployment workflow still targets `main`.

## Target architecture

- Firebase Hosting serves `frontend/`.
- The existing frontend sends requests to `/api/**`; Firebase Hosting forwards these to a Python API on Cloud Run in `me-central1` (Doha).
- Firestore stores migrated Azure Table entities. Only the server-side service account accesses Firestore; client SDK access is denied by `firestore.rules`.
- Cloud Storage stores migrated blobs. Public versus private access needs to be decided per container before copying assets.
- Existing bcrypt hashes and server-side sessions need deliberate migration. Never publish account documents or hashes to the frontend.

## Account setup

1. In [Firebase Console](https://console.firebase.google.com/project/nust-alumni-association/overview), confirm the project is present.
2. Upgrade to Blaze and link a billing account for Cloud Run and Cloud Storage; create a budget alert.
3. Create a Firestore Standard database in production mode. `me-central1` (Doha) is the target region in this branch; confirm the data location before creation because it cannot later be changed.
4. Enable Firebase Hosting and Cloud Storage. Keep Firebase Hosting disconnected from automatic deploys to `main`.
5. Export Azure Tables and Blob containers into a secure local location; count records and files, then retain a backup. Do not commit the export or Azure credentials.
6. After the API port, migrate a copy of data to Firestore and Storage, compare counts, and test login, search, events, admin CRUD and image uploads on a preview deployment.
7. Only after acceptance, schedule a write freeze, perform a final incremental export/import, verify, then switch the NUST domain. Keep Azure available for rollback.

## Branches

- `main`: current NUST Azure SWA.
- `archive/nust-azure-swa-2026-09-28`: source snapshot (does not include live Azure data).
- `feature/nust-firebase-migration`: work in progress.
- `develop-vcnity` and `feature/vcnity-pwa`: VCNITY development. Move to a separate repository after stakeholder approval. Do not merge them into NUST `main`.

The `firebase.json` rewrite cannot serve a functional API until the Cloud Run service exists. Keep all Firebase changes off `main` during the migration.
