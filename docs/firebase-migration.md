# NUST Alumni: Azure hosting with Firebase Firestore (in progress)

Firebase project: `nust-alumni-association`.

The user's requirement is **no Firebase billing account**. This branch configures Firestore rules only. Do not deploy the earlier Firebase Hosting/Cloud Run design or enable Blaze.

## What exists today

The repository's `main` workflow deploys `frontend/` and the Python Azure Functions `api/` to an Azure Static Web App. Its API uses Azure Tables and Azure Blob Storage. Some static assets may live in Azure Blob Storage, but the repository workflow does not deploy the HTML frontend to a Blob static website.

## Target

- Keep NUST frontend on its existing Azure Static Web App for now, with existing Azure Blob content.
- Keep the `/api/**` routes on Azure Functions, so the frontend needs no endpoint/CORS change.
- Migrate Azure Table entities to the single free Firestore database in `nust-alumni-association`. Replace server-side table access in the Azure Functions API with the Firestore Python server SDK, preserving the existing response shape and login/session behavior.
- Keep Azure Blob Storage for images and other files. Do not enable Firebase Storage.
- Firestore rules deny direct browser access. The Azure Functions backend needs a tightly scoped Google service account credential, stored in Azure application settings or Key Vault, never in GitHub or frontend code. The server SDK uses IAM and bypasses Firestore rules.
- Monitor the Firestore Spark quota. On a project without billing, operations can fail when free limits are exceeded.

## Setup

1. In Firebase Console, confirm the project ID, then create **one Firestore Standard database** in production mode. `me-central1` (Doha) is a possible location for a KSA audience; confirm your data-location needs before creating the database because its location is fixed afterward. No Blaze upgrade or payment method is required for Firestore's free quota.
2. Retain an independent backup/export of every Azure Table before migration. Compare per-table counts and sample records, including user password hashes and session handling. Never commit exports to Git.
3. Develop the Firestore-backed Azure API in this branch and verify it locally against non-production test data. Configure the service account in Azure as a secret at deployment time.
4. Test login, role checks, directory filtering, events, knowledge, admin CRUD and media uploads with a staging endpoint. Plan a write freeze and final sync for cutover, with an Azure Tables rollback path.
5. Keep `main` running NUST throughout. Move VCNITY branches into a separate repository after stakeholder approval; do not merge VCNITY into NUST `main`.

**Status:** The API is still Azure Tables-backed. This configuration alone does not migrate data or switch the live site.
